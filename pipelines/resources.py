import json
import os
import pickle
from abc import abstractmethod
from typing import Any, Optional, Type
from urllib.parse import urljoin

import dagster._check as check
import pandas as pd
from dagster import (
    ConfigurableIOManagerFactory,
    DagsterInvariantViolationError,
    InitResourceContext,
    InputContext,
    MetadataValue,
    OutputContext,
)
from dagster._core.storage.upath_io_manager import UPathIOManager
from dagster._utils import PICKLE_PROTOCOL
from django.urls import reverse
from pydantic.fields import Field
from upath import UPath


class DownloadAssetMixin:
    """
    Mixin that adds download URL of the asset to the metadata.
    """

    def get_download_url(self, context: OutputContext) -> str:
        if not context or not getattr(context, "has_asset_key", False) or not context.has_asset_key:
            return ""

        asset_name = context.asset_key.path[-1]
        root_url = os.getenv("BASELINE_EXPLORER_API_ROOT_URL", "http://localhost:8000")

        kwargs = {"asset_name": asset_name}
        if context.has_partition_key:
            kwargs["partition_name"] = context.partition_key
            relative_url = reverse("asset_download_partitioned", kwargs=kwargs)
        else:
            relative_url = reverse("asset_download", kwargs=kwargs)

        return urljoin(root_url, relative_url)

    def handle_output(self, context: OutputContext, obj):
        download_url = self.get_download_url(context)
        if download_url:
            context.add_output_metadata(
                {
                    "download": MetadataValue.url(download_url),
                }
            )
        super().handle_output(context, obj)


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


class JSONFilesystemIOManager(DownloadAssetMixin, UPathIOManager):
    """
    Dagster I/O Manager that serializes Python objects to JSON files.
    """

    extension = ".json"

    def dump_to_path(self, context: OutputContext, obj: Any, path: "UPath"):
        if self.path_exists(path):
            context.log.warning(f"Removing existing file: {path}")
            self.unlink(path)

        with path.open("w") as file:
            file.write(json.dumps(obj, indent=4, ensure_ascii=False))

    def load_from_path(self, context: InputContext, path: "UPath") -> Any:
        with path.open("r") as file:
            return json.loads(file.read())


class DataFrameCSVFilesystemIOManager(DownloadAssetMixin, UPathIOManager):
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


class DataFrameExcelFilesystemIOManager(DownloadAssetMixin, UPathIOManager):
    """
    Dagster I/O Manager that serializes DataFrames to Excel .xlsx using the OpenPyXL engine.

    It accepts a single DataFrame or a list of DataFrames or a dict of sheet names to DataFrames,
    and writes them to a single Excel file. If the file already exists, it will be appended to,
    replacing any existing sheets with the same name but leaving other sheets untouched.
    """

    extension = ".xlsx"

    def __init__(
        self,
        base_path: UPath,
        to_excel_kwargs: Optional[dict] = None,
        if_sheet_exists: Optional[bool] = None,
        engine_kwargs: Optional[dict] = None,
    ):
        super().__init__(base_path)
        self.to_excel_kwargs = to_excel_kwargs or {"index": False}
        self.if_sheet_exists = if_sheet_exists
        self.engine_kwargs = engine_kwargs or {}

    def dump_to_path(
        self, context: OutputContext, obj: dict[str, pd.DataFrame] | list[pd.DataFrame] | pd.DataFrame, path: UPath
    ) -> None:
        if isinstance(obj, pd.DataFrame):
            obj = {"Sheet1": obj}
        elif isinstance(obj, list):
            obj = {f"Sheet{i+1}": df for i, df in enumerate(obj)}

        # Set the ExcelWriter parameters
        mode = "w"
        if self.path_exists(path):
            mode = "a"
            if self.if_sheet_exists is None:
                self.if_sheet_exists = "replace"
            if "keep_vba" not in self.engine_kwargs:
                self.engine_kwargs["keep_vba"] = True

        # Write the DataFrames to the Excel file
        with pd.ExcelWriter(
            path,
            engine="openpyxl",
            mode=mode,
            if_sheet_exists=self.if_sheet_exists,
            engine_kwargs=self.engine_kwargs,
        ) as writer:
            for sheet_name, df in obj.items():
                df.to_excel(writer, sheet_name=sheet_name, **self.to_excel_kwargs)

    def load_from_path(self, context: InputContext, path: UPath) -> dict[str, pd.DataFrame]:
        with pd.ExcelFile(path, engine="openpyxl") as xls:
            return xls.parse(sheet_name=None)  # Get all sheets as a dict


class ConfigurableUPathIOManagerFactory(
    ConfigurableIOManagerFactory[
        PickleFilesystemIOManager
        | JSONFilesystemIOManager
        | DataFrameCSVFilesystemIOManager
        | DataFrameExcelFilesystemIOManager
    ]
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


class ConfigurableDataFrameExcelFilesystemIOManagerFactory(ConfigurableUPathIOManagerFactory):
    to_excel_kwargs: Optional[dict] = Field(
        default=None, description="Additional arguments passed DataFrame.to_excel()"
    )
    engine_kwargs: Optional[dict] = Field(default=None, description="Additional arguments passed the OpenPyXL engine")

    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return DataFrameExcelFilesystemIOManager

    def create_io_manager(self, context: InitResourceContext) -> UPathIOManager:
        base_path = self.base_path or check.not_none(context.instance).storage_directory()
        return self.get_iomanager_class()(
            base_path=UPath(base_path), to_excel_kwargs=self.to_excel_kwargs, engine_kwargs=self.engine_kwargs
        )


class PickleIOManager(ConfigurableUPathIOManagerFactory):
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return PickleFilesystemIOManager


class JSONIOManager(ConfigurableUPathIOManagerFactory):
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return JSONFilesystemIOManager


class DataFrameCSVIOManager(ConfigurableUPathIOManagerFactory):
    def get_iomanager_class(self) -> Type[UPathIOManager]:
        return DataFrameCSVFilesystemIOManager


class DataFrameExcelIOManager(ConfigurableDataFrameExcelFilesystemIOManagerFactory):
    pass
