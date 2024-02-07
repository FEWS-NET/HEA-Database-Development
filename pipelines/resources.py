import io
import json
import os
import pickle
import posixpath
import tempfile
from abc import abstractmethod
from functools import cached_property
from typing import Any, Optional, Type

import dagster._check as check
import gspread
import pandas as pd
from dagster import (
    ConfigurableIOManagerFactory,
    ConfigurableResource,
    DagsterInvariantViolationError,
    InitResourceContext,
    InputContext,
    OutputContext,
)
from dagster._core.storage.upath_io_manager import UPathIOManager
from dagster._utils import PICKLE_PROTOCOL
from google.oauth2 import service_account
from googleapiclient import discovery, http
from googleapiclient.errors import HttpError
from pydantic.fields import Field
from upath import UPath


class _DeleteOnCloseFile(io.FileIO):
    def close(self):
        super().close()
        try:
            os.remove(self.name)
        except OSError:
            # Catch a potential threading race condition and also allow this
            # method to be called multiple times.
            pass

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return True


class GoogleClientResource(ConfigurableResource):
    credentials_json: str

    def get_gspread_client(self) -> gspread.Client:
        client = gspread.service_account_from_dict(json.loads(self.credentials_json))
        return client

    @cached_property
    def client(self):
        # Convert the credentials_json string to a scoped credentials object
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        oauth_credentials = service_account.Credentials.from_service_account_info(
            json.loads(self.credentials_json)
        ).with_scopes(scopes)

        client = discovery.build("drive", "v3", credentials=oauth_credentials)
        return client

    def get_id_from_path(self, path: str, create_folders: bool = False):
        """
        Convert a path potentially containing subfolders to a Google Drive folder or file id.

        By default find an existing folder id, but optionally (if create_folders=True) create the subfolders.
        """
        components = path.strip(posixpath.sep).split(posixpath.sep)
        # The first component must be an actual Google Folder id
        file_or_folder_id = components.pop(0)
        while components:
            name = components.pop(0)
            # Find an object in this parent directory with the correct name
            query = f"name = '{name}' and parents='{file_or_folder_id}'"
            # If there are still components left, then this component must be a directory
            if components:
                query += "and mimeType='application/vnd.google-apps.folder'"
            try:
                response = (
                    self.client.files().list(q=query, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
                )
                if response and response.get("files"):
                    assert (
                        len(response.get("files")) == 1
                    ), f"There are multiple files called {name} in folder {file_or_folder_id}"  # NOQA: E501
                    file_or_folder_id = response.get("files")[0].get("id")
                else:
                    if create_folders:
                        metadata = {
                            "name": name,
                            "parents": [file_or_folder_id],
                            "mimeType": "application/vnd.google-apps.folder",
                        }
                        folder = (
                            self.client.files()
                            .create(
                                body=metadata,
                                fields="id",
                                supportsAllDrives=True,
                            )
                            .execute()
                        )
                        file_or_folder_id = folder.get("id")
                    else:
                        return None
            except HttpError as http_error:
                if http_error.status_code == 404 and create_folders:
                    metadata = {
                        "name": name,
                        "parents": [file_or_folder_id],
                        "mimeType": "application/vnd.google-apps.folder",
                    }
                    folder = (
                        self.client.files()
                        .create(
                            body=metadata,
                            fields="id",
                            supportsAllDrives=True,
                        )
                        .execute()
                    )
                    file_or_folder_id = folder.get("id")
                else:
                    raise
        return file_or_folder_id

    def download(
        self,
        path,
        chunksize: Optional[int] = None,
        chunk_callback=lambda _: False,
        mimetype: Optional[str] = None,
    ):
        """
        Downloads a file from Google Drive given the file_id to a temporary local file
        and returns the local file for processing
        """
        chunksize = chunksize or self.chunksize
        file_id = self.get_id_from_path(path)
        if not file_id:
            raise Exception("File %s not found" % path)
        # As per https://developers.google.com/drive/api/v3/manage-downloads#download_a_document
        # export_media method should be used if the file is Google Workspace Document
        file_obj = self.client.files().get(fileId=file_id, supportsAllDrives=True).execute()
        # Assuming we only need to deal with spreadsheet types from google workspace docs
        if file_obj.get("mimeType") == "application/vnd.google-apps.spreadsheet":
            mimetype = mimetype or "application/x-vnd.oasis.opendocument.spreadsheet"
            request = self.client.files().export_media(
                fileId=file_id,
                mimeType=mimetype,
            )
        else:
            request = self.client.files().get_media(fileId=file_id)

        done = False
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            downloader = http.MediaIoBaseDownload(fp, request, chunksize=chunksize)
            return_fp = _DeleteOnCloseFile(fp.name, "r")
            while done is False:
                _, done = downloader.next_chunk()
                if chunk_callback(fp):
                    done = True
        return return_fp


class PickleFilesystemIOManager(UPathIOManager):
    """
    Dagster I/O Manager that serializes Python objects to files using Pickle.

    Based on dagster._core.storage.fs_io_manager.PickledObjectFilesystemIOManager but with more standard path handling.
    """

    extension = ".pickle"

    def dump_to_path(self, context: OutputContext, obj: Any, path: "UPath"):
        try:
            with path.open("wb") as file:
                pickle.dump(obj, file, PICKLE_PROTOCOL)
        except (AttributeError, RecursionError, ImportError, pickle.PicklingError) as e:
            executor = context.step_context.job_def.executor_def

            if isinstance(e, RecursionError):
                # if obj can't be pickled because of RecursionError then __str__() will also
                # throw a RecursionError
                obj_repr = f"{obj.__class__} exceeds recursion limit and"
            else:
                obj_repr = obj.__str__()

            raise DagsterInvariantViolationError(
                f"Object {obj_repr} is not picklable. You are currently using the "
                f"fs_io_manager and the {executor.name}. You will need to use a different "
                "io manager to continue using this output. For example, you can use the "
                "mem_io_manager with the in_process_executor.\n"
                "For more information on io managers, visit "
                "https://docs.dagster.io/concepts/io-management/io-managers \n"
                "For more information on executors, vist "
                "https://docs.dagster.io/deployment/executors#overview"
            ) from e

    def load_from_path(self, context: InputContext, path: "UPath") -> Any:
        with path.open("rb") as file:
            return pickle.load(file)


class JSONFilesystemIOManager(UPathIOManager):
    """
    Dagster I/O Manager that serializes Python objects to JSON files.
    """

    extension = ".json"

    def dump_to_path(self, context: OutputContext, obj: Any, path: "UPath"):
        if self.path_exists(path):
            context.log.warning(f"Removing existing file: {path}")
            self.unlink(path)

        with path.open("w") as file:
            file.write(json.dumps(obj, indent=4))

    def load_from_path(self, context: InputContext, path: "UPath") -> Any:
        with path.open("r") as file:
            return json.loads(file.read())


class DataFrameCSVFilesystemIOManager(UPathIOManager):
    """
    Dagster I/O Manager that serializes DataFrames to CSV files.
    """

    extension = ".csv"

    def dump_to_path(self, context: OutputContext, obj: pd.DataFrame, path: UPath) -> None:
        if self.path_exists(path):
            context.log.warning(f"Removing existing file: {path}")
            self.unlink(path)

        obj.to_csv(path, index=False)

    def load_from_path(self, context: InputContext, path: UPath) -> pd.DataFrame:
        return pd.read_csv(path)


class ConfigurableUPathIOManagerFactory(
    ConfigurableIOManagerFactory[PickleFilesystemIOManager | JSONFilesystemIOManager | DataFrameCSVFilesystemIOManager]
):
    base_path: Optional[str] = Field(default=None, description="Base path for storing files.")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return False

    @abstractmethod
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        raise NotImplementedError

    def create_io_manager(self, context: InitResourceContext) -> UPathIOManager:
        base_path = self.base_path or check.not_none(context.instance).storage_directory()
        return self.get_iomanager_class()(base_path=UPath(base_path))


class PickleIOManager(ConfigurableUPathIOManagerFactory):
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return PickleFilesystemIOManager


class JSONIOManager(ConfigurableUPathIOManagerFactory):
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return JSONFilesystemIOManager


class DataFrameCSVIOManager(ConfigurableUPathIOManagerFactory):
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return DataFrameCSVFilesystemIOManager
