from dataclasses import dataclass
from typing import Optional, Dict, Tuple

@dataclass
class ClassifiedEvent:
    raw_line: str
    normalized_line: str
    timestamp: Optional[str]
    entity_id: Optional[str]
    rule_name: Optional[str]
    state: Optional[str]

@dataclass
class FSM:
    # transitions[from_state][(to_state, trigger_rule)] = count
    transitions: Dict[str, Dict[Tuple[str, str], int]]
