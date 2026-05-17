import streamlit as st
from supabase import create_client, Client
from typing import Optional

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
            return None
            
        return create_client(url, key)
    except Exception as e:
        print(f"Błąd inicjalizacji Supabase: {e}")
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
    except Exception as e:
        error_msg = str(e)
        return False, f"Błąd połączenia z bazą (lub brak tabel): {error_msg}"
