from dotenv import load_dotenv

from app.env import get_env


load_dotenv(verbose=True)

CHECK_INTERVAL = int(get_env("CHESHIRE_CAT_CHECK_INTERVAL"))  # seconds
INTRO_MESSAGE = get_env("CHESHIRE_CAT_INTRO_MESSAGE")
