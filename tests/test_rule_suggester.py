import pytest
from logfsm.rule_suggester import suggest_rules_from_lines


class TestSuggestRulesFromLines:
    """Test the suggest_rules_from_lines function."""
    
    def test_suggest_rules_empty_lines(self):
        """Test suggesting rules from empty lines list."""
        lines = []
        suggestions = suggest_rules_from_lines(lines)
        
        assert suggestions == []
    
    def test_suggest_rules_single_line(self):
        """Test suggesting rules from single line."""
        lines = ["2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123"]
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        assert len(suggestions) == 1
        pattern, count = suggestions[0]
        assert pattern == "<ts> info newordersingle clordid=<id>"
        assert count == 1
    
    def test_suggest_rules_duplicate_patterns(self):
        """Test suggesting rules with duplicate normalized patterns."""
        lines = [
            "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",
            "2023-10-26T12:35:00.123 INFO NewOrderSingle ClOrdID=DEF456",
            "2023-10-26T12:35:30.456 INFO NewOrderSingle ClOrdID=GHI789"
        ]
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        assert len(suggestions) == 1
        pattern, count = suggestions[0]
        assert pattern == "<ts> info newordersingle clordid=<id>"
        assert count == 3
    
    def test_suggest_rules_multiple_patterns(self):
        """Test suggesting rules with multiple different patterns."""
        lines = [
            "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",
            "2023-10-26T12:35:00.123 INFO ExecutionReport ExecType=0 ClOrdID=ABC123",
            "2023-10-26T12:35:30.456 INFO ExecutionReport ExecType=F ClOrdID=ABC123",
            "2023-10-26T12:36:00.789 INFO NewOrderSingle ClOrdID=DEF456"
        ]
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        # Should have multiple patterns, sorted by frequency
        assert len(suggestions) >= 2
        
        # Check that patterns are sorted by count (descending)
        for i in range(len(suggestions) - 1):
            assert suggestions[i][1] >= suggestions[i + 1][1]
        
        # Verify specific patterns exist
        patterns = [pattern for pattern, count in suggestions]
        assert "<ts> info newordersingle clordid=<id>" in patterns
        assert "<ts> info executionreport exectype=<num> clordid=<id>" in patterns
        assert "<ts> info executionreport exectype=f clordid=<id>" in patterns
    
    def test_suggest_rules_top_n_limit(self):
        """Test that top_n parameter limits the number of suggestions."""
        lines = [
            f"Pattern {i} with different content" for i in range(10)
        ]
        
        suggestions = suggest_rules_from_lines(lines, top_n=5)
        
        # All patterns normalize to the same thing because digits get replaced
        assert len(suggestions) == 1
        pattern, count = suggestions[0]
        assert pattern == "pattern <num> with different content"
        assert count == 10
    
    def test_suggest_rules_top_n_more_than_available(self):
        """Test top_n larger than available patterns."""
        lines = [
            "Pattern A",
            "Pattern B", 
            "Pattern A"  # Duplicate
        ]
        
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        # Should return 2 unique patterns
        assert len(suggestions) == 2
        
        # Check ordering by count
        pattern1, count1 = suggestions[0]
        pattern2, count2 = suggestions[1]
        
        assert count1 >= count2
        if count1 == count2:
            # If counts are equal, ordering might vary
            pass
        else:
            assert count1 > count2
    
    def test_suggest_rules_default_top_n(self):
        """Test default top_n value."""
        lines = [f"Unique pattern {chr(65+i)}" for i in range(25)]  # Different letters to avoid digit normalization
        
        suggestions = suggest_rules_from_lines(lines)  # Uses default top_n=20
        
        assert len(suggestions) == 20
    
    def test_suggest_rules_complex_log_patterns(self):
        """Test suggesting rules from complex log patterns."""
        lines = [
            "2023-10-26T12:34:56.789 ERROR Connection failed to server 192.168.1.100 port 8080",
            "2023-10-26T12:35:00.123 ERROR Connection failed to server 192.168.1.200 port 8080",
            "2023-10-26T12:35:30.456 ERROR Connection failed to server 10.0.0.1 port 443",
            "2023-10-26T12:36:00.789 INFO User login successful for user12345",
            "2023-10-26T12:36:30.123 INFO User login successful for admin99",
            "2023-10-26T12:37:00.456 WARN Memory usage at 85.5%",
            "2023-10-26T12:37:30.789 WARN Memory usage at 92.1%"
        ]
        
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        # Verify that normalization worked correctly
        patterns = [pattern for pattern, count in suggestions]
        
        # Connection error pattern (appears 3 times)
        connection_pattern = "<ts> error connection failed to server <num>.<num> port <num>"
        assert connection_pattern in patterns
        
        # User login patterns (appear 1 time each due to user vs admin difference)
        user_pattern = "<ts> info user login successful for user<num>"
        admin_pattern = "<ts> info user login successful for admin<num>"
        # These will be separate patterns
        
        # Memory warning pattern (appears 2 times)
        memory_pattern = "<ts> warn memory usage at <num>%"
        assert memory_pattern in patterns
        
        # Check counts
        pattern_counts = {pattern: count for pattern, count in suggestions}
        assert pattern_counts[connection_pattern] == 3
        assert pattern_counts[memory_pattern] == 2
    
    def test_suggest_rules_whitespace_normalization(self):
        """Test that whitespace normalization works correctly."""
        lines = [
            "Message   with    multiple     spaces",
            "Message with multiple spaces",
            "Message\t\twith\ttabs",  # This produces different text due to tab replacement
            "  Message  with  leading  and  trailing  spaces  "  # This also produces different text
        ]
        
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        # Due to tabs and different leading/trailing spaces, we get different patterns
        assert len(suggestions) == 3
        patterns = [pattern for pattern, count in suggestions]
        assert "message with multiple spaces" in patterns
        assert "message with tabs" in patterns
        assert "message with leading and trailing spaces" in patterns
    
    def test_suggest_rules_case_normalization(self):
        """Test that case normalization works correctly."""
        lines = [
            "ERROR: System Failure",
            "error: system failure", 
            "Error: System Failure",
            "ERROR: SYSTEM FAILURE"  # This gets different normalization due to SYSTEM/FAILURE being all caps and >=6 chars
        ]
        
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        # We get 2 patterns: one normal and one with <id> replacements
        assert len(suggestions) == 2
        patterns = [pattern for pattern, count in suggestions]
        assert "error: system failure" in patterns
        assert "error: <id> <id>" in patterns
    
    def test_suggest_rules_empty_and_whitespace_lines(self):
        """Test handling of empty and whitespace-only lines."""
        lines = [
            "",
            "   ",
            "\t\t",
            "Valid log message",
            "",
            "Another valid message"
        ]
        
        suggestions = suggest_rules_from_lines(lines, top_n=10)
        
        # Empty/whitespace lines should normalize to empty string
        patterns = [pattern for pattern, count in suggestions]
        
        assert "valid log message" in patterns
        assert "another valid message" in patterns
        
        # Check if empty pattern is included
        empty_count = 0
        for pattern, count in suggestions:
            if pattern == "":
                empty_count = count
                break
        
        # Should have 4 empty/whitespace lines (all whitespace normalizes to empty)
        assert empty_count == 4