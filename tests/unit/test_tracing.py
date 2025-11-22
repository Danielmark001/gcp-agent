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

"""Unit tests for tracing utilities."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.utils.tracing import CloudTraceLoggingSpanExporter
from tests.utils.mocks import MockLogger, MockSpan


class TestCloudTraceLoggingSpanExporter:
    """Tests for CloudTraceLoggingSpanExporter."""

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_initialization(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test exporter initialization."""
        exporter = CloudTraceLoggingSpanExporter(project_id="test-project")

        assert exporter.project_id == "test-project"
        assert exporter.bucket_name == "test-project-my-agent-logs-data"
        assert not exporter.debug

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_initialization_with_custom_bucket(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test exporter initialization with custom bucket."""
        exporter = CloudTraceLoggingSpanExporter(
            project_id="test-project", bucket_name="custom-bucket"
        )

        assert exporter.bucket_name == "custom-bucket"

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_initialization_debug_mode(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test exporter initialization with debug mode."""
        exporter = CloudTraceLoggingSpanExporter(
            project_id="test-project", debug=True
        )

        assert exporter.debug is True

    @patch("app.utils.tracing.CloudTraceSpanExporter.export")
    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_export_span(
        self,
        mock_storage_client: MagicMock,
        mock_logging_client: MagicMock,
        mock_parent_export: MagicMock,
    ) -> None:
        """Test exporting a span."""
        from opentelemetry.sdk.trace.export import SpanExportResult

        mock_logger = MockLogger(MagicMock())
        mock_logging_client.return_value.logger.return_value = mock_logger

        exporter = CloudTraceLoggingSpanExporter(project_id="test-project")

        span = MockSpan(name="test_span", trace_id=123456789, span_id=987654321)
        mock_parent_export.return_value = SpanExportResult.SUCCESS

        result = exporter.export([span])

        # Should log to Cloud Logging
        assert len(mock_logger.entries) > 0
        # Should call parent export
        mock_parent_export.assert_called_once()
        assert result == SpanExportResult.SUCCESS

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_store_in_gcs(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test storing content in GCS."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.exists.return_value = True

        exporter = CloudTraceLoggingSpanExporter(
            project_id="test-project", bucket_name="test-bucket"
        )

        content = '{"test": "data"}'
        span_id = "span-123"

        result = exporter.store_in_gcs(content, span_id)

        assert result == "gs://test-bucket/spans/span-123.json"
        mock_blob.upload_from_string.assert_called_once_with(
            content, "application/json"
        )

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_store_in_gcs_bucket_not_exists(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test storing in GCS when bucket doesn't exist."""
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = False
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        exporter = CloudTraceLoggingSpanExporter(
            project_id="test-project", bucket_name="test-bucket"
        )

        result = exporter.store_in_gcs('{"test": "data"}', "span-123")

        assert result == "GCS bucket not found"

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_process_large_attributes(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test processing large attributes."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.exists.return_value = True
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        exporter = CloudTraceLoggingSpanExporter(
            project_id="test-project", bucket_name="test-bucket"
        )

        # Create large attributes (>250KB)
        large_data = "A" * (256 * 1024)
        span_dict = {"attributes": {"large_field": large_data}}

        result = exporter._process_large_attributes(span_dict, "span-123")

        # Should have uri_payload and url_payload
        assert "uri_payload" in result["attributes"]
        assert "url_payload" in result["attributes"]
        assert result["attributes"]["uri_payload"] == "gs://test-bucket/spans/span-123.json"

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_process_small_attributes(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test processing small attributes (no GCS storage needed)."""
        exporter = CloudTraceLoggingSpanExporter(project_id="test-project")

        span_dict = {"attributes": {"small_field": "small data"}}

        result = exporter._process_large_attributes(span_dict, "span-123")

        # Should not modify attributes for small data
        assert "uri_payload" not in result["attributes"]
        assert "url_payload" not in result["attributes"]
        assert result["attributes"]["small_field"] == "small data"

    @patch("app.utils.tracing.google_cloud_logging.Client")
    @patch("app.utils.tracing.storage.Client")
    def test_custom_clients(
        self, mock_storage_client: MagicMock, mock_logging_client: MagicMock
    ) -> None:
        """Test initialization with custom clients."""
        custom_logging_client = MagicMock()
        custom_storage_client = MagicMock()

        exporter = CloudTraceLoggingSpanExporter(
            project_id="test-project",
            logging_client=custom_logging_client,
            storage_client=custom_storage_client,
        )

        assert exporter.logging_client == custom_logging_client
        assert exporter.storage_client == custom_storage_client
