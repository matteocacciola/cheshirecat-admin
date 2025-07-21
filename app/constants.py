import os
from cheshirecat_python_sdk import Configuration
from dotenv import load_dotenv

load_dotenv(verbose=True)

CLIENT_CONFIGURATION = Configuration(
    host=os.getenv("CHESHIRE_CAT_API_HOST", "localhost").replace("https://", "").replace("http://", ""),
    port=int(os.getenv("CHESHIRE_CAT_API_PORT")),
    auth_key=os.getenv("CHESHIRE_CAT_API_KEY"),
    secure_connection=os.getenv("CHESHIRE_CAT_API_SECURE_CONNECTION", "true").lower() == "true",
)

CHECK_INTERVAL = int(os.getenv("CHESHIRE_CAT_CHECK_INTERVAL", 20))  # seconds
