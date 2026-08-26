import os

# Provider can be 'ollama' or 'openai'
PROVIDER = os.getenv('LLM_PROVIDER', 'ollama').lower()

# Set to disable vision-model calls for image-only pages/slides and embedded
# figures (e.g. if CHAT_MODEL doesn't support vision, or to skip the cost).
ENABLE_VISION = os.getenv('ENABLE_VISION', 'true').lower() not in ('0', 'false', 'no')

if PROVIDER == 'ollama':
    BASE_URL = "http://localhost:11434/v1"
    API_KEY = "ollama"  # Dummy key for Ollama
    CHAT_MODEL = "ornith-1.5:9b"
    EMBEDDING_MODEL = "qwen3-embedding:8b"
else:
    BASE_URL = None  # Use OpenAI default
    API_KEY = os.getenv('OPENAI_API_KEY')
    CHAT_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
