import yaml

class Config:
    def __init__(self, cfg):
        self.signal_rules = cfg.get("signal_rules", [])
        self.entity_id_field = cfg.get("entity_id_field", "order_id")
        self.start_state = cfg.get("start_state", "START")
        self.unknown_state = cfg.get("unknown_state", "UNKNOWN")

    @staticmethod
    def load(path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return Config(data)

    def save(self, path: str):
        data = {
            "signal_rules": self.signal_rules,
            "entity_id_field": self.entity_id_field,
            "start_state": self.start_state,
            "unknown_state": self.unknown_state,
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
