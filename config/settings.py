import streamlit as st

def check_secrets():
    """Sprawdza, czy wszystkie wymagane sekrety są skonfigurowane."""
    # Obecnie wymagamy tylko APP_PASSWORD, docelowo będą też klucze supabase i AI
    required_secrets = ["APP_PASSWORD"]
    
    missing = []
    for secret in required_secrets:
        if secret not in st.secrets:
            missing.append(secret)
            
    return missing
