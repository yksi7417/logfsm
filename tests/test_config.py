import pytest
import tempfile
import os
import yaml
from logfsm.config import Config


class TestConfig:
    """Test the Config class."""
    
    def test_config_creation_empty(self):
        """Test creating a Config with empty configuration."""
        cfg = Config({})
        
        assert cfg.signal_rules == []
        assert cfg.entity_id_field == "order_id"
        assert cfg.start_state == "START"
        assert cfg.unknown_state == "UNKNOWN"
    
    def test_config_creation_with_values(self):
        """Test creating a Config with custom values."""
        cfg_data = {
            "signal_rules": [
                {"name": "TEST_RULE", "regex": "test.*", "state": "TEST_STATE"}
            ],
            "entity_id_field": "transaction_id",
            "start_state": "INIT",
            "unknown_state": "FAILED"
        }
        
        cfg = Config(cfg_data)
        
        assert len(cfg.signal_rules) == 1
        assert cfg.signal_rules[0]["name"] == "TEST_RULE"
        assert cfg.entity_id_field == "transaction_id"
        assert cfg.start_state == "INIT"
        assert cfg.unknown_state == "FAILED"
    
    def test_config_creation_partial_values(self):
        """Test creating a Config with some values, others should use defaults."""
        cfg_data = {
            "signal_rules": [
                {"name": "RULE1", "regex": "rule1.*", "state": "STATE1"}
            ],
            "entity_id_field": "custom_id"
        }
        
        cfg = Config(cfg_data)
        
        assert len(cfg.signal_rules) == 1
        assert cfg.entity_id_field == "custom_id"
        assert cfg.start_state == "START"  # default
        assert cfg.unknown_state == "UNKNOWN"  # default
    
    def test_config_load_from_file(self):
        """Test loading Config from a YAML file."""
        yaml_content = """
signal_rules:
  - name: NEW_ORDER
    regex: "(?i)newordersingle.*clordid=(?P<order_id>[A-Z0-9]+)"
    state: "NEW_REQUESTED"
  - name: ACK_NEW
    regex: "(?i)executionreport.*exectype=0.*clordid=(?P<order_id>[A-Z0-9]+)"
    state: "ACKED_NEW"

entity_id_field: "order_id"
start_state: "START"
unknown_state: "UNKNOWN"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            cfg = Config.load(temp_path)
            
            assert len(cfg.signal_rules) == 2
            assert cfg.signal_rules[0]["name"] == "NEW_ORDER"
            assert cfg.signal_rules[1]["name"] == "ACK_NEW"
            assert cfg.entity_id_field == "order_id"
            assert cfg.start_state == "START"
            assert cfg.unknown_state == "UNKNOWN"
        finally:
            os.unlink(temp_path)
    
    def test_config_save_to_file(self):
        """Test saving Config to a YAML file."""
        cfg_data = {
            "signal_rules": [
                {"name": "TEST_RULE", "regex": "test.*", "state": "TEST_STATE"}
            ],
            "entity_id_field": "test_id",
            "start_state": "BEGIN",
            "unknown_state": "ERROR"
        }
        
        cfg = Config(cfg_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            cfg.save(temp_path)
            
            # Load the saved file and verify contents
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_data = yaml.safe_load(f)
            
            assert len(saved_data["signal_rules"]) == 1
            assert saved_data["signal_rules"][0]["name"] == "TEST_RULE"
            assert saved_data["entity_id_field"] == "test_id"
            assert saved_data["start_state"] == "BEGIN"
            assert saved_data["unknown_state"] == "ERROR"
        finally:
            os.unlink(temp_path)
    
    def test_config_round_trip(self):
        """Test loading and saving config preserves data."""
        original_data = {
            "signal_rules": [
                {"name": "RULE1", "regex": "pattern1", "state": "STATE1"},
                {"name": "RULE2", "regex": "pattern2", "state": "STATE2"}
            ],
            "entity_id_field": "order_id",
            "start_state": "START",
            "unknown_state": "UNKNOWN"
        }
        
        cfg = Config(original_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            # Save and reload
            cfg.save(temp_path)
            cfg_reloaded = Config.load(temp_path)
            
            assert cfg_reloaded.signal_rules == original_data["signal_rules"]
            assert cfg_reloaded.entity_id_field == original_data["entity_id_field"]
            assert cfg_reloaded.start_state == original_data["start_state"]
            assert cfg_reloaded.unknown_state == original_data["unknown_state"]
        finally:
            os.unlink(temp_path)
    
    def test_config_load_nonexistent_file(self):
        """Test loading Config from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config.load("nonexistent_file.yaml")
    
    def test_config_load_invalid_yaml(self):
        """Test loading Config from invalid YAML raises yaml.YAMLError."""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(invalid_yaml)
            temp_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                Config.load(temp_path)
        finally:
            os.unlink(temp_path)