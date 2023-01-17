import json
import re


class Config:
    TOKEN_REGEX = r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}'
    WEBHOOK_REGEX = r'https://discord.com\/api\/webhooks\/([^\/]+)\/([^\/]+)'

    def __init__(self) -> None:
        with open('config.json', 'r', encoding='utf-8') as f:
            self.__data = json.loads(f.read())
        self.prefix: str = self.__data["prefix"] if 'prefix' in self.__data else ">"
        self.token: str = self.__data["token"] if 'token' in self.__data else ""
        self.default_language: str = self.__data["default_language"] if 'default_language' in self.__data else "en"

        self.valid_keys = [key for key, _ in self.to_json().items()]

    def __save_config(self) -> None:
        with open('config.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.to_json(), sort_keys=False, indent=2))

    def set(self, key: str, value: any) -> None:
        if not self.__valid_key(key): raise KeyError(f"Invalid Key only valid keys are {self.valid_keys.__str__()}")
        self.__validate(key, value)
        exec(f"self.{key} = type(self.{key})(value)")
        self.__data[key] = value
        self.__save_config()

    def __valid_key(self, key: str):
        return key in self.valid_keys

    def __validate(self, key: str, value: any) -> None:
        match key:
            case 'token':
                if not re.match(self.TOKEN_REGEX, str(value)): raise Exception("Invalid Discord Token")
            case _:
                return

    def to_json(self):
        return {
            "prefix": self.prefix,
            "token": self.token,
            "default_language": self.default_language,
        }