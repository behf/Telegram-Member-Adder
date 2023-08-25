import json
from typing import List, Dict, Any


class Config:

    def __init__(self, filename="src/config.json"):
        self.filename = filename

    def read(self) -> Dict[str, Any]:
        # Open file and parse config values
        # Return config dict
        config = {}
        try:
            with open(self.filename) as f:
                config = json.load(f)
        except FileNotFoundError:
            self.write(config=config)
        finally:
            return config

    def write(self, config: Dict[str, Any]) -> None:
        with open(self.filename, 'w') as f:
            json.dump(config, f, indent=4)

    @property
    def api_credentials(self) -> List[Dict]:
        return self.read().get("API_CREDENTIALS", [])

    @property
    def phone_numbers(self) -> List[str]:
        return self.read().get("PHONE_NUMBERS", [])

    @property
    def source_group(self) -> int:
        return self.read().get("SOURCE_GROUP_ID", None)

    @property
    def target_group(self) -> int:
        return self.read().get("TARGET_GROUP_ID", None)

    @property
    def adding_method(self) -> str:
        return self.read().get("ADDING_METHOD", "username")

    @api_credentials.setter
    def api_credentials(self, value: List[Dict[str, str]]) -> None:
        config = self.read()
        config["API_CREDENTIALS"] = value
        self.write(config)

    @phone_numbers.setter
    def phone_numbers(self, value: List[str]) -> None:
        config = self.read()
        config["PHONE_NUMBERS"] = value
        self.write(config)

    @source_group.setter
    def source_group(self, value: int) -> None:
        config = self.read()
        config["SOURCE_GROUP_ID"] = value
        self.write(config)

    @target_group.setter
    def target_group(self, value: int) -> None:
        config = self.read()
        config["TARGET_GROUP_ID"] = value
        self.write(config)

    @adding_method.setter
    def adding_method(self, value) -> None:
        config = self.read()
        config["ADDING_METHOD"] = value
        self.write(config)
