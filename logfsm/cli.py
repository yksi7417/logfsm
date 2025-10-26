import sys
import argparse
from .config import Config
from .rule_engine import compile_rules, classify_line
from .rule_suggester import suggest_rules_from_lines
from .fsm_builder import build_fsm, fsm_to_dot

def cmd_suggest_rules(args):
    raw_lines = [line.rstrip("\n") for line in sys.stdin]

    cfg = Config.load(args.config) if args.config else Config({"signal_rules": []})
    compiled = compile_rules(cfg)

    unmatched = []
    for ln in raw_lines:
        ev = classify_line(ln, compiled, cfg)
        if ev.rule_name is None:
            unmatched.append(ln)

    suggestions = suggest_rules_from_lines(unmatched, top_n=args.top_n)

    print("# Suggested candidate patterns (normalized form, count):")
    for pattern, count in suggestions:
        print(f"- {count}x  {pattern}")

    if args.save is not None:
        cfg_out = Config.load(args.config) if args.config else Config({"signal_rules": []})
        for i, (pattern, count) in enumerate(suggestions):
            cfg_out.signal_rules.append({
                "name": f"AUTO_RULE_{i}",
                "regex": pattern,
                "state": "TBD_STATE"
            })
        cfg_out.save(args.save)
        print(f"\nWrote draft rules to {args.save}")

def cmd_build_fsm(args):
    raw_lines = [line.rstrip("\n") for line in sys.stdin]

    cfg = Config.load(args.config)
    compiled = compile_rules(cfg)

    classified_events = []
    for ln in raw_lines:
        ev = classify_line(ln, compiled, cfg)
        if ev.entity_id and ev.state:
            classified_events.append(ev)

    fsm = build_fsm(classified_events, cfg.start_state)
    dot = fsm_to_dot(fsm)

    if args.output_dot:
        with open(args.output_dot, "w", encoding="utf-8") as f:
            f.write(dot)
        print(f"FSM DOT written to {args.output_dot}")
    else:
        print(dot)

def main():
    p = argparse.ArgumentParser(prog="logfsm", description="Log → Rules → FSM tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_rules = sub.add_parser("suggest-rules", help="Mine candidate regex rules from stdin logs")
    p_rules.add_argument("--config", help="existing rules.yaml (optional)")
    p_rules.add_argument("--top-n", type=int, default=20)
    p_rules.add_argument("--save", help="write updated draft config to this path")
    p_rules.set_defaults(func=cmd_suggest_rules)

    p_fsm = sub.add_parser("build-fsm", help="Build FSM DOT from stdin logs using rules")
    p_fsm.add_argument("--config", required=True, help="rules.yaml with signal_rules[] etc")
    p_fsm.add_argument("--output-dot", help="write Graphviz DOT instead of printing")
    p_fsm.set_defaults(func=cmd_build_fsm)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
