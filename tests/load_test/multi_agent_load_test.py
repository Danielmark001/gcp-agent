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

"""Load tests for multi-agent scenarios."""

import json
import logging
import os
import random
import time
from typing import Any

from locust import HttpUser, between, task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load agent configuration if available
try:
    with open("deployment_metadata.json") as f:
        remote_agent_engine_id = json.load(f)["remote_agent_engine_id"]

    parts = remote_agent_engine_id.split("/")
    project_id = parts[1]
    location = parts[3]
    engine_id = parts[5]

    base_url = f"https://{location}-aiplatform.googleapis.com"
    url_path = f"/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}:streamQuery"

    logger.info("Using remote agent engine ID: %s", remote_agent_engine_id)
    logger.info("Using base URL: %s", base_url)
    logger.info("Using URL path: %s", url_path)
except FileNotFoundError:
    logger.warning("deployment_metadata.json not found. Using placeholder values.")
    base_url = "http://localhost:8000"
    url_path = "/stream_query"


class MultiAgentUser(HttpUser):
    """Simulates multiple users with different query patterns."""

    wait_time = between(1, 3)
    host = base_url

    def on_start(self) -> None:
        """Initialize user with random ID."""
        self.user_id = f"load_test_user_{random.randint(1000, 9999)}"
        logger.info(f"Starting user: {self.user_id}")

    @task(3)
    def weather_query(self) -> None:
        """Simulate weather query (higher weight)."""
        cities = ["San Francisco", "New York", "Los Angeles", "Chicago", "Miami"]
        city = random.choice(cities)

        headers = {"Content-Type": "application/json"}
        if "_AUTH_TOKEN" in os.environ:
            headers["Authorization"] = f"Bearer {os.environ['_AUTH_TOKEN']}"

        data = {
            "input": {
                "message": f"What's the weather in {city}?",
                "user_id": self.user_id,
            }
        }

        self._execute_query(data, headers, "weather_query")

    @task(2)
    def time_query(self) -> None:
        """Simulate time query."""
        cities = ["San Francisco", "New York", "Los Angeles"]
        city = random.choice(cities)

        headers = {"Content-Type": "application/json"}
        if "_AUTH_TOKEN" in os.environ:
            headers["Authorization"] = f"Bearer {os.environ['_AUTH_TOKEN']}"

        data = {
            "input": {
                "message": f"What time is it in {city}?",
                "user_id": self.user_id,
            }
        }

        self._execute_query(data, headers, "time_query")

    @task(1)
    def complex_query(self) -> None:
        """Simulate complex multi-part query."""
        headers = {"Content-Type": "application/json"}
        if "_AUTH_TOKEN" in os.environ:
            headers["Authorization"] = f"Bearer {os.environ['_AUTH_TOKEN']}"

        data = {
            "input": {
                "message": "What's the weather and current time in San Francisco?",
                "user_id": self.user_id,
            }
        }

        self._execute_query(data, headers, "complex_query")

    def _execute_query(
        self, data: dict[str, Any], headers: dict[str, str], query_type: str
    ) -> None:
        """Execute a query and track metrics."""
        start_time = time.time()

        try:
            with self.client.post(
                url_path,
                headers=headers,
                json=data,
                catch_response=True,
                name=f"/{query_type}",
                stream=True,
                params={"alt": "sse"},
                timeout=30,
            ) as response:
                if response.status_code == 200:
                    events = []
                    for line in response.iter_lines():
                        if line:
                            try:
                                event = json.loads(line)
                                events.append(event)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode line: {line}")

                    end_time = time.time()
                    total_time = end_time - start_time

                    # Record completion metrics
                    self.environment.events.request.fire(
                        request_type="POST",
                        name=f"/{query_type}_complete",
                        response_time=total_time * 1000,
                        response_length=len(json.dumps(events)),
                        response=response,
                        context={},
                    )

                    logger.debug(
                        f"{query_type} completed in {total_time:.2f}s with {len(events)} events"
                    )
                else:
                    response.failure(
                        f"Unexpected status code: {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Error executing {query_type}: {e}")


class BurstTrafficUser(HttpUser):
    """Simulates burst traffic patterns."""

    wait_time = between(0.1, 1)
    host = base_url

    def on_start(self) -> None:
        """Initialize user."""
        self.user_id = f"burst_user_{random.randint(1000, 9999)}"

    @task
    def rapid_queries(self) -> None:
        """Send rapid successive queries."""
        headers = {"Content-Type": "application/json"}
        if "_AUTH_TOKEN" in os.environ:
            headers["Authorization"] = f"Bearer {os.environ['_AUTH_TOKEN']}"

        queries = [
            "What's the weather?",
            "What time is it?",
            "Weather in SF?",
        ]

        for query in queries:
            data = {
                "input": {
                    "message": query,
                    "user_id": self.user_id,
                }
            }

            try:
                with self.client.post(
                    url_path,
                    headers=headers,
                    json=data,
                    catch_response=True,
                    name="/rapid_query",
                    stream=True,
                    params={"alt": "sse"},
                    timeout=15,
                ) as response:
                    if response.status_code != 200:
                        response.failure(
                            f"Unexpected status code: {response.status_code}"
                        )
            except Exception as e:
                logger.error(f"Error in rapid query: {e}")

            # Very short wait between rapid queries
            time.sleep(0.1)


class LongRunningQueryUser(HttpUser):
    """Simulates users with long-running queries."""

    wait_time = between(5, 10)
    host = base_url

    def on_start(self) -> None:
        """Initialize user."""
        self.user_id = f"long_query_user_{random.randint(1000, 9999)}"

    @task
    def long_query(self) -> None:
        """Send query that might take longer to process."""
        headers = {"Content-Type": "application/json"}
        if "_AUTH_TOKEN" in os.environ:
            headers["Authorization"] = f"Bearer {os.environ['_AUTH_TOKEN']}"

        data = {
            "input": {
                "message": "Can you give me a detailed explanation about the weather "
                "patterns in San Francisco, including the current conditions, "
                "typical weather for this time of year, and what time it is there?",
                "user_id": self.user_id,
            }
        }

        try:
            with self.client.post(
                url_path,
                headers=headers,
                json=data,
                catch_response=True,
                name="/long_query",
                stream=True,
                params={"alt": "sse"},
                timeout=60,
            ) as response:
                if response.status_code == 200:
                    event_count = 0
                    for line in response.iter_lines():
                        if line:
                            event_count += 1
                    logger.info(f"Long query received {event_count} events")
                else:
                    response.failure(
                        f"Unexpected status code: {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Error in long query: {e}")
