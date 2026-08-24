import tiktoken
from . import config

def count_tokens(text: str, model_name: str = None) -> int:
    """
    Count tokens in a string. Uses tiktoken for OpenAI models and
    a generic approximation for others.
    """
    if config.PROVIDER == 'openai':
        try:
            # Use the provided model name or the default config one
            target_model = model_name if model_name else config.CHAT_MODEL
            encoding = tiktoken.encoding_for_model(target_model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback if model name is not recognized by tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
    else:
        # For local LLMs, a common approximation is 1 token approx 4 characters
        # or we can use a simple split for a very rough estimate.
        # Since we aren't using a specific local tokenizer here,
        # we'll use a reasonable heuristic: words * 1.3
        return len(text.split()) * 2 # conservative estimate

def get_encoding(encoding_name: str = None):
    """
    Returns a tiktoken encoding if the provider is openai.
    Returns a dummy object for other providers to avoid crashes.
    """
    if config.PROVIDER == 'openai':
        return tiktoken.get_encoding(encoding_name or "cl100k_base")

    # Dummy encoding object for non-openai providers
    class DummyEncoding:
        def encode(self, text):
            return [0] * (len(text.split()) * 2)
        def decode(self, tokens):
            return "dummy decoded text"

    return DummyEncoding()
