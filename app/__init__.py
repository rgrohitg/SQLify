from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now your environment variables should be loaded
CUBEJS_API_URL = os.getenv("CUBEJS_API_URL")
CUBEJS_API_TOKEN = os.getenv("CUBEJS_API_TOKEN")