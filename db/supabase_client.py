import streamlit as st
from supabase import create_client, Client
from typing import Optional

import logging
from postgrest.exceptions import APIError

logger = logging.getLogger("ai_content_generator.db")

# Cacheowanie klienta, aby uniknąć wielokrotnego zestawiania połączeń przy każdym przerysowaniu UI
@st.cache_resource
def get_supabase_client() -> Optional[Client]:
    """
    Zwraca zainicjalizowanego klienta Supabase.
    Pobiera zmienne SUPABASE_URL i SUPABASE_KEY z st.secrets.
    Zwraca None, jeśli zmienne nie są dostępne lub niekompletne.
    """
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
        # Odrzucamy puste stringi i None
        if not url or not key:
            logger.error("Brak poprawnych kluczy Supabase w środowisku.")
            return None
            
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Błąd inicjalizacji Supabase: {str(e)}")
        return None

def check_supabase_connection() -> tuple[bool, str]:
    """
    Służy do diagnozowania połączenia z bazą.
    Zwraca tuplę: (Czy działa, "Komunikat")
    """
    supabase = get_supabase_client()
    
    if not supabase:
        return False, "Brak poprawnej konfiguracji SUPABASE_URL lub SUPABASE_KEY w pliku .streamlit/secrets.toml."
        
    try:
        # Lekkiego zapytanie testowe, żeby upewnić się, że klucze są autentyczne
        # Możemy odpytać dowolną tabelę, np. 'operators'
        supabase.table("operators").select("id").limit(1).execute()
        return True, "Połączenie z Supabase działa poprawnie!"
    except APIError as e:
        error_msg = str(e)
        logger.error(f"Błąd API Supabase podczas weryfikacji połączenia: {error_msg}")
        return False, f"Błąd uprawnień/API Supabase: {error_msg}"
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Nieznany błąd podczas łączenia z bazą: {error_msg}")
        return False, f"Błąd połączenia z bazą (lub brak tabel): {error_msg}"
