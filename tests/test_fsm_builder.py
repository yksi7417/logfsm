import pytest
from logfsm.fsm_builder import build_fsm, fsm_to_dot
from logfsm.models import ClassifiedEvent, FSM


class TestBuildFSM:
    """Test the build_fsm function."""
    
    def test_build_fsm_empty_events(self):
        """Test building FSM with empty events list."""
        events = []
        fsm = build_fsm(events, "START")
        
        assert fsm.transitions == {}
    
    def test_build_fsm_single_entity_single_transition(self):
        """Test building FSM with single entity and single transition."""
        events = [
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        expected_transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_single_entity_multiple_transitions(self):
        """Test building FSM with single entity and multiple transitions."""
        events = [
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            ),
            ClassifiedEvent(
                raw_line="log line 2",
                normalized_line="normalized 2",
                timestamp="2023-10-26T12:35:00.123",
                entity_id="ORDER1",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            ),
            ClassifiedEvent(
                raw_line="log line 3",
                normalized_line="normalized 3",
                timestamp="2023-10-26T12:35:30.456",
                entity_id="ORDER1",
                rule_name="FILLED",
                state="FILLED"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        expected_transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 1
            },
            "NEW_REQUESTED": {
                ("ACKED_NEW", "ACK_NEW"): 1
            },
            "ACKED_NEW": {
                ("FILLED", "FILLED"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_multiple_entities_same_pattern(self):
        """Test building FSM with multiple entities following same pattern."""
        events = [
            # Entity 1
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            ),
            ClassifiedEvent(
                raw_line="log line 2",
                normalized_line="normalized 2",
                timestamp="2023-10-26T12:35:00.123",
                entity_id="ORDER1",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            ),
            # Entity 2
            ClassifiedEvent(
                raw_line="log line 3",
                normalized_line="normalized 3",
                timestamp="2023-10-26T12:36:00.789",
                entity_id="ORDER2",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            ),
            ClassifiedEvent(
                raw_line="log line 4",
                normalized_line="normalized 4",
                timestamp="2023-10-26T12:36:30.123",
                entity_id="ORDER2",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        expected_transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 2  # Both entities follow same pattern
            },
            "NEW_REQUESTED": {
                ("ACKED_NEW", "ACK_NEW"): 2
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_different_patterns(self):
        """Test building FSM with entities following different patterns."""
        events = [
            # Entity 1: NEW -> ACK -> FILLED
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            ),
            ClassifiedEvent(
                raw_line="log line 2",
                normalized_line="normalized 2",
                timestamp="2023-10-26T12:35:00.123",
                entity_id="ORDER1",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            ),
            ClassifiedEvent(
                raw_line="log line 3",
                normalized_line="normalized 3",
                timestamp="2023-10-26T12:35:30.456",
                entity_id="ORDER1",
                rule_name="FILLED",
                state="FILLED"
            ),
            # Entity 2: NEW -> REJECTED
            ClassifiedEvent(
                raw_line="log line 4",
                normalized_line="normalized 4",
                timestamp="2023-10-26T12:36:00.789",
                entity_id="ORDER2",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            ),
            ClassifiedEvent(
                raw_line="log line 5",
                normalized_line="normalized 5",
                timestamp="2023-10-26T12:36:10.123",
                entity_id="ORDER2",
                rule_name="REJECT",
                state="REJECTED"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        expected_transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 2
            },
            "NEW_REQUESTED": {
                ("ACKED_NEW", "ACK_NEW"): 1,
                ("REJECTED", "REJECT"): 1
            },
            "ACKED_NEW": {
                ("FILLED", "FILLED"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_unordered_timestamps(self):
        """Test building FSM with events not in timestamp order."""
        events = [
            ClassifiedEvent(
                raw_line="log line 2",
                normalized_line="normalized 2",
                timestamp="2023-10-26T12:35:00.123",
                entity_id="ORDER1",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            ),
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        # Should be sorted by timestamp, so NEW_ORDER comes first
        expected_transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 1
            },
            "NEW_REQUESTED": {
                ("ACKED_NEW", "ACK_NEW"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_missing_entity_id(self):
        """Test building FSM with events missing entity_id."""
        events = [
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id=None,  # Missing entity ID
                rule_name="NEW_ORDER",
                state="NEW_REQUESTED"
            ),
            ClassifiedEvent(
                raw_line="log line 2",
                normalized_line="normalized 2",
                timestamp="2023-10-26T12:35:00.123",
                entity_id="ORDER1",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        # Only the event with entity_id should be processed
        expected_transitions = {
            "START": {
                ("ACKED_NEW", "ACK_NEW"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_missing_state(self):
        """Test building FSM with events missing state."""
        events = [
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name="NEW_ORDER",
                state=None  # Missing state
            ),
            ClassifiedEvent(
                raw_line="log line 2",
                normalized_line="normalized 2",
                timestamp="2023-10-26T12:35:00.123",
                entity_id="ORDER1",
                rule_name="ACK_NEW",
                state="ACKED_NEW"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        # Only the event with state should be processed
        expected_transitions = {
            "START": {
                ("ACKED_NEW", "ACK_NEW"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions
    
    def test_build_fsm_missing_rule_name(self):
        """Test building FSM with events missing rule_name."""
        events = [
            ClassifiedEvent(
                raw_line="log line 1",
                normalized_line="normalized 1",
                timestamp="2023-10-26T12:34:56.789",
                entity_id="ORDER1",
                rule_name=None,  # Missing rule name
                state="NEW_REQUESTED"
            )
        ]
        
        fsm = build_fsm(events, "START")
        
        # Should use "UNKNOWN_RULE" for missing rule names
        expected_transitions = {
            "START": {
                ("NEW_REQUESTED", "UNKNOWN_RULE"): 1
            }
        }
        
        assert fsm.transitions == expected_transitions


class TestFSMToDot:
    """Test the fsm_to_dot function."""
    
    def test_fsm_to_dot_empty(self):
        """Test converting empty FSM to DOT format."""
        fsm = FSM(transitions={})
        dot = fsm_to_dot(fsm)
        
        expected = "digraph FSM {\n}"
        assert dot == expected
    
    def test_fsm_to_dot_single_transition(self):
        """Test converting FSM with single transition to DOT format."""
        transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 1
            }
        }
        fsm = FSM(transitions=transitions)
        dot = fsm_to_dot(fsm)
        
        lines = dot.split('\n')
        assert lines[0] == "digraph FSM {"
        assert lines[-1] == "}"
        assert '  "START" -> "NEW_REQUESTED" [label="NEW_ORDER\\n(1)"];' in lines
    
    def test_fsm_to_dot_multiple_transitions(self):
        """Test converting FSM with multiple transitions to DOT format."""
        transitions = {
            "START": {
                ("NEW_REQUESTED", "NEW_ORDER"): 2,
                ("REJECTED", "REJECT"): 1
            },
            "NEW_REQUESTED": {
                ("ACKED_NEW", "ACK_NEW"): 2
            }
        }
        fsm = FSM(transitions=transitions)
        dot = fsm_to_dot(fsm)
        
        lines = dot.split('\n')
        assert lines[0] == "digraph FSM {"
        assert lines[-1] == "}"
        
        # Check that all transitions are present
        dot_content = '\n'.join(lines)
        assert '"START" -> "NEW_REQUESTED" [label="NEW_ORDER\\n(2)"];' in dot_content
        assert '"START" -> "REJECTED" [label="REJECT\\n(1)"];' in dot_content
        assert '"NEW_REQUESTED" -> "ACKED_NEW" [label="ACK_NEW\\n(2)"];' in dot_content
    
    def test_fsm_to_dot_special_characters(self):
        """Test converting FSM with special characters in states/rules."""
        transitions = {
            "START": {
                ("STATE_WITH_UNDERSCORE", "RULE_WITH_UNDERSCORE"): 1
            }
        }
        fsm = FSM(transitions=transitions)
        dot = fsm_to_dot(fsm)
        
        assert '"START" -> "STATE_WITH_UNDERSCORE" [label="RULE_WITH_UNDERSCORE\\n(1)"];' in dot
    
    def test_fsm_to_dot_self_transition(self):
        """Test converting FSM with self-transitions."""
        transitions = {
            "WAITING": {
                ("WAITING", "HEARTBEAT"): 5
            }
        }
        fsm = FSM(transitions=transitions)
        dot = fsm_to_dot(fsm)
        
        assert '"WAITING" -> "WAITING" [label="HEARTBEAT\\n(5)"];' in dot