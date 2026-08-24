from openai import OpenAI
from . import config

# Create a single shared client based on the configuration
client = OpenAI(
    base_url=config.BASE_URL,
    api_key=config.API_KEY
)
