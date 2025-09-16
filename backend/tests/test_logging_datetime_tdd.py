"""
TDD test to identify and fix datetime formatting issues in core/logging.py

Following FastAPI timezone best practices from:
https://medium.com/@rameshkannanyt0078/how-to-handle-timezones-properly-in-fastapi-and-database-68b1c019c1bc
"""

import pytest
import json
import subprocess
from datetime import datetime, timezone
from src.core.logging import StructuredFormatter


class TestLoggingDatetimeTDD:
    def test_structured_formatter_datetime_format(self):
        """Test that StructuredFormatter produces valid datetime format for JavaScript."""
        formatter = StructuredFormatter()

        # Create a mock log record
        import logging
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )

        # Format the log entry
        formatted_log = formatter.format(record)
        log_entry = json.loads(formatted_log)

        # Check that timestamp field exists
        assert "timestamp" in log_entry
        timestamp = log_entry["timestamp"]

        # Test that the timestamp is valid for JavaScript Date constructor
        js_test_code = f"""
        const dateStr = "{timestamp}";
        const date = new Date(dateStr);
        console.log(JSON.stringify({{
            valid: !isNaN(date.getTime()),
            original: dateStr,
            parsed: date.toISOString(),
            local_display: date.toLocaleString()
        }}));
        """

        result = subprocess.run(['node', '-e', js_test_code], capture_output=True, text=True)
        assert result.returncode == 0, f"JavaScript test failed: {result.stderr}"

        js_result = json.loads(result.stdout.strip())

        # The JavaScript Date constructor should parse it successfully
        assert js_result["valid"] is True, f"JavaScript cannot parse timestamp: {timestamp}"

        # Should not have the problematic +00:00Z pattern that causes "Invalid Date"
        assert not ("+00:00" in timestamp and timestamp.endswith("Z")), \
            f"Timestamp has invalid +00:00Z pattern: {timestamp}"

    def test_structured_formatter_follows_fastapi_best_practices(self):
        """Test that timestamp format follows FastAPI timezone best practices."""
        formatter = StructuredFormatter()

        import logging
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )

        formatted_log = formatter.format(record)
        log_entry = json.loads(formatted_log)
        timestamp = log_entry["timestamp"]

        # Should be valid ISO format
        try:
            # Test Python datetime parsing first
            if timestamp.endswith('Z'):
                # Handle Z suffix
                parsed_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                parsed_dt = datetime.fromisoformat(timestamp)

            # Should have timezone info
            assert parsed_dt.tzinfo is not None, "Timestamp should include timezone information"

        except ValueError as e:
            pytest.fail(f"Timestamp is not valid ISO format: {timestamp}, error: {e}")