import streamlit as st
from db.supabase_client import get_supabase_client
from datetime import datetime, timezone

def get_dashboard_metrics():
    """Zwraca metryki ze zoptymalizowanym obciążeniem zapytań Supabase."""
    client = get_supabase_client()
    if not client: return None
    
    try:
        camps = client.table("campaigns").select("id", count="exact").eq("status", "active").execute()
        active_camps = camps.count if camps.count is not None else 0
        
        # Pobieramy same statusy by nie ciągnąć ciężkich JSONów/HTMLów, co jest najszybszym rozwiązaniem w Supabase bez procedur RPC
        jobs_res = client.table("content_jobs").select("status").execute()
        
        counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0, "needs_review": 0, "interrupted": 0, "draft": 0}
        if jobs_res.data:
            for j in jobs_res.data:
                s = j["status"]
                if s in counts:
                    counts[s] += 1
                else:
                    counts[s] = 1
                    
        return {
            "active_campaigns": active_camps,
            "jobs_counts": counts
        }
    except Exception as e:
        st.error(f"Błąd ładowania metryk: {str(e)}")
        return None

def get_recent_jobs(limit=10):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("content_jobs").select("id, created_at, campaign_id, main_keyword, status, operator_name").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_recent_jobs error: {e}")
        return []

def get_recent_errors(limit=5):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("content_jobs").select("id, created_at, main_keyword, error_message").eq("status", "failed").order("updated_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_recent_errors error: {e}")
        return []

def mark_interrupted_jobs():
    """Wykrywa zawieszone sesje (processing > 60 min bez aktualizacji) i oznacza je jako przerwane."""
    client = get_supabase_client()
    if not client: return 0
    try:
        res = client.table("content_jobs").select("id, updated_at").eq("status", "processing").execute()
        if not res.data: return 0
        
        now_utc = datetime.now(timezone.utc)
        to_interrupt = []
        
        for j in res.data:
            updated_str = j.get("updated_at")
            if updated_str:
                try:
                    dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    diff = now_utc - dt
                    if diff.total_seconds() > 3600:
                        to_interrupt.append(j["id"])
                except Exception as e:
                    pass
                    
        if to_interrupt:
            client.table("content_jobs").update({
                "status": "interrupted", 
                "error_message": "Zadanie zawieszone (Timeout >60 minut bez akcji). Przerwano automatycznie."
            }).in_("id", to_interrupt).execute()
            
        return len(to_interrupt)
    except Exception as e:
        return 0

def restore_interrupted_jobs():
    client = get_supabase_client()
    if not client: return 0
    try:
        res = client.table("content_jobs").update({"status": "queued", "error_message": None}).eq("status", "interrupted").execute()
        return len(res.data) if res.data else 0
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"restore_interrupted_jobs error: {e}")
        return 0
