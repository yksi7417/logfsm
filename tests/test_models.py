import pytest
from logfsm.models import ClassifiedEvent, FSM


class TestClassifiedEvent:
    """Test the ClassifiedEvent dataclass."""
    
    def test_classified_event_creation(self):
        """Test creating a ClassifiedEvent with all fields."""
        event = ClassifiedEvent(
            raw_line="2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",
            normalized_line="<ts> info newordersingle clordid=<id>",
            timestamp="2023-10-26T12:34:56.789",
            entity_id="ABC123",
            rule_name="NEW_ORDER",
            state="NEW_REQUESTED"
        )
        
        assert event.raw_line == "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123"
        assert event.normalized_line == "<ts> info newordersingle clordid=<id>"
        assert event.timestamp == "2023-10-26T12:34:56.789"
        assert event.entity_id == "ABC123"
        assert event.rule_name == "NEW_ORDER"
        assert event.state == "NEW_REQUESTED"
    
    def test_classified_event_with_none_values(self):
        """Test creating a ClassifiedEvent with optional None values."""
        event = ClassifiedEvent(
            raw_line="Unknown log line",
            normalized_line="unknown log line",
            timestamp=None,
            entity_id=None,
            rule_name=None,
            state=None
        )
        
        assert event.raw_line == "Unknown log line"
        assert event.normalized_line == "unknown log line"
        assert event.timestamp is None
        assert event.entity_id is None
        assert event.rule_name is None
        assert event.state is None
    
    def test_classified_event_equality(self):
        """Test equality comparison between ClassifiedEvent instances."""
        event1 = ClassifiedEvent(
            raw_line="test",
            normalized_line="test",
            timestamp="2023-10-26T12:34:56.789",
            entity_id="ABC123",
            rule_name="TEST_RULE",
            state="TEST_STATE"
        )
        
        event2 = ClassifiedEvent(
            raw_line="test",
            normalized_line="test",
            timestamp="2023-10-26T12:34:56.789",
            entity_id="ABC123",
            rule_name="TEST_RULE",
            state="TEST_STATE"
        )
        
        event3 = ClassifiedEvent(
            raw_line="different",
            normalized_line="different",
            timestamp="2023-10-26T12:34:56.789",
            entity_id="ABC123",
            rule_name="TEST_RULE",
            state="TEST_STATE"
        )
        
        assert event1 == event2
        assert event1 != event3


class TestFSM:
    """Test the FSM dataclass."""
    
    def test_fsm_creation_empty(self):
        """Test creating an empty FSM."""
        fsm = FSM(transitions={})
        assert fsm.transitions == {}
    
    def test_fsm_creation_with_transitions(self):
        """Test creating an FSM with transitions."""
        transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 5,
                ("REJECTED", "REJECT"): 2
            },
            "NEW_REQUESTED": {
                ("ACKED_NEW", "ACK_NEW"): 4,
                ("REJECTED", "REJECT"): 1
            }
        }
        
        fsm = FSM(transitions=transitions)
        assert fsm.transitions == transitions
        assert fsm.transitions["START"][("NEW_REQUESTED", "NEW_ORDER")] == 5
        assert fsm.transitions["NEW_REQUESTED"][("ACKED_NEW", "ACK_NEW")] == 4
    
    def test_fsm_equality(self):
        """Test equality comparison between FSM instances."""
        transitions1 = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 5
            }
        }
        
        transitions2 = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 5
            }
        }
        
        transitions3 = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 3
            }
        }
        
        fsm1 = FSM(transitions=transitions1)
        fsm2 = FSM(transitions=transitions2)
        fsm3 = FSM(transitions=transitions3)
        
        assert fsm1 == fsm2
        assert fsm1 != fsm3
    
    def test_fsm_access_nonexistent_state(self):
        """Test accessing a non-existent state in FSM."""
        fsm = FSM(transitions={})
        
        # Should not raise an error, but return empty dict or None
        result = fsm.transitions.get("NONEXISTENT_STATE", {})
        assert result == {}