import os

from dotenv import find_dotenv, load_dotenv

from codegen.cli.env.constants import DEFAULT_ENV
from codegen.cli.env.enums import Environment


class GlobalEnv:
    def __init__(self) -> None:
        self.ENV = self._parse_env()
        self._load_dotenv()

        # =====[ DEV ]=====
        self.DEBUG = self._get_env_var("DEBUG")

        # =====[ AUTH ]=====
        self.CODEGEN_USER_ACCESS_TOKEN = self._get_env_var("CODEGEN_USER_ACCESS_TOKEN")

        # =====[ ALGOLIA ]=====
        self.ALGOLIA_SEARCH_KEY = self._get_env_var("ALGOLIA_SEARCH_KEY")

        # =====[ POSTHOG ]=====
        self.POSTHOG_PROJECT_API_KEY = self._get_env_var("POSTHOG_PROJECT_API_KEY")

        # =====[ MODAL ]=====
        self.MODAL_ENVIRONMENT = self._get_env_var("MODAL_ENVIRONMENT")

    def _parse_env(self) -> Environment:
        env_envvar = os.environ.get("ENV")
        if not env_envvar:
            return DEFAULT_ENV
        if env_envvar not in Environment:
            msg = f"Invalid environment: {env_envvar}"
            raise ValueError(msg)
        return Environment(env_envvar)

    def _load_dotenv(self) -> None:
        env_file = find_dotenv(filename=f".env.{self.ENV}")
        # if env specific .env file does not exist, try to load .env
        load_dotenv(env_file or None, override=True)

    def _get_env_var(self, var_name, required: bool = False) -> str:
        if self.ENV == "local":
            return ""

        if value := os.environ.get(var_name):
            return value

        if required:
            msg = f"Environment variable {var_name} is not set with ENV={self.ENV}!"
            raise ValueError(msg)
        return ""

    def __repr__(self) -> str:
        # Returns all env vars in a readable format
        return "\n".join([f"{k}={v}" for k, v in self.__dict__.items()])


# NOTE: load and store envvars once
global_env = GlobalEnv()
