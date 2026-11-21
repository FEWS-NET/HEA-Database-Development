import warnings

import fsspec
from django.test import SimpleTestCase
from gdrivefs.core import GoogleDriveFileSystem
from upath import UPath

import pipelines  # NOQA: F401


class GoogleDriveRegistrationTestCase(SimpleTestCase):
    """
    Regression tests for resolving gdrive:// paths to the gdrivefs fork.

    Newer fsspec releases map gdrive:// to the `gdrive_fsspec` module, which the fork does not provide, so the
    pipelines package registers the fork explicitly. Without it, UPath("gdrive://...") raises
    "ImportError: Please install gdrive_fs for access to Google Drive".
    """

    def test_fsspec_resolves_gdrive_to_gdrivefs(self):
        """
        The fsspec registry returns the gdrivefs fork for the gdrive protocol.
        """
        self.assertIs(fsspec.get_filesystem_class("gdrive"), GoogleDriveFileSystem)

    def test_upath_accepts_gdrive_path(self):
        """
        A gdrive:// UPath can be constructed with the storage options used by the metadata jobs.
        """
        # universal-pathlib has no dedicated gdrive class, so it warns that it is using its default implementation
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="UPath 'gdrive' filesystem not explicitly implemented")
            path = UPath(
                "gdrive://Database Design/BSS Metadata",
                token="service_account",
                access="read_only",
                root_file_id="0AOJ0gJ8sjnO7Uk9PVA",
                creds={},
            )
        self.assertEqual(path.protocol, "gdrive")
        self.assertEqual(path.path, "Database Design/BSS Metadata")
