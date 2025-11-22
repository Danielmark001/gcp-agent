# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for GCS utilities."""

from unittest.mock import MagicMock, patch

import pytest
from google.api_core import exceptions

from app.utils.gcs import create_bucket_if_not_exists


class TestCreateBucketIfNotExists:
    """Tests for create_bucket_if_not_exists function."""

    @patch("app.utils.gcs.storage.Client")
    def test_bucket_already_exists(self, mock_client: MagicMock) -> None:
        """Test when bucket already exists."""
        mock_storage = MagicMock()
        mock_client.return_value = mock_storage

        # Bucket exists, so get_bucket succeeds
        mock_bucket = MagicMock()
        mock_storage.get_bucket.return_value = mock_bucket

        create_bucket_if_not_exists(
            bucket_name="existing-bucket", project="test-project", location="us-central1"
        )

        # Should call get_bucket
        mock_storage.get_bucket.assert_called_once_with("existing-bucket")
        # Should not call create_bucket
        mock_storage.create_bucket.assert_not_called()

    @patch("app.utils.gcs.storage.Client")
    def test_bucket_creation(self, mock_client: MagicMock) -> None:
        """Test bucket creation when it doesn't exist."""
        mock_storage = MagicMock()
        mock_client.return_value = mock_storage

        # Bucket doesn't exist, so get_bucket raises NotFound
        mock_storage.get_bucket.side_effect = exceptions.NotFound("Bucket not found")

        # Mock create_bucket
        mock_bucket = MagicMock()
        mock_bucket.name = "new-bucket"
        mock_bucket.location = "us-central1"
        mock_storage.create_bucket.return_value = mock_bucket

        create_bucket_if_not_exists(
            bucket_name="new-bucket", project="test-project", location="us-central1"
        )

        # Should call get_bucket first
        mock_storage.get_bucket.assert_called_once_with("new-bucket")
        # Should call create_bucket
        mock_storage.create_bucket.assert_called_once_with(
            "new-bucket", location="us-central1", project="test-project"
        )

    @patch("app.utils.gcs.storage.Client")
    def test_bucket_name_with_gs_prefix(self, mock_client: MagicMock) -> None:
        """Test bucket name handling with gs:// prefix."""
        mock_storage = MagicMock()
        mock_client.return_value = mock_storage

        mock_bucket = MagicMock()
        mock_storage.get_bucket.return_value = mock_bucket

        create_bucket_if_not_exists(
            bucket_name="gs://test-bucket", project="test-project", location="us-central1"
        )

        # Should strip gs:// prefix
        mock_storage.get_bucket.assert_called_once_with("test-bucket")

    @patch("app.utils.gcs.storage.Client")
    def test_custom_location(self, mock_client: MagicMock) -> None:
        """Test bucket creation with custom location."""
        mock_storage = MagicMock()
        mock_client.return_value = mock_storage

        mock_storage.get_bucket.side_effect = exceptions.NotFound("Not found")
        mock_bucket = MagicMock()
        mock_storage.create_bucket.return_value = mock_bucket

        create_bucket_if_not_exists(
            bucket_name="test-bucket", project="test-project", location="us-west1"
        )

        mock_storage.create_bucket.assert_called_once_with(
            "test-bucket", location="us-west1", project="test-project"
        )

    @patch("app.utils.gcs.storage.Client")
    def test_different_project(self, mock_client: MagicMock) -> None:
        """Test bucket operations with different project."""
        mock_storage = MagicMock()
        mock_client.return_value = mock_storage

        mock_storage.get_bucket.side_effect = exceptions.NotFound("Not found")
        mock_bucket = MagicMock()
        mock_storage.create_bucket.return_value = mock_bucket

        create_bucket_if_not_exists(
            bucket_name="test-bucket", project="different-project", location="us-central1"
        )

        # Should use the specified project
        mock_client.assert_called_once_with(project="different-project")
        mock_storage.create_bucket.assert_called_once_with(
            "test-bucket", location="us-central1", project="different-project"
        )

    @patch("app.utils.gcs.storage.Client")
    def test_permission_error(self, mock_client: MagicMock) -> None:
        """Test handling of permission errors."""
        mock_storage = MagicMock()
        mock_client.return_value = mock_storage

        # Simulate permission error
        mock_storage.get_bucket.side_effect = exceptions.Forbidden("Permission denied")

        with pytest.raises(exceptions.Forbidden):
            create_bucket_if_not_exists(
                bucket_name="test-bucket", project="test-project", location="us-central1"
            )
