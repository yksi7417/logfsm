from collections import defaultdict
from .models import FSM

def build_fsm(events, start_state: str) -> FSM:
    per_entity = defaultdict(list)
    for ev in events:
        if ev.entity_id and ev.state:
            per_entity[ev.entity_id].append(ev)

    for eid in per_entity:
        per_entity[eid].sort(key=lambda e: e.timestamp)

    transition_counts = defaultdict(lambda: defaultdict(int))

    for eid, evs in per_entity.items():
        prev_state = start_state
        for ev in evs:
            next_state = ev.state
            trigger = ev.rule_name or "UNKNOWN_RULE"
            transition_counts[prev_state][(next_state, trigger)] += 1
            prev_state = next_state

    return FSM(transitions=transition_counts)

def fsm_to_dot(fsm: FSM) -> str:
    lines = ["digraph FSM {"]
    for from_state, dests in fsm.transitions.items():
        for (to_state, trigger), count in dests.items():
            label = f"{trigger}\\n({count})"
            lines.append(f'  "{from_state}" -> "{to_state}" [label="{label}"];')
    lines.append("}")
    return "\n".join(lines)
