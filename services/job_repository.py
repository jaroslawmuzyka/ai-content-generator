import streamlit as st
from db.supabase_client import get_supabase_client

# -------------------------------------------------------------------------
# WARSTWA BAZY DANYCH DLA ZADAŃ CONTENTOWYCH (CRUD)
# Odizolowana od logiki AI, odpowiedzialna wyłącznie za zapis i odczyt z Supabase
# -------------------------------------------------------------------------

def get_content_jobs(campaign_id=None, status=None, content_type=None, language=None, search_keyword=None):
    client = get_supabase_client()
    if not client: return []
    try:
        query = client.table("content_jobs").select("*").order("created_at", desc=True)
        if campaign_id: query = query.eq("campaign_id", campaign_id)
        if status and status != "all": query = query.eq("status", status)
        if content_type and content_type != "all": query = query.eq("content_type", content_type)
        if language and language != "all": query = query.eq("language", language)
        if search_keyword: query = query.ilike("main_keyword", f"%{search_keyword}%")
        
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Błąd pobierania zadań: {str(e)}")
        return []

def get_next_queued_jobs(limit=1, campaign_id=None):
    """Pobiera kolejne oczekujące zadania z kolejki na podstawie priorytetu."""
    client = get_supabase_client()
    if not client: return []
    try:
        query = client.table("content_jobs").select("*").eq("status", "queued").order("priority", desc=True).order("created_at", desc=False)
        if campaign_id and campaign_id != "all":
            query = query.eq("campaign_id", campaign_id)
        
        if limit is not None:
            query = query.limit(limit)
            
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Błąd pobierania partii zadań: {str(e)}")
        return []

def update_job_status(job_id, status, error_message=None):
    client = get_supabase_client()
    if not client: return False
    data = {"status": status}
    if error_message is not None:
        data["error_message"] = error_message
    try:
        client.table("content_jobs").update(data).eq("id", job_id).execute()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"update_job_status error: {e}")
        return False

def requeue_failed_jobs(campaign_id=None):
    """Przerzuca wszystkie zadania typu failed z powrotem do kolejki queued."""
    client = get_supabase_client()
    if not client: return 0
    try:
        query = client.table("content_jobs").update({"status": "queued", "error_message": None}).eq("status", "failed")
        if campaign_id and campaign_id != "all":
            query = query.eq("campaign_id", campaign_id)
            
        res = query.execute()
        return len(res.data) if res.data else 0
    except Exception as e:
        st.error(f"Błąd podczas ponawiania błędnych zadań: {str(e)}")
        return 0

def get_job_by_id(job_id):
    client = get_supabase_client()
    if not client: return None
    try:
        res = client.table("content_jobs").select("*").eq("id", job_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_job_by_id error: {e}")
        return None

def get_job_snapshots(job_id):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("job_prompt_snapshots").select("*").eq("job_id", job_id).order("step_order").execute()
        return res.data if res.data else []
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_job_snapshots error: {e}")
        return []

def get_job_steps(job_id):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("content_job_steps").select("*").eq("job_id", job_id).order("step_order").execute()
        return res.data if res.data else []
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_job_steps error: {e}")
        return []

def update_job_final_fields(job_id, final_html, meta_title, meta_description, faq_html, seo_abstract=""):
    client = get_supabase_client()
    if not client: return False
    try:
        client.table("content_jobs").update({
            "final_html": final_html,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "seo_abstract": seo_abstract,
            "faq_html": faq_html,
            "updated_at": "now()"
        }).eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu poprawek: {str(e)}")
        return False

def create_content_job(job_data):
    client = get_supabase_client()
    if not client: return None
    try:
        res = client.table("content_jobs").insert(job_data).execute()
        if res.data: return res.data[0]["id"]
        return None
    except Exception as e:
        st.error(f"Błąd zapisu zadania: {str(e)}")
        return None

def create_prompt_snapshots_for_job(job_id, original_steps, job_step_toggles):
    client = get_supabase_client()
    if not client: return False
    try:
        snapshots = []
        for step in original_steps:
            is_active = job_step_toggles.get(step["id"], step["is_active"])
            snapshot_data = {
                "job_id": job_id,
                "step_order": step["step_order"],
                "step_key": step["step_key"],
                "step_name": step["step_name"],
                "system_prompt_snapshot": step["system_prompt"],
                "user_prompt_snapshot": step["user_prompt"],
                "provider": step["provider"],
                "model": step["model"],
                "temperature": step["temperature"],
                "max_tokens": step["max_tokens"],
                "is_active": is_active,
                "stage_group": step.get("stage_group", "seo")
            }
            snapshots.append(snapshot_data)
            
        if snapshots:
            client.table("job_prompt_snapshots").insert(snapshots).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu snapshotów: {str(e)}")
        return False

def duplicate_job(job_id, status="draft"):
    client = get_supabase_client()
    if not client: return None
    
    orig_job = get_job_by_id(job_id)
    if not orig_job: return None
    
    new_job_data = {
        "campaign_id": orig_job["campaign_id"],
        "operator_name": st.session_state.get("current_operator", "unknown"),
        "content_type": orig_job["content_type"],
        "language": orig_job["language"],
        "locale": orig_job["locale"],
        "url": orig_job["url"],
        "is_existing_url": orig_job["is_existing_url"],
        "main_keyword": orig_job["main_keyword"],
        "secondary_keywords": orig_job["secondary_keywords"],
        "target_length": orig_job["target_length"],
        "current_content": orig_job["current_content"],
        "additional_notes": orig_job["additional_notes"],
        "provider": orig_job["provider"],
        "model": orig_job["model"],
        "priority": orig_job["priority"],
        "status": status,
        "generation_mode": orig_job.get("generation_mode", "seo_and_attractiveness"),
        "content_goal": orig_job.get("content_goal"),
        "call_to_action": orig_job.get("call_to_action"),
        "target_audience_override": orig_job.get("target_audience_override"),
        "persona_override": orig_job.get("persona_override"),
        "tone_override": orig_job.get("tone_override")
    }
    
    new_id = create_content_job(new_job_data)
    if not new_id: return None
    
    orig_snapshots = get_job_snapshots(job_id)
    if orig_snapshots:
        new_snapshots = []
        for s in orig_snapshots:
            new_s = s.copy()
            new_s.pop("id", None)
            new_s.pop("created_at", None)
            new_s["job_id"] = new_id
            new_snapshots.append(new_s)
        client.table("job_prompt_snapshots").insert(new_snapshots).execute()
        
    return new_id
