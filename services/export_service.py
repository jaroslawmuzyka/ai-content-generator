import pandas as pd
import io
import json
import re
import streamlit as st
from db.supabase_client import get_supabase_client
from bs4 import BeautifulSoup

def sanitize_excel_cell(text, fallback="Brak danych"):
    """Zabezpiecza tekst przed wysypaniem parsera Excela (długość i illegal chars)."""
    if not text:
        return fallback
    text_str = str(text)
    # Usuwamy nielegalne znaki XML (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F)
    text_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text_str)
    # Limit Excela to 32767 znaków w komórce, ucinamy z buforem
    if len(text_str) > 32700:
        return text_str[:32700] + "\n[... OBcięto przez limit Excela ...]"
    return text_str

def get_jobs_for_export(campaign_id=None, status=None, content_type=None, language=None, date_from=None, date_to=None):
    """Pobiera zadania dopasowane do wszystkich filtrów z UI."""
    client = get_supabase_client()
    if not client: return []
    try:
        query = client.table("content_jobs").select("*").order("created_at", desc=True)
        
        if campaign_id and campaign_id != "all": 
            query = query.eq("campaign_id", campaign_id)
        if status and status != "all": 
            query = query.eq("status", status)
        if content_type and content_type != "all": 
            query = query.eq("content_type", content_type)
        if language and language != "all": 
            query = query.eq("language", language)
            
        if date_from:
            query = query.gte("created_at", date_from.isoformat() + "T00:00:00Z")
        if date_to:
            query = query.lte("created_at", date_to.isoformat() + "T23:59:59Z")
            
        return query.execute().data
    except Exception as e:
        st.error(f"Błąd pobierania zadań do eksportu: {str(e)}")
        return []

def get_all_steps_for_jobs(job_ids):
    """Pobiera wszystkie zarejestrowane kroki powiązane z danymi zadaniami (In bulk)."""
    if not job_ids: return []
    client = get_supabase_client()
    if not client: return []
    try:
        # Podział na chunki jeśli tablica idków byłaby ogromna (powyżej 200)
        all_steps = []
        chunk_size = 150
        for i in range(0, len(job_ids), chunk_size):
            chunk = job_ids[i:i + chunk_size]
            res = client.table("content_job_steps").select("*").in_("job_id", chunk).order("step_order").execute()
            all_steps.extend(res.data)
            
        return all_steps
    except Exception as e:
        st.error(f"Błąd pobierania logów kroków: {str(e)}")
        return []

def log_export(campaign_id, operator_name, file_name, filters_dict):
    """Zapisuje ślad rewizyjny po pobraniu danych do tabeli 'exports'."""
    client = get_supabase_client()
    if not client: return False
    
    try:
        data = {
            "campaign_id": campaign_id if campaign_id != "all" else None,
            "operator_name": operator_name,
            "export_type": "xlsx",
            "file_name": file_name,
            "filters_json": filters_dict
        }
        client.table("exports").insert(data).execute()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"log_export error: {e}")
        return False

def get_export_history():
    """Zwraca log pobrań."""
    client = get_supabase_client()
    if not client: return []
    try:
        res = client.table("exports").select("*").order("created_at", desc=True).limit(50).execute()
        return res.data
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_export_history error: {e}")
        return []

def generate_export_xlsx(jobs, steps):
    """
    Formuje kompleksowy skoroszyt z wieloma arkuszami na podstawie surowych danych bazowych.
    Zamraża pierwsze wiersze nagłówkowe (Freeze Panes).
    Zwraca strumień bajtów gotowy do przekazania do przycisku Download.
    """
    final_contents_data = []
    meta_data = []
    faq_data = []
    seo_qa_data = []
    attr_qa_data = []
    errors_data = []
    
    # 1. Pętle transformacji głównego strumienia Jobsów
    for job in jobs:
        # Wyciągnij prawdziwą liczbę znaków bez tagów HTML, jeśli tekst istnieje
        final_len = 0
        if job.get("final_html"):
            final_len = len(BeautifulSoup(job["final_html"], "html.parser").get_text(strip=True, separator=" "))
            
        final_contents_data.append({
            "id": job["id"],
            "campaign_id": job["campaign_id"],
            "content_type": job["content_type"],
            "language": job["language"],
            "locale": job["locale"],
            "url": job["url"],
            "main_keyword": job["main_keyword"],
            "secondary_keywords": job["secondary_keywords"],
            "target_length": job["target_length"],
            "final_length": final_len,
            "final_html": sanitize_excel_cell(job.get("final_html")),
            "status": job["status"],
            "created_at": job["created_at"][:19] if job.get("created_at") else "", # ucinamy timezone w excelu by było ładniej
            "completed_at": job["completed_at"][:19] if job.get("completed_at") else ""
        })
        
        meta_data.append({
            "id": job["id"],
            "main_keyword": job["main_keyword"],
            "meta_title": sanitize_excel_cell(job.get("meta_title")),
            "meta_description": sanitize_excel_cell(job.get("meta_description"))
        })
        
        faq_data.append({
            "id": job["id"],
            "main_keyword": job["main_keyword"],
            "faq_html": sanitize_excel_cell(job.get("faq_html")),
            "faq_json": "" # Przygotowane miejsce na ewentualny eksport stricte obiektowy
        })
        
        seo_qa_data.append({
            "id": job["id"],
            "main_keyword": job["main_keyword"],
            "seo_report_json": sanitize_excel_cell(json.dumps(job.get("seo_report_json"), ensure_ascii=False) if job.get("seo_report_json") else "")
        })
        
        attr_qa_data.append({
            "id": job["id"],
            "main_keyword": job["main_keyword"],
            "attractiveness_score": job.get("attractiveness_score", ""),
            "attractiveness_report_json": sanitize_excel_cell(json.dumps(job.get("attractiveness_report_json"), ensure_ascii=False) if job.get("attractiveness_report_json") else "")
        })
        
        # Jeśli job zgasł na błędzie, spróbuj przypiąć do tego arkusza "Error" winowajcę
        if job["status"] == "failed" and job.get("error_message"):
            failed_step = next((s["step_name"] for s in steps if s["job_id"] == job["id"] and s["status"] == "failed"), "Nieznany krok")
            errors_data.append({
                "job_id": job["id"],
                "main_keyword": job["main_keyword"],
                "status": job["status"],
                "error_message": job["error_message"],
                "failed_step": failed_step
            })

    # 2. Mapowanie kroków
    steps_data = []
    for s in steps:
        steps_data.append({
            "job_id": s["job_id"],
            "step_order": s["step_order"],
            "step_key": s["step_key"],
            "step_name": s["step_name"],
            "status": s["status"],
            "provider": s["provider"],
            "model": s["model"],
            "input_tokens": s.get("input_tokens", 0),
            "output_tokens": s.get("output_tokens", 0),
            "estimated_cost": "", # Na etapie MVP puste
            "output_text": sanitize_excel_cell(str(s.get("output_text", ""))),
            "error_message": sanitize_excel_cell(str(s.get("error_message", "")))
        })
        
    # Konstrukcja mechanizmów pandas
    df_final = pd.DataFrame(final_contents_data)
    df_meta = pd.DataFrame(meta_data)
    df_faq = pd.DataFrame(faq_data)
    df_seo = pd.DataFrame(seo_qa_data)
    df_attr = pd.DataFrame(attr_qa_data)
    df_steps = pd.DataFrame(steps_data)
    df_errors = pd.DataFrame(errors_data)
    
    # Zapis i powrót jako obiekt binarny zoptymalizowany dla biblioteki openpyxl
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dfs = {
            "final_contents": df_final,
            "meta": df_meta,
            "faq": df_faq,
            "seo_qa": df_seo,
            "attractiveness_qa": df_attr,
            "steps": df_steps,
            "errors": df_errors
        }
        
        for sheet_name, df in dfs.items():
            # W Excelu arkusz może mieć max 31 znaków nazwy
            safe_name = sheet_name[:31]
            df.to_excel(writer, index=False, sheet_name=safe_name)
            
            # Zamrażanie pierwszego rzędu z nazwami nagłówków (ułatwia przeglądanie)
            worksheet = writer.sheets[safe_name]
            worksheet.freeze_panes = "A2"
            
    return output.getvalue()
