import streamlit as st
from db.supabase_client import get_supabase_client

def get_campaigns(status_filter="active"):
    """
    Pobiera listę kampanii z bazy.
    status_filter: 'active', 'archived', 'all'
    """
    client = get_supabase_client()
    if not client:
        return []
        
    try:
        query = client.table("campaigns").select("*").order("created_at", desc=True)
        if status_filter != "all":
            query = query.eq("status", status_filter)
            
        result = query.execute()
        return result.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania kampanii z bazy: {str(e)}")
        return []

def get_campaign_by_id(campaign_id):
    """Zwraca pojedynczą kampanię na podstawie ID."""
    client = get_supabase_client()
    if not client:
        return None
        
    try:
        result = client.table("campaigns").select("*").eq("id", campaign_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Błąd podczas pobierania szczegółów kampanii: {str(e)}")
        return None

def create_campaign(data):
    """Tworzy nową kampanię w bazie."""
    client = get_supabase_client()
    if not client:
        return None
        
    try:
        result = client.table("campaigns").insert(data).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Błąd podczas tworzenia kampanii: {str(e)}")
        return None

def update_campaign(campaign_id, data):
    """Aktualizuje istniejącą kampanię."""
    client = get_supabase_client()
    if not client:
        return None
        
    try:
        result = client.table("campaigns").update(data).eq("id", campaign_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Błąd podczas aktualizacji kampanii: {str(e)}")
        return None

def archive_campaign(campaign_id):
    """Archiwizuje kampanię (zmiana statusu)."""
    return update_campaign(campaign_id, {"status": "archived"})
