logfsm
======

Pipeline tool for:
1. suggesting new regex rules from raw logs
2. applying rules to logs and inferring an FSM (finite state machine)

## Installation

```bash
pip install -e .
```

For development with testing dependencies:

```bash
pip install -e .[test]
```

## Usage Examples

```bash
cat abc.log | logfsm suggest-rules --top-n 30 --save draft_rules.yaml
cat abc.log | logfsm build-fsm --config rules.yaml --output-dot fsm.dot
```

## Development

### Running Tests

The project uses pytest for testing. To run all tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=logfsm --cov-report=term-missing
```

To run a specific test file:

```bash
pytest tests/test_models.py -v
```

### Test Structure

- `tests/test_models.py` - Tests for data models (ClassifiedEvent, FSM)
- `tests/test_config.py` - Tests for configuration loading/saving
- `tests/test_normalizer.py` - Tests for log line normalization
- `tests/test_rule_engine.py` - Tests for rule compilation and classification
- `tests/test_fsm_builder.py` - Tests for FSM building and DOT generation
- `tests/test_rule_suggester.py` - Tests for rule suggestion functionality
- `tests/test_cli.py` - Integration tests for CLI commands

### Continuous Integration

The project uses GitHub Actions for CI/CD. Tests are automatically run on:
- Push to main or develop branches
- Pull requests to main or develop branches
- Multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Multiple operating systems (Ubuntu, Windows, macOS)

See `.github/workflows/test.yml` for the complete CI configuration.
