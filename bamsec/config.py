import os
from dotenv import load_dotenv

load_dotenv()

BAMSEC_EMAIL = os.getenv("BAMSEC_EMAIL")
BAMSEC_PASSWORD = os.getenv("BAMSEC_PASSWORD")
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
