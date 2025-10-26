import pytest
import re
from logfsm.rule_engine import CompiledRule, compile_rules, classify_line
from logfsm.config import Config
from logfsm.models import ClassifiedEvent


class TestCompiledRule:
    """Test the CompiledRule class."""
    
    def test_compiled_rule_creation(self):
        """Test creating a CompiledRule."""
        rule = CompiledRule(
            name="TEST_RULE",
            regex=r"test.*pattern",
            state="TEST_STATE"
        )
        
        assert rule.name == "TEST_RULE"
        assert rule.state == "TEST_STATE"
        assert isinstance(rule.pattern, re.Pattern)
    
    def test_compiled_rule_match_success(self):
        """Test successful matching with a CompiledRule."""
        rule = CompiledRule(
            name="ORDER_RULE",
            regex=r"(?i)order.*clordid=(?P<order_id>[A-Z0-9]+)",
            state="ORDER_STATE"
        )
        
        line = "NewOrderSingle ClOrdID=ABC123DEF quantity=100"
        match = rule.match(line)
        
        assert match is not None
        assert match.groupdict()["order_id"] == "ABC123DEF"
    
    def test_compiled_rule_match_failure(self):
        """Test failed matching with a CompiledRule."""
        rule = CompiledRule(
            name="ORDER_RULE",
            regex=r"(?i)order.*clordid=(?P<order_id>[A-Z0-9]+)",
            state="ORDER_STATE"
        )
        
        line = "ExecutionReport without ClOrdID"
        match = rule.match(line)
        
        assert match is None
    
    def test_compiled_rule_case_insensitive(self):
        """Test case insensitive matching."""
        rule = CompiledRule(
            name="CASE_RULE",
            regex=r"(?i)test",
            state="TEST_STATE"
        )
        
        assert rule.match("TEST message") is not None
        assert rule.match("test message") is not None
        assert rule.match("Test message") is not None
        assert rule.match("other message") is None


class TestCompileRules:
    """Test the compile_rules function."""
    
    def test_compile_rules_empty(self):
        """Test compiling empty rules list."""
        cfg = Config({"signal_rules": []})
        compiled = compile_rules(cfg)
        
        assert compiled == []
    
    def test_compile_rules_single(self):
        """Test compiling a single rule."""
        cfg_data = {
            "signal_rules": [
                {
                    "name": "NEW_ORDER",
                    "regex": r"(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "NEW_REQUESTED"
                }
            ]
        }
        cfg = Config(cfg_data)
        compiled = compile_rules(cfg)
        
        assert len(compiled) == 1
        assert compiled[0].name == "NEW_ORDER"
        assert compiled[0].state == "NEW_REQUESTED"
        assert isinstance(compiled[0].pattern, re.Pattern)
    
    def test_compile_rules_multiple(self):
        """Test compiling multiple rules."""
        cfg_data = {
            "signal_rules": [
                {
                    "name": "NEW_ORDER",
                    "regex": r"(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "NEW_REQUESTED"
                },
                {
                    "name": "ACK_NEW",
                    "regex": r"(?i)executionreport.*exectype=0.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "ACKED_NEW"
                }
            ]
        }
        cfg = Config(cfg_data)
        compiled = compile_rules(cfg)
        
        assert len(compiled) == 2
        assert compiled[0].name == "NEW_ORDER"
        assert compiled[1].name == "ACK_NEW"
        assert compiled[0].state == "NEW_REQUESTED"
        assert compiled[1].state == "ACKED_NEW"


class TestClassifyLine:
    """Test the classify_line function."""
    
    def setup_method(self):
        """Set up test configuration and compiled rules."""
        self.cfg_data = {
            "signal_rules": [
                {
                    "name": "NEW_ORDER",
                    "regex": r"(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "NEW_REQUESTED"
                },
                {
                    "name": "ACK_NEW",
                    "regex": r"(?i)executionreport.*exectype=0.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "ACKED_NEW"
                },
                {
                    "name": "FILLED",
                    "regex": r"(?i)executionreport.*exectype=f.*leavesqty=0.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "FILLED"
                }
            ],
            "entity_id_field": "order_id",
            "start_state": "START",
            "unknown_state": "UNKNOWN"
        }
        self.cfg = Config(self.cfg_data)
        self.compiled_rules = compile_rules(self.cfg)
    
    def test_classify_line_match_first_rule(self):
        """Test classifying a line that matches the first rule."""
        line = "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123DEF quantity=100"
        event = classify_line(line, self.compiled_rules, self.cfg)
        
        assert event.raw_line == line
        assert event.normalized_line == "<ts> info newordersingle clordid=<id> quantity=<num>"
        assert event.timestamp == "2023-10-26T12:34:56.789"
        assert event.entity_id == "ABC123DEF"
        assert event.rule_name == "NEW_ORDER"
        assert event.state == "NEW_REQUESTED"
    
    def test_classify_line_match_second_rule(self):
        """Test classifying a line that matches the second rule."""
        line = "2023-10-26T12:35:00.123 INFO ExecutionReport ExecType=0 OrdStatus=0 ClOrdID=ABC123DEF"
        event = classify_line(line, self.compiled_rules, self.cfg)
        
        assert event.raw_line == line
        assert event.entity_id == "ABC123DEF"
        assert event.rule_name == "ACK_NEW"
        assert event.state == "ACKED_NEW"
    
    def test_classify_line_no_match(self):
        """Test classifying a line that doesn't match any rule."""
        line = "2023-10-26T12:35:00.123 INFO Unknown log message"
        event = classify_line(line, self.compiled_rules, self.cfg)
        
        assert event.raw_line == line
        assert event.timestamp == "2023-10-26T12:35:00.123"
        assert event.entity_id is None
        assert event.rule_name is None
        assert event.state is None
    
    def test_classify_line_no_timestamp(self):
        """Test classifying a line without timestamp."""
        line = "NewOrderSingle ClOrdID=ABC123DEF quantity=100"
        event = classify_line(line, self.compiled_rules, self.cfg)
        
        assert event.raw_line == line
        assert event.timestamp == ""
        assert event.entity_id == "ABC123DEF"
        assert event.rule_name == "NEW_ORDER"
        assert event.state == "NEW_REQUESTED"
    
    def test_classify_line_no_entity_id(self):
        """Test classifying a line that matches rule but has no entity ID."""
        # Create a rule without named group
        cfg_data = {
            "signal_rules": [
                {
                    "name": "SIMPLE_RULE",
                    "regex": r"(?i)simple.*message",
                    "state": "SIMPLE_STATE"
                }
            ],
            "entity_id_field": "order_id"
        }
        cfg = Config(cfg_data)
        compiled_rules = compile_rules(cfg)
        
        line = "Simple message without entity ID"
        event = classify_line(line, compiled_rules, cfg)
        
        assert event.raw_line == line
        assert event.entity_id is None
        assert event.rule_name == "SIMPLE_RULE"
        assert event.state == "SIMPLE_STATE"
    
    def test_classify_line_different_entity_field(self):
        """Test classifying with different entity ID field name."""
        cfg_data = {
            "signal_rules": [
                {
                    "name": "CUSTOM_RULE",
                    "regex": r"(?i)transaction.*id=(?P<transaction_id>[A-Z0-9]+)",
                    "state": "TRANSACTION_STATE"
                }
            ],
            "entity_id_field": "transaction_id"
        }
        cfg = Config(cfg_data)
        compiled_rules = compile_rules(cfg)
        
        line = "Transaction processing ID=TXN123ABC"
        event = classify_line(line, compiled_rules, cfg)
        
        assert event.entity_id == "TXN123ABC"
        assert event.rule_name == "CUSTOM_RULE"
        assert event.state == "TRANSACTION_STATE"
    
    def test_classify_line_empty_string(self):
        """Test classifying an empty string."""
        line = ""
        event = classify_line(line, self.compiled_rules, self.cfg)
        
        assert event.raw_line == ""
        assert event.normalized_line == ""
        assert event.timestamp == ""
        assert event.entity_id is None
        assert event.rule_name is None
        assert event.state is None
    
    def test_classify_line_rule_priority(self):
        """Test that rules are matched in order (first match wins)."""
        # Create overlapping rules
        cfg_data = {
            "signal_rules": [
                {
                    "name": "GENERAL_RULE",
                    "regex": r"(?i)execution.*report",
                    "state": "GENERAL_STATE"
                },
                {
                    "name": "SPECIFIC_RULE",
                    "regex": r"(?i)executionreport.*filled",
                    "state": "SPECIFIC_STATE"
                }
            ]
        }
        cfg = Config(cfg_data)
        compiled_rules = compile_rules(cfg)
        
        line = "ExecutionReport status filled"
        event = classify_line(line, compiled_rules, cfg)
        
        # Should match first rule, not second
        assert event.rule_name == "GENERAL_RULE"
        assert event.state == "GENERAL_STATE"