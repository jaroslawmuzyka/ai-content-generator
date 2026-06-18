import os
import toml
import logging

logger = logging.getLogger("ai_content_generator.secrets")

_secrets_cache = None

def get_secret(key: str) -> str:
    """
    Pobiera sekret z .streamlit/secrets.toml.
    Działa niezależnie od kontekstu Streamlit (bezpieczne dla wątków w tle).
    """
    global _secrets_cache
    
    # Najpierw próbujemy standardowo przez st.secrets (działa w głównym wątku)
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val is not None:
            return val
    except Exception:
        pass

    # Fallback: czytanie pliku ręcznie (dla wątków, gdy sesja st umrze)
    if _secrets_cache is None:
        try:
            secrets_path = os.path.join(".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, "r", encoding="utf-8") as f:
                    _secrets_cache = toml.load(f)
            else:
                _secrets_cache = {}
        except Exception as e:
            logger.error(f"Nie udało się odczytać secrets.toml: {e}")
            _secrets_cache = {}

    return _secrets_cache.get(key)
