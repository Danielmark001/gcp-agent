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

"""Unit tests for typing models."""

import pytest
from pydantic import ValidationError

from app.utils.typing import Feedback


class TestFeedbackModel:
    """Tests for the Feedback Pydantic model."""

    def test_valid_feedback_with_all_fields(self) -> None:
        """Test creating feedback with all fields."""
        feedback = Feedback(
            score=5,
            text="Great response!",
            invocation_id="inv-123",
            log_type="feedback",
            service_name="my-agent",
            user_id="user-456",
        )

        assert feedback.score == 5
        assert feedback.text == "Great response!"
        assert feedback.invocation_id == "inv-123"
        assert feedback.log_type == "feedback"
        assert feedback.service_name == "my-agent"
        assert feedback.user_id == "user-456"

    def test_valid_feedback_with_minimal_fields(self) -> None:
        """Test creating feedback with only required fields."""
        feedback = Feedback(score=4, invocation_id="inv-789")

        assert feedback.score == 4
        assert feedback.invocation_id == "inv-789"
        assert feedback.text == ""  # Default value
        assert feedback.log_type == "feedback"  # Default value
        assert feedback.service_name == "my-agent"  # Default value
        assert feedback.user_id == ""  # Default value

    def test_integer_score(self) -> None:
        """Test feedback with integer score."""
        feedback = Feedback(score=3, invocation_id="inv-001")
        assert feedback.score == 3
        assert isinstance(feedback.score, int)

    def test_float_score(self) -> None:
        """Test feedback with float score."""
        feedback = Feedback(score=4.5, invocation_id="inv-002")
        assert feedback.score == 4.5
        assert isinstance(feedback.score, float)

    def test_invalid_score_type(self) -> None:
        """Test that invalid score type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Feedback(score="invalid", invocation_id="inv-003")  # type: ignore

        errors = exc_info.value.errors()
        assert any(error["type"] == "float_type" for error in errors)

    def test_missing_required_score(self) -> None:
        """Test that missing score raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Feedback(invocation_id="inv-004")  # type: ignore

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("score",) for error in errors)

    def test_missing_required_invocation_id(self) -> None:
        """Test that missing invocation_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Feedback(score=5)  # type: ignore

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("invocation_id",) for error in errors)

    def test_empty_text_field(self) -> None:
        """Test that empty text field is allowed."""
        feedback = Feedback(score=5, text="", invocation_id="inv-005")
        assert feedback.text == ""

    def test_none_text_field(self) -> None:
        """Test that None text field is converted to empty string."""
        feedback = Feedback(score=5, text=None, invocation_id="inv-006")
        assert feedback.text == ""

    def test_custom_log_type(self) -> None:
        """Test that log_type is fixed to 'feedback'."""
        feedback = Feedback(
            score=5, invocation_id="inv-007", log_type="feedback"
        )
        assert feedback.log_type == "feedback"

    def test_custom_service_name(self) -> None:
        """Test that service_name is fixed to 'my-agent'."""
        feedback = Feedback(
            score=5, invocation_id="inv-008", service_name="my-agent"
        )
        assert feedback.service_name == "my-agent"

    def test_model_dump(self) -> None:
        """Test converting feedback to dictionary."""
        feedback = Feedback(
            score=5,
            text="Excellent!",
            invocation_id="inv-009",
            user_id="user-123",
        )

        data = feedback.model_dump()

        assert data["score"] == 5
        assert data["text"] == "Excellent!"
        assert data["invocation_id"] == "inv-009"
        assert data["log_type"] == "feedback"
        assert data["service_name"] == "my-agent"
        assert data["user_id"] == "user-123"

    def test_model_validate(self) -> None:
        """Test validating feedback from dictionary."""
        data = {
            "score": 4,
            "text": "Good",
            "invocation_id": "inv-010",
            "user_id": "user-789",
        }

        feedback = Feedback.model_validate(data)

        assert feedback.score == 4
        assert feedback.text == "Good"
        assert feedback.invocation_id == "inv-010"
        assert feedback.user_id == "user-789"

    def test_negative_score(self) -> None:
        """Test that negative scores are allowed."""
        feedback = Feedback(score=-1, invocation_id="inv-011")
        assert feedback.score == -1

    def test_large_score(self) -> None:
        """Test that large scores are allowed."""
        feedback = Feedback(score=1000000, invocation_id="inv-012")
        assert feedback.score == 1000000

    def test_long_text(self) -> None:
        """Test feedback with very long text."""
        long_text = "A" * 10000
        feedback = Feedback(score=5, text=long_text, invocation_id="inv-013")
        assert feedback.text == long_text
        assert len(feedback.text) == 10000
