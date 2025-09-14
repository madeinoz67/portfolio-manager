"""
Simple TDD test to identify and fix datetime formatting issues in admin.py
"""

import pytest
import json
import subprocess
from datetime import datetime, timezone
from src.utils.datetime_utils import utc_now, to_iso_string


class TestAdminDatetimeFormattingSimple:
    """Simple TDD test for datetime formatting issues."""

    def test_current_problematic_datetime_formatting(self):
        """Test that the current problematic formatting fails JavaScript parsing."""
        # This simulates the current admin.py line 192: .isoformat() + "Z"
        now = utc_now()
        problematic_format = now.isoformat() + "Z"

        # This should fail JavaScript parsing if timezone info already exists
        js_test = f'''
        const date = new Date("{problematic_format}");
        console.log(!isNaN(date.getTime()));
        '''

        result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        is_valid = result.stdout.strip() == "true"

        # If the current format is invalid, this test should fail (showing the problem)
        if "+00:00Z" in problematic_format:
            assert not is_valid, f"Invalid format should fail: {problematic_format}"
        else:
            assert is_valid, f"Valid format should pass: {problematic_format}"

    def test_corrected_datetime_formatting(self):
        """Test that using to_iso_string() produces valid JavaScript-parseable dates."""
        now = utc_now()
        corrected_format = to_iso_string(now)

        # This should always pass with our helper function
        js_test = f'''
        const date = new Date("{corrected_format}");
        console.log(!isNaN(date.getTime()));
        '''

        result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        is_valid = result.stdout.strip() == "true"

        assert is_valid, f"Corrected format should be valid: {corrected_format}"

    def test_specific_admin_datetime_format_patterns(self):
        """Test the specific patterns found in admin.py that need fixing."""
        test_cases = [
            # Line 103: createdAt=user.created_at.isoformat(),
            ("isoformat_no_suffix", lambda dt: dt.isoformat()),
            # Line 182: lastUpdated=portfolio.updated_at.isoformat()
            ("isoformat_no_suffix_2", lambda dt: dt.isoformat()),
            # Line 192: createdAt=to_iso_string(user.created_at), - FIXED
            ("isoformat_plus_z_fixed", lambda dt: to_iso_string(dt)),
            # Line 230: lastUpdated=datetime.now().isoformat()
            ("datetime_now_isoformat", lambda dt: dt.isoformat()),
            # Line 345: "lastUpdate": provider.updated_at.isoformat(),
            ("provider_updated_at", lambda dt: dt.isoformat()),
            # Line 882: lastUpdated=provider.updated_at.isoformat(),
            ("provider_updated_at_2", lambda dt: dt.isoformat()),
            # Line 950: timestamp=activity.timestamp.isoformat()
            ("activity_timestamp", lambda dt: dt.isoformat()),
            # Line 1106: timestamp=activity.timestamp.isoformat(),
            ("activity_timestamp_2", lambda dt: dt.isoformat()),
        ]

        for pattern_name, formatter in test_cases:
            now = utc_now()
            formatted_date = formatter(now)

            # Test JavaScript parsing
            js_test = f'''
            const date = new Date("{formatted_date}");
            console.log(!isNaN(date.getTime()));
            '''

            result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
            is_valid = result.stdout.strip() == "true"

            # Show which patterns are problematic
            if not is_valid:
                print(f"❌ PROBLEMATIC: {pattern_name}: {formatted_date}")
            else:
                print(f"✅ OK: {pattern_name}: {formatted_date}")

            # All should be valid after we fix them
            assert is_valid, f"{pattern_name} should produce valid datetime: {formatted_date}"