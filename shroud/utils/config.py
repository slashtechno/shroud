from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="SHROUD",
    load_dotenv=True,
    settings_files=["settings.toml", ".secrets.toml"],
    merge_enabled=True,
)
settings.validators.register(
        validators=[
        Validator(
            "slack_bot_token",
            must_exist=True,
            condition=lambda x: x.startswith("xoxb-"),
            messages={"condition": "Must start with 'xoxb-'"},
        ),
        Validator(
            "slack_app_token",
            must_exist=True,
            condition=lambda x: x.startswith("xapp-"),
            messages={"condition": "Must start with 'xapp-'"},
        ),
    ],
)

settings.validators.validate()
