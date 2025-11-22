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

"""Unit tests for agent tools."""

import pytest

from app.agent import get_current_time, get_weather


class TestGetWeatherTool:
    """Tests for the get_weather tool."""

    def test_san_francisco_weather(self) -> None:
        """Test weather for San Francisco returns foggy."""
        result = get_weather("San Francisco")
        assert "60 degrees" in result
        assert "foggy" in result

    def test_san_francisco_abbreviation(self) -> None:
        """Test weather for SF abbreviation."""
        result = get_weather("sf")
        assert "60 degrees" in result
        assert "foggy" in result

    def test_case_insensitive_sf(self) -> None:
        """Test case insensitive matching for SF."""
        result = get_weather("SF")
        assert "60 degrees" in result
        assert "foggy" in result

        result = get_weather("SAN FRANCISCO")
        assert "60 degrees" in result
        assert "foggy" in result

    def test_other_city_weather(self) -> None:
        """Test weather for other cities returns sunny."""
        result = get_weather("New York")
        assert "90 degrees" in result
        assert "sunny" in result

    def test_empty_query(self) -> None:
        """Test weather with empty query."""
        result = get_weather("")
        assert "90 degrees" in result
        assert "sunny" in result

    def test_numeric_query(self) -> None:
        """Test weather with numeric input."""
        result = get_weather("12345")
        assert "90 degrees" in result
        assert "sunny" in result

    def test_special_characters_query(self) -> None:
        """Test weather with special characters."""
        result = get_weather("!@#$%")
        assert "90 degrees" in result
        assert "sunny" in result


class TestGetCurrentTimeTool:
    """Tests for the get_current_time tool."""

    def test_san_francisco_time(self) -> None:
        """Test time for San Francisco."""
        result = get_current_time("San Francisco")
        assert "current time" in result.lower()
        assert "San Francisco" in result

    def test_san_francisco_abbreviation(self) -> None:
        """Test time for SF abbreviation."""
        result = get_current_time("sf")
        assert "current time" in result.lower()

    def test_case_insensitive_sf(self) -> None:
        """Test case insensitive matching for SF."""
        result = get_current_time("SF")
        assert "current time" in result.lower()

        result = get_current_time("SAN FRANCISCO")
        assert "current time" in result.lower()

    def test_unknown_city(self) -> None:
        """Test time for unknown city."""
        result = get_current_time("Unknown City")
        assert "Sorry" in result
        assert "don't have timezone information" in result

    def test_empty_query(self) -> None:
        """Test time with empty query."""
        result = get_current_time("")
        assert "Sorry" in result

    def test_time_format(self) -> None:
        """Test that time is returned in expected format."""
        result = get_current_time("San Francisco")
        # Should contain year-month-day hour:minute:second format
        assert any(char.isdigit() for char in result)
        assert ":" in result

    def test_timezone_info(self) -> None:
        """Test that timezone information is included."""
        result = get_current_time("San Francisco")
        # Should include timezone offset info
        assert any(x in result for x in ["-", "+"])
