import streamlit as st

def show_error(message: str):
    """Wyświetla standaryzowany komunikat błędu."""
    st.error(message, icon="🚨")

def show_success(message: str):
    """Wyświetla standaryzowany komunikat sukcesu."""
    st.success(message, icon="✅")

def show_info(message: str):
    """Wyświetla standaryzowany komunikat informacyjny."""
    st.info(message, icon="ℹ️")
