import pytest
import tempfile
import os
import sys
import io
from unittest.mock import patch, MagicMock
import yaml
from logfsm.cli import cmd_suggest_rules, cmd_build_fsm, main


class TestCmdSuggestRules:
    """Test the cmd_suggest_rules function."""
    
    def test_cmd_suggest_rules_no_config(self, capsys):
        """Test suggest_rules command without existing config."""
        # Mock stdin
        mock_lines = [
            "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",
            "2023-10-26T12:35:00.123 INFO NewOrderSingle ClOrdID=DEF456",
            "2023-10-26T12:35:30.456 INFO ExecutionReport ExecType=0 ClOrdID=ABC123"
        ]
        
        # Create mock args
        args = MagicMock()
        args.config = None
        args.top_n = 20
        args.save = None
        
        with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
            cmd_suggest_rules(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check that suggestions are printed
        assert "# Suggested candidate patterns" in output
        assert "<ts> info newordersingle clordid=<id>" in output
        assert "<ts> info executionreport exectype=<num> clordid=<id>" in output
    
    def test_cmd_suggest_rules_with_existing_config(self, capsys):
        """Test suggest_rules command with existing config that filters some lines."""
        # Create temporary config file
        config_data = {
            "signal_rules": [
                {
                    "name": "NEW_ORDER",
                    "regex": r"(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "NEW_REQUESTED"
                }
            ],
            "entity_id_field": "order_id"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name
        
        try:
            mock_lines = [
                "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",  # Will match existing rule
                "2023-10-26T12:35:00.123 INFO ExecutionReport ExecType=0 ClOrdID=ABC123",  # Will not match
                "2023-10-26T12:35:30.456 INFO Unknown message"  # Will not match
            ]
            
            args = MagicMock()
            args.config = config_path
            args.top_n = 20
            args.save = None
            
            with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
                cmd_suggest_rules(args)
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should only suggest rules for unmatched lines
            assert "# Suggested candidate patterns" in output
            assert "<ts> info executionreport exectype=<num> clordid=<id>" in output
            assert "<ts> info unknown message" in output
            # Should not suggest rule for already matched NewOrderSingle
            assert "newordersingle" not in output.lower() or "2x" not in output
        
        finally:
            os.unlink(config_path)
    
    def test_cmd_suggest_rules_with_save(self):
        """Test suggest_rules command with save option."""
        mock_lines = [
            "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",
            "2023-10-26T12:35:00.123 INFO ExecutionReport ExecType=0 ClOrdID=ABC123"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            save_path = f.name
        
        try:
            args = MagicMock()
            args.config = None
            args.top_n = 20
            args.save = save_path
            
            with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
                cmd_suggest_rules(args)
            
            # Check that file was created and contains expected rules
            with open(save_path, 'r', encoding='utf-8') as f:
                saved_config = yaml.safe_load(f)
            
            assert 'signal_rules' in saved_config
            assert len(saved_config['signal_rules']) >= 2
            
            # Check that auto-generated rules are present
            rule_names = [rule['name'] for rule in saved_config['signal_rules']]
            assert 'AUTO_RULE_0' in rule_names
            assert 'AUTO_RULE_1' in rule_names
            
            # Check that states are set to TBD_STATE
            for rule in saved_config['signal_rules']:
                assert rule['state'] == 'TBD_STATE'
        
        finally:
            os.unlink(save_path)
    
    def test_cmd_suggest_rules_top_n_limit(self, capsys):
        """Test suggest_rules command with top_n limit."""
        mock_lines = [f"Unique pattern {chr(65+i)}" for i in range(10)]  # Use letters to avoid digit normalization
        
        args = MagicMock()
        args.config = None
        args.top_n = 3
        args.save = None
        
        with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
            cmd_suggest_rules(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should only show top 3 patterns
        pattern_lines = [line for line in output.split('\n') if line.startswith('- ')]
        assert len(pattern_lines) == 3


class TestCmdBuildFSM:
    """Test the cmd_build_fsm function."""
    
    def test_cmd_build_fsm_print_to_stdout(self, capsys):
        """Test build_fsm command printing DOT to stdout."""
        # Create temporary config file
        config_data = {
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
            ],
            "entity_id_field": "order_id",
            "start_state": "START"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name
        
        try:
            mock_lines = [
                "2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123",
                "2023-10-26T12:35:00.123 INFO ExecutionReport ExecType=0 ClOrdID=ABC123"
            ]
            
            args = MagicMock()
            args.config = config_path
            args.output_dot = None
            
            with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
                cmd_build_fsm(args)
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Check DOT format output
            assert "digraph FSM {" in output
            assert "}" in output
            assert "START" in output
            assert "NEW_REQUESTED" in output
            assert "ACKED_NEW" in output
        
        finally:
            os.unlink(config_path)
    
    def test_cmd_build_fsm_save_to_file(self, capsys):
        """Test build_fsm command saving DOT to file."""
        config_data = {
            "signal_rules": [
                {
                    "name": "NEW_ORDER",
                    "regex": r"(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "NEW_REQUESTED"
                }
            ],
            "entity_id_field": "order_id",
            "start_state": "START"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False, encoding='utf-8') as f:
            dot_path = f.name
        
        try:
            mock_lines = ["2023-10-26T12:34:56.789 INFO NewOrderSingle ClOrdID=ABC123"]
            
            args = MagicMock()
            args.config = config_path
            args.output_dot = dot_path
            
            with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
                cmd_build_fsm(args)
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Check that success message is printed
            assert f"FSM DOT written to {dot_path}" in output
            
            # Check that DOT file was created with correct content
            with open(dot_path, 'r', encoding='utf-8') as f:
                dot_content = f.read()
            
            assert "digraph FSM {" in dot_content
            assert "START" in dot_content
            assert "NEW_REQUESTED" in dot_content
        
        finally:
            os.unlink(config_path)
            os.unlink(dot_path)
    
    def test_cmd_build_fsm_no_matching_events(self, capsys):
        """Test build_fsm command with no events matching rules."""
        config_data = {
            "signal_rules": [
                {
                    "name": "NEW_ORDER",
                    "regex": r"(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)",
                    "state": "NEW_REQUESTED"
                }
            ],
            "entity_id_field": "order_id",
            "start_state": "START"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name
        
        try:
            mock_lines = ["2023-10-26T12:34:56.789 INFO Unknown message"]
            
            args = MagicMock()
            args.config = config_path
            args.output_dot = None
            
            with patch('sys.stdin', io.StringIO('\n'.join(mock_lines))):
                cmd_build_fsm(args)
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should produce empty FSM
            assert "digraph FSM {" in output
            assert "}" in output
            # Should not contain any transitions
            assert "->" not in output
        
        finally:
            os.unlink(config_path)


class TestMain:
    """Test the main function and argument parsing."""
    
    def test_main_suggest_rules_command(self):
        """Test main function with suggest-rules command."""
        test_args = ['logfsm', 'suggest-rules', '--top-n', '5']
        
        with patch('sys.argv', test_args):
            with patch('logfsm.cli.cmd_suggest_rules') as mock_cmd:
                main()
                mock_cmd.assert_called_once()
                args = mock_cmd.call_args[0][0]
                assert args.top_n == 5
    
    def test_main_build_fsm_command(self):
        """Test main function with build-fsm command."""
        test_args = ['logfsm', 'build-fsm', '--config', 'test.yaml']
        
        with patch('sys.argv', test_args):
            with patch('logfsm.cli.cmd_build_fsm') as mock_cmd:
                main()
                mock_cmd.assert_called_once()
                args = mock_cmd.call_args[0][0]
                assert args.config == 'test.yaml'
    
    def test_main_no_command(self):
        """Test main function without command (should show help)."""
        test_args = ['logfsm']
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        test_args = ['logfsm', 'invalid-command']
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_suggest_rules_with_all_options(self):
        """Test main function with all suggest-rules options."""
        test_args = [
            'logfsm', 'suggest-rules',
            '--config', 'input.yaml',
            '--top-n', '10',
            '--save', 'output.yaml'
        ]
        
        with patch('sys.argv', test_args):
            with patch('logfsm.cli.cmd_suggest_rules') as mock_cmd:
                main()
                mock_cmd.assert_called_once()
                args = mock_cmd.call_args[0][0]
                assert args.config == 'input.yaml'
                assert args.top_n == 10
                assert args.save == 'output.yaml'
    
    def test_main_build_fsm_with_all_options(self):
        """Test main function with all build-fsm options."""
        test_args = [
            'logfsm', 'build-fsm',
            '--config', 'rules.yaml',
            '--output-dot', 'fsm.dot'
        ]
        
        with patch('sys.argv', test_args):
            with patch('logfsm.cli.cmd_build_fsm') as mock_cmd:
                main()
                mock_cmd.assert_called_once()
                args = mock_cmd.call_args[0][0]
                assert args.config == 'rules.yaml'
                assert args.output_dot == 'fsm.dot'