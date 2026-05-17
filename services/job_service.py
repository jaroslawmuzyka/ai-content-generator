import streamlit as st
import json
import re
from datetime import datetime
from db.supabase_client import get_supabase_client
from services.ai_service import generate_ai_response
from services.html_cleaner import clean_html
from services.seo_quality_service import analyze_seo_quality

# -------------------------------------------------------------------------
# CRUD Zadań
# -------------------------------------------------------------------------

def get_campaign_prompt_sets(campaign_id):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("campaign_prompt_sets").select("*").eq("campaign_id", campaign_id).order("created_at").execute()
        return res.data
    except:
        return []

def get_prompt_steps_for_set(set_id):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("campaign_prompt_steps").select("*").eq("campaign_prompt_set_id", set_id).order("step_order").execute()
        return res.data
    except:
        return []

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
        return query.execute().data
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
            
        return query.execute().data
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
    except:
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
    except:
        return None

def get_job_snapshots(job_id):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("job_prompt_snapshots").select("*").eq("job_id", job_id).order("step_order").execute()
        return res.data
    except:
        return []

def get_job_steps(job_id):
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("content_job_steps").select("*").eq("job_id", job_id).order("step_order").execute()
        return res.data
    except:
        return []

def update_job_final_fields(job_id, final_html, meta_title, meta_description, faq_html):
    client = get_supabase_client()
    if not client: return False
    try:
        client.table("content_jobs").update({
            "final_html": final_html,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "faq_html": faq_html,
            "updated_at": "now()"
        }).eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu poprawek: {str(e)}")
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
        "status": status
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
                "is_active": is_active
            }
            snapshots.append(snapshot_data)
            
        if snapshots:
            client.table("job_prompt_snapshots").insert(snapshots).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu snapshotów: {str(e)}")
        return False


# -------------------------------------------------------------------------
# PROCESOR AI (PIPELINE ZADANIA ORAZ PARTII ZADAŃ)
# -------------------------------------------------------------------------

def _replace_variables(prompt_text, job, previous_outputs):
    if not prompt_text:
        return ""
    
    replacements = {
        "{{content_type}}": str(job.get("content_type") or ""),
        "{{language}}": str(job.get("language") or ""),
        "{{locale}}": str(job.get("locale") or ""),
        "{{main_keyword}}": str(job.get("main_keyword") or ""),
        "{{secondary_keywords}}": str(job.get("secondary_keywords") or ""),
        "{{target_length}}": str(job.get("target_length") or ""),
        "{{current_content}}": str(job.get("current_content") or ""),
        "{{additional_notes}}": str(job.get("additional_notes") or ""),
        "{{url}}": str(job.get("url") or ""),
        "{{is_existing_url}}": str(job.get("is_existing_url") or "")
    }
    
    for key, val in replacements.items():
        prompt_text = prompt_text.replace(key, val)
        
    matches = re.findall(r'\{\{previous_steps\.([a-zA-Z0-9_]+)\}\}', prompt_text)
    for step_key in matches:
        output_val = previous_outputs.get(step_key, "")
        if isinstance(output_val, dict):
            output_val = json.dumps(output_val, ensure_ascii=False, indent=2)
        prompt_text = prompt_text.replace(f"{{{{previous_steps.{step_key}}}}}", str(output_val))
        
    direct_aliases = ["outline", "section_plan", "main_content", "faq", "meta_title", "meta_description"]
    for alias in direct_aliases:
        if f"{{{{{alias}}}}}" in prompt_text:
            output_val = previous_outputs.get(alias, "")
            prompt_text = prompt_text.replace(f"{{{{{alias}}}}}", str(output_val))
            
    if "{{previous_steps}}" in prompt_text:
        all_outputs = "\n\n".join([f"--- Wynik etapu: {k} ---\n{v}" for k,v in previous_outputs.items()])
        prompt_text = prompt_text.replace("{{previous_steps}}", all_outputs)
            
    return prompt_text


def process_single_job(job_id, progress_callback=None):
    client = get_supabase_client()
    if not client:
        return False, "Błąd klienta Supabase."
        
    job = get_job_by_id(job_id)
    if not job:
        return False, "Nie znaleziono zadania w bazie."
        
    client.table("content_jobs").update({"status": "processing", "started_at": "now()", "error_message": None}).eq("id", job_id).execute()
    
    steps = get_job_snapshots(job_id)
    if not steps:
        update_job_status(job_id, "failed", "Zadanie nie posiada snapshotów promptów.")
        return False, "Brak przypisanych kroków."
        
    existing_steps_res = client.table("content_job_steps").select("*").eq("job_id", job_id).execute()
    existing_steps = {s["step_key"]: s for s in existing_steps_res.data}
    
    previous_outputs = {}
    total_steps = len(steps)
    
    for i, step in enumerate(steps):
        step_key = step["step_key"]
        
        if progress_callback:
            progress_callback(step["step_name"], i, total_steps)
            
        client.table("content_jobs").update({"current_step_key": step_key}).eq("id", job_id).execute()
        
        if not step["is_active"]:
            if step_key not in existing_steps:
                client.table("content_job_steps").insert({
                    "job_id": job_id, "step_order": step["step_order"],
                    "step_key": step_key, "step_name": step["step_name"],
                    "status": "skipped", "output_text": ""
                }).execute()
            else:
                client.table("content_job_steps").update({"status": "skipped"}).eq("id", existing_steps[step_key]["id"]).execute()
            continue
            
        if step_key in existing_steps and existing_steps[step_key]["status"] == "completed":
            out_text = existing_steps[step_key].get("output_text", "")
            out_json = existing_steps[step_key].get("output_json")
            previous_outputs[step_key] = out_json if out_json else out_text
            continue
            
        sys_prompt = _replace_variables(step["system_prompt_snapshot"], job, previous_outputs)
        usr_prompt = _replace_variables(step["user_prompt_snapshot"], job, previous_outputs)
        
        ai_res = generate_ai_response(
            provider=step["provider"] or job["provider"],
            model=step["model"] or job["model"],
            system_prompt=sys_prompt,
            user_prompt=usr_prompt,
            temperature=step["temperature"],
            max_tokens=step["max_tokens"]
        )
        
        step_record = {
            "job_id": job_id, "step_order": step["step_order"],
            "step_key": step_key, "step_name": step["step_name"],
            "provider": step["provider"] or job["provider"],
            "model": step["model"] or job["model"],
            "system_prompt_used": sys_prompt, "user_prompt_used": usr_prompt,
            "input_tokens": ai_res.get("input_tokens"), "output_tokens": ai_res.get("output_tokens")
        }
        
        if ai_res["success"]:
            step_record["status"] = "completed"
            step_record["output_text"] = ai_res["text"]
            step_record["completed_at"] = "now()"
            
            parsed_json = None
            if step_key == "seo_qa" or step_key.endswith("json"):
                try:
                    json_str = ai_res["text"]
                    if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str: json_str = json_str.split("```")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_str)
                    step_record["output_json"] = parsed_json
                except:
                    pass 
                    
            previous_outputs[step_key] = parsed_json if parsed_json else ai_res["text"]
            
            if step_key in existing_steps:
                client.table("content_job_steps").update(step_record).eq("id", existing_steps[step_key]["id"]).execute()
            else:
                res_ins = client.table("content_job_steps").insert(step_record).execute()
                if res_ins.data:
                    existing_steps[step_key] = res_ins.data[0]
        else:
            step_record["status"] = "failed"
            step_record["error_message"] = ai_res["error"]
            
            if step_key in existing_steps:
                client.table("content_job_steps").update(step_record).eq("id", existing_steps[step_key]["id"]).execute()
            else:
                client.table("content_job_steps").insert(step_record).execute()
                
            error_msg = f"Przerwano na etapie '{step_key}': {ai_res['error']}"
            update_job_status(job_id, "failed", error_msg)
            return False, error_msg
            
    final_fields = {
        "status": "completed",
        "completed_at": "now()",
        "error_message": None,
        "current_step_key": "done"
    }
    
    # Mapowanie outputów
    if "html_cleanup" in previous_outputs: 
        final_fields["final_html"] = previous_outputs["html_cleanup"]
    elif "main_content" in previous_outputs: 
        final_fields["final_html"] = previous_outputs["main_content"]
        
    # Bezpieczne czyszczenie kodu HTML
    if final_fields.get("final_html"):
        final_fields["final_html"] = clean_html(final_fields["final_html"])
        
    if "faq" in previous_outputs: 
        raw_faq = previous_outputs["faq"]
        final_fields["faq_html"] = clean_html(raw_faq) if raw_faq else ""
        
    if "meta_title" in previous_outputs: 
        final_fields["meta_title"] = previous_outputs["meta_title"]
        
    if "meta_description" in previous_outputs: 
        final_fields["meta_description"] = previous_outputs["meta_description"]
        
    # Przetwarzanie QA (Analiza Regułowa i połączenie z QA od LLM)
    qa_report = analyze_seo_quality(job, final_fields.get("final_html", ""))
    
    if "seo_qa" in previous_outputs:
        final_fields["seo_report_json"] = {
            "ai_report": previous_outputs["seo_qa"] if isinstance(previous_outputs["seo_qa"], dict) else {"raw": previous_outputs["seo_qa"]},
            "rules_qa": qa_report
        }
    else:
        final_fields["seo_report_json"] = {"rules_qa": qa_report}
        
    client.table("content_jobs").update(final_fields).eq("id", job_id).execute()
    
    if progress_callback:
        progress_callback("Zakończono", total_steps, total_steps)
        
    return True, "Zadanie wygenerowane pomyślnie!"


def process_job_batch(limit, campaign_id=None, batch_progress_cb=None, job_progress_cb=None):
    """
    Uruchamia pętlę procesu dla N zadań (limit).
    Dzięki temu pojedyncze błędy nie zatrzymują całej partii.
    """
    jobs = get_next_queued_jobs(limit, campaign_id)
    if not jobs:
        return 0, 0, 0
        
    success_count = 0
    error_count = 0
    total = len(jobs)
    
    for i, job in enumerate(jobs):
        if batch_progress_cb:
            batch_progress_cb(i, total, job, success_count, error_count)
            
        try:
            success, msg = process_single_job(job["id"], job_progress_cb)
            if success:
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            update_job_status(job["id"], "failed", f"Krytyczny błąd wygenerowany podczas trwania partii (Batches): {str(e)}")
            
    if batch_progress_cb:
        batch_progress_cb(total, total, None, success_count, error_count)
        
    return total, success_count, error_count
