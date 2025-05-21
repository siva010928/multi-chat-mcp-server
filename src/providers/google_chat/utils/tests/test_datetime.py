import unittest
import datetime
from src.providers.google_chat.utils.datetime import create_date_filter, parse_date, rfc3339_format


class TestDatetimeUtils(unittest.TestCase):
    def test_create_date_filter_with_quotes(self):
        """Test that create_date_filter adds quotes around timestamp values."""
        # Test with only start_date
        start_date = "2024-05-01"
        result = create_date_filter(start_date)
        self.assertIn('"', result)
        self.assertTrue(result.startswith('createTime > "'))
        
        # Test with both start_date and end_date
        end_date = "2024-05-31"
        result = create_date_filter(start_date, end_date)
        self.assertIn('"', result)
        self.assertTrue('createTime > "' in result)
        self.assertTrue('" AND createTime < "' in result)
        
    def test_parse_date(self):
        """Test that parse_date correctly handles string dates."""
        # Test start of day
        dt = parse_date("2024-05-01", "start")
        self.assertEqual(dt.hour, 0)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        
        # Test end of day
        dt = parse_date("2024-05-01", "end")
        self.assertEqual(dt.hour, 23)
        self.assertEqual(dt.minute, 59)
        self.assertEqual(dt.second, 59)
        
    def test_rfc3339_format(self):
        """Test that rfc3339_format correctly formats dates."""
        dt = datetime.datetime(2024, 5, 1, 12, 30, 45, tzinfo=datetime.timezone.utc)
        result = rfc3339_format(dt)
        self.assertEqual(result, "2024-05-01T12:30:45Z")


if __name__ == "__main__":
    unittest.main() 