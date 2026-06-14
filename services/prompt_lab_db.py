import json
from db.supabase_client import get_supabase_client

def save_lab_session(session_id, campaign_id, campaign_prompt_set_id, session_data):
    client = get_supabase_client()
    if not client: return None
    
    payload = {
        "campaign_id": campaign_id,
        "campaign_prompt_set_id": campaign_prompt_set_id,
        "session_data": session_data,
        "updated_at": "now()"
    }
    
    if session_id:
        res = client.table("prompt_lab_sessions").update(payload).eq("id", session_id).execute()
        if res.data:
            return session_id
    
    # Insert new
    try:
        res = client.table("prompt_lab_sessions").insert(payload).execute()
        if res.data:
            return res.data[0]["id"]
    except Exception:
        pass
    return None

def load_lab_sessions(campaign_id=None):
    client = get_supabase_client()
    if not client: return []
    query = client.table("prompt_lab_sessions").select("id, campaign_id, updated_at, session_data").order("updated_at", desc=True)
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    return query.execute().data
