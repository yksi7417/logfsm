import re
from .models import ClassifiedEvent
from .normalizer import normalize_line, extract_timestamp

class CompiledRule:
    def __init__(self, name: str, regex: str, state: str):
        self.name = name
        self.state = state
        self.pattern = re.compile(regex)

    def match(self, raw_line: str):
        return self.pattern.search(raw_line)

def compile_rules(cfg):
    compiled = []
    for rule in cfg.signal_rules:
        compiled.append(
            CompiledRule(
                name=rule["name"],
                regex=rule["regex"],
                state=rule["state"]
            )
        )
    return compiled

def classify_line(raw_line: str, compiled_rules, cfg):
    norm = normalize_line(raw_line)
    ts = extract_timestamp(raw_line)
    match_rule = None
    entity_id_val = None
    state = None

    for rule in compiled_rules:
        m = rule.match(raw_line)
        if m:
            match_rule = rule.name
            state = rule.state
            entity_id_val = m.groupdict().get(cfg.entity_id_field, None)
            break

    return ClassifiedEvent(
        raw_line=raw_line,
        normalized_line=norm,
        timestamp=ts,
        entity_id=entity_id_val,
        rule_name=match_rule,
        state=state
    )
