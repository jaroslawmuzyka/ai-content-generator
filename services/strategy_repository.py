import streamlit as st
from db.supabase_client import get_supabase_client

def get_campaign_strategy(campaign_id):
    client = get_supabase_client()
    if not client: return None
    try:
        res = client.table("campaign_content_strategy").select("*").eq("campaign_id", campaign_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_campaign_strategy error: {e}")
        return None

def save_campaign_strategy(campaign_id, data):
    client = get_supabase_client()
    if not client: return False
    try:
        existing = get_campaign_strategy(campaign_id)
        if existing:
            client.table("campaign_content_strategy").update(data).eq("campaign_id", campaign_id).execute()
        else:
            data["campaign_id"] = campaign_id
            client.table("campaign_content_strategy").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu strategii: {str(e)}")
        return False
