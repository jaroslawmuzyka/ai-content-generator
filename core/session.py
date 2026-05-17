import streamlit as st

def init_session_state():
    """Inicjalizacja wymaganych zmiennych w session_state."""
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False
        
    if "current_operator" not in st.session_state:
        st.session_state["current_operator"] = None
        
    if "active_campaign_id" not in st.session_state:
        st.session_state["active_campaign_id"] = None
        
    if "campaign_view_mode" not in st.session_state:
        st.session_state["campaign_view_mode"] = "list"  # 'list', 'create', 'edit'
        
    if "campaign_edit_id" not in st.session_state:
        st.session_state["campaign_edit_id"] = None
