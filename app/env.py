import os


def get_supported_env_variables():
    return {
        "CHESHIRE_CAT_API_HOST": "localhost",
        "CHESHIRE_CAT_API_PORT": "1865",
        "CHESHIRE_CAT_API_KEY": None,
        "CHESHIRE_CAT_API_SECURE_CONNECTION": "false",
        "CHESHIRE_CAT_INTRO_MESSAGE": None,
        "CHESHIRE_CAT_CHECK_INTERVAL": "20",
        "CHESHIRE_CAT_JWT_EXPIRE_MINUTES": str(60 * 24),  # JWT expires after 1 day
        "CHESHIRE_CAT_ENVIRONMENT": "prod",
    }


def get_env(name):
    """Utility to get an environment variable value. To be used only for supported Cat envs.
    - covers default supported variables and their default value
    - automagically handles legacy env variables missing the prefix "CCAT_"
    """
    cat_default_env_variables = get_supported_env_variables()

    default = None
    if name in cat_default_env_variables:
        default = cat_default_env_variables[name]

    return os.getenv(name, default)


def get_env_bool(name):
    return get_env(name) in ("1", "true")
