logfsm
======

Pipeline tool for:
1. suggesting new regex rules from raw logs
2. applying rules to logs and inferring an FSM (finite state machine)

Usage examples:

    cat abc.log | logfsm suggest-rules --top-n 30 --save draft_rules.yaml
    cat abc.log | logfsm build-fsm --config rules.yaml --output-dot fsm.dot
