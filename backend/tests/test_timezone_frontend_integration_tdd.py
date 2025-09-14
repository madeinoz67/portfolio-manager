"""
TDD test for frontend timezone integration following FastAPI best practices.

Based on: https://medium.com/@rameshkannanyt0078/how-to-handle-timezones-properly-in-fastapi-and-database-68b1c019c1bc

Best practices implemented:
1. Store all datetimes in UTC in database
2. Send UTC timestamps with timezone info to frontend
3. Frontend converts to user's local timezone for display
4. Use timezone-aware datetimes throughout the backend
"""

import pytest
import json
import subprocess
from datetime import datetime, timezone, timedelta
from src.utils.datetime_utils import utc_now, to_iso_string


class TestFrontendTimezoneIntegrationTDD:
    """TDD tests for proper timezone handling between backend and frontend."""

    def test_backend_stores_utc_datetimes(self):
        """Test that backend stores all datetimes in UTC (database best practice)."""
        # Backend should always work in UTC internally
        current_time = utc_now()

        # Should be timezone-aware UTC
        assert current_time.tzinfo == timezone.utc

        # All database operations should use UTC
        assert current_time.tzinfo is not None

    def test_api_sends_utc_with_timezone_info(self):
        """Test that API sends UTC timestamps that frontend can convert."""
        # Following the article's recommendation
        utc_time = utc_now()
        api_response_time = to_iso_string(utc_time)

        # Should include timezone information for frontend conversion
        assert "+00:00" in api_response_time or api_response_time.endswith("Z")

        # Should NOT have the invalid double timezone format we fixed
        assert not ("+00:00" in api_response_time and api_response_time.endswith("Z"))

    def test_frontend_timezone_conversion_contract(self):
        """Test the contract between backend and frontend for timezone handling."""
        # This test defines how frontend should handle UTC timestamps

        # Backend sends UTC timestamp
        utc_timestamp = "2025-09-14T20:28:54.754899+00:00"

        # Frontend should:
        # 1. Parse the UTC timestamp
        # 2. Convert to user's local timezone
        # 3. Display in human-readable format

        # Expected behavior (this is what JavaScript should do):
        expected_behaviors = {
            "parsing": "new Date(utc_timestamp) creates valid Date object",
            "conversion": "JavaScript automatically converts to local timezone",
            "display": "Use toLocaleString() for user-friendly display"
        }

        # Verify our UTC timestamp format is valid for JavaScript Date constructor
        # JavaScript Date.parse() returns NaN for invalid dates
        import subprocess
        import json

        js_test = f'''
        const date = new Date("{utc_timestamp}");
        const result = {{
            valid: !isNaN(date.getTime()),
            utc_string: "{utc_timestamp}",
            local_display: date.toLocaleString(),
            iso_string: date.toISOString()
        }};
        console.log(JSON.stringify(result));
        '''

        result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        js_result = json.loads(result.stdout.strip())

        # Verify JavaScript can parse and convert our UTC timestamp
        assert js_result["valid"] is True
        assert js_result["utc_string"] == utc_timestamp
        assert "AM" in js_result["local_display"] or "PM" in js_result["local_display"]

    def test_scheduler_api_timezone_compliance(self):
        """Test that scheduler API follows timezone best practices."""
        # Based on the actual API response format
        utc_time = utc_now()

        # Mock scheduler API response following best practices
        scheduler_response = {
            "scheduler": {
                "last_run_at": to_iso_string(utc_time - timedelta(minutes=15)),
                "next_run_at": to_iso_string(utc_time + timedelta(minutes=15)),
                "status": "running",
                "uptime_seconds": 3600
            }
        }

        # Verify both timestamps are UTC with proper timezone info
        last_run = scheduler_response["scheduler"]["last_run_at"]
        next_run = scheduler_response["scheduler"]["next_run_at"]

        # Both should be valid ISO strings with timezone info
        for timestamp in [last_run, next_run]:
            assert "T" in timestamp  # ISO format
            assert any(tz in timestamp for tz in ["+00:00", "Z"])  # Timezone info

            # Should be parseable by JavaScript
            import subprocess
            js_check = f'console.log(!isNaN(new Date("{timestamp}").getTime()))'
            result = subprocess.run(['node', '-e', js_check], capture_output=True, text=True)
            assert result.stdout.strip() == "true"

    def test_timezone_display_formatting_contract(self):
        """Test the expected display formats for different timezone scenarios."""
        # Test various timestamp formats that might come from API

        test_cases = [
            "2025-09-14T20:28:54.754899+00:00",  # UTC with explicit offset
            "2025-09-14T20:28:54.000Z",          # UTC with Z suffix
            "2025-09-14T20:28:54+00:00",         # UTC without microseconds
        ]

        for utc_timestamp in test_cases:
            # Each should be valid for JavaScript Date parsing
            import subprocess
            js_test = f'''
            const date = new Date("{utc_timestamp}");
            const result = {{
                valid: !isNaN(date.getTime()),
                local_string: date.toLocaleString("en-US", {{
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                    hour12: true
                }})
            }};
            console.log(JSON.stringify(result));
            '''

            result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
            js_result = json.loads(result.stdout.strip())

            assert js_result["valid"] is True, f"Invalid timestamp format: {utc_timestamp}"
            assert len(js_result["local_string"]) > 10, "Local display should be formatted"