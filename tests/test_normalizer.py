import pytest
from logfsm.normalizer import normalize_line, extract_timestamp


class TestNormalizeLine:
    """Test the normalize_line function."""
    
    def test_normalize_timestamp(self):
        """Test normalization of timestamps."""
        line = "2023-10-26T12:34:56.789 INFO Some log message"
        normalized = normalize_line(line)
        assert normalized == "<ts> info some log message"
    
    def test_normalize_multiple_timestamps(self):
        """Test normalization of multiple timestamps."""
        line = "2023-10-26T12:34:56.789 Process started at 2024-01-01T00:00:00.000"
        normalized = normalize_line(line)
        assert normalized == "<ts> process started at <ts>"
    
    def test_normalize_long_ids(self):
        """Test normalization of long alphanumeric IDs."""
        line = "Order ABC123DEF456 processed with ID XYZ789ABC"
        normalized = normalize_line(line)
        assert normalized == "order <id> processed with id <id>"
    
    def test_normalize_numbers(self):
        """Test normalization of numbers (integers and decimals)."""
        line = "Price: 123.45 Quantity: 100 Total: 12345"
        normalized = normalize_line(line)
        assert normalized == "price: <num> quantity: <num> total: <num>"
    
    def test_normalize_whitespace(self):
        """Test normalization of multiple whitespaces."""
        line = "Message   with    multiple     spaces"
        normalized = normalize_line(line)
        assert normalized == "message with multiple spaces"
    
    def test_normalize_case_conversion(self):
        """Test conversion to lowercase."""
        line = "UPPERCASE Mixed CaSe lowercase"
        normalized = normalize_line(line)
        # "UPPERCASE" is 9 chars (>=6) so it gets replaced with <id>
        assert normalized == "<id> mixed case lowercase"
    
    def test_normalize_complex_log_line(self):
        """Test normalization of a complex log line with all patterns."""
        line = "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123DEF quantity=100.50 price=45.25"
        normalized = normalize_line(line)
        assert normalized == "<ts> info newordersingle clordid=<id> quantity=<num> price=<num>"
    
    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        line = ""
        normalized = normalize_line(line)
        assert normalized == ""
    
    def test_normalize_whitespace_only(self):
        """Test normalization of whitespace-only string."""
        line = "   \t  \n  "
        normalized = normalize_line(line)
        assert normalized == ""
    
    def test_normalize_no_patterns(self):
        """Test normalization of line with no special patterns."""
        line = "simple log message without patterns"
        normalized = normalize_line(line)
        assert normalized == "simple log message without patterns"
    
    def test_normalize_preserves_non_matching_alphanumeric(self):
        """Test that short alphanumeric strings are preserved."""
        line = "Order ID: A1B2 short ABC but LONGIDENTIFIER123456 is replaced"
        normalized = normalize_line(line)
        # A1B2 contains digits so gets normalized: a<num>b<num>
        assert normalized == "order id: a<num>b<num> short abc but <id> is replaced"


class TestExtractTimestamp:
    """Test the extract_timestamp function."""
    
    def test_extract_timestamp_present(self):
        """Test extracting timestamp when present."""
        line = "2023-10-26T12:34:56.789 INFO Some log message"
        timestamp = extract_timestamp(line)
        assert timestamp == "2023-10-26T12:34:56.789"
    
    def test_extract_timestamp_multiple(self):
        """Test extracting first timestamp when multiple are present."""
        line = "2023-10-26T12:34:56.789 Process started at 2024-01-01T00:00:00.000"
        timestamp = extract_timestamp(line)
        assert timestamp == "2023-10-26T12:34:56.789"
    
    def test_extract_timestamp_not_present(self):
        """Test extracting timestamp when not present."""
        line = "INFO Some log message without timestamp"
        timestamp = extract_timestamp(line)
        assert timestamp == ""
    
    def test_extract_timestamp_empty_string(self):
        """Test extracting timestamp from empty string."""
        line = ""
        timestamp = extract_timestamp(line)
        assert timestamp == ""
    
    def test_extract_timestamp_partial_match(self):
        """Test that partial timestamp patterns don't match."""
        line = "Date: 2023-10-26 Time: 12:34:56 (not ISO format)"
        timestamp = extract_timestamp(line)
        assert timestamp == ""
    
    def test_extract_timestamp_different_formats(self):
        """Test various valid ISO timestamp formats."""
        test_cases = [
            ("2023-10-26T12:34:56.789", "2023-10-26T12:34:56.789"),
            ("2023-10-26T12:34:56.123456", "2023-10-26T12:34:56.123456"),
            ("2023-01-01T00:00:00.0", "2023-01-01T00:00:00.0"),
            ("9999-12-31T23:59:59.999", "9999-12-31T23:59:59.999"),
        ]
        
        for line, expected in test_cases:
            timestamp = extract_timestamp(f"LOG {line} MESSAGE")
            assert timestamp == expected
    
    def test_extract_timestamp_in_middle(self):
        """Test extracting timestamp when it's in the middle of the line."""
        line = "Process started at 2023-10-26T12:34:56.789 successfully"
        timestamp = extract_timestamp(line)
        assert timestamp == "2023-10-26T12:34:56.789"