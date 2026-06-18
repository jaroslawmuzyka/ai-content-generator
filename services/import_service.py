import pandas as pd
import io
import streamlit as st
from services.job_repository import create_content_job, create_prompt_snapshots_for_job
from services.prompt_service import get_campaign_prompt_steps
from utils.constants import CONTENT_TYPES, PROVIDERS

EXPECTED_COLUMNS = [
    "content_type", "language", "locale", "url", "is_existing_url",
    "main_keyword", "secondary_keywords", "target_length", 
    "current_content", "additional_notes", "provider", "model", "priority"
]

def generate_template_bytes():
    """Generuje pusty plik Excel z nazwami kolumn i jednym wierszem pokazowym."""
    df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    df.loc[0] = [
        "blog_post", "pl", "pl-PL", "https://example.com/blog/test", "nie",
        "najlepsze kosiarki spalinowe", "kosiarka, poradnik, ogród", "3000",
        "", "Zwróć uwagę na lekki ton. Używaj wypunktowań.", "openai", "gpt-4o", "10"
    ]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Szablon_AI_Content')
    return output.getvalue()

def validate_uploaded_file(file):
    """
    Parsuje plik XLSX, sprawdza poprawność typów i kluczowych wartości.
    Zwraca krotkę: (lista_poprawnych_rekordów, lista_błędów_do_wyswietlenia).
    """
    valid_records = []
    errors_list = []
    
    try:
        df = pd.read_excel(file)
    except Exception as e:
        return [], [{"Wiersz": "N/A", "Słowo (main_keyword)": "-", "Znalezione błędy": f"Krytyczny błąd odczytu pliku: {str(e)[:100]}. Upewnij się, że to format .xlsx"}]
        
    # Walidacja struktury
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        return [], [{"Wiersz": "N/A", "Słowo (main_keyword)": "-", "Znalezione błędy": f"Brakuje niezbędnych kolumn: {', '.join(missing_cols)}. Pobierz szablon by to naprawić."}]
        
    if df.empty:
        return [], [{"Wiersz": "N/A", "Słowo (main_keyword)": "-", "Znalezione błędy": "Plik Excel jest pusty (brak danych poniżej nagłówków)."}]
        
        
    # Pandas NaN -> Python None
    df = df.where(pd.notnull(df), None)
    
    seen_keywords = set()
    
    for idx, row in df.iterrows():
        row_num = idx + 2 # Header to wiersz 1, więc dane zaczynają się od 2
        row_errors = []
        
        main_keyword = str(row.get("main_keyword", "") or "").strip()
        if main_keyword.lower() == "none": main_keyword = ""
            
        content_type = str(row.get("content_type", "") or "").strip()
        language = str(row.get("language", "") or "").strip()
        
        if not main_keyword:
            row_errors.append("Puste pole 'main_keyword' (Wymagane)")
        elif len(main_keyword) > 255:
            row_errors.append(f"Zbyt długie 'main_keyword' (max 255 znaków, ma {len(main_keyword)})")
        elif main_keyword.lower() in seen_keywords:
            row_errors.append(f"Duplikat frazy 'main_keyword' w tym pliku: {main_keyword}")
        else:
            seen_keywords.add(main_keyword.lower())
            
        if not content_type or content_type not in CONTENT_TYPES:
            row_errors.append(f"Zły 'content_type'. Dozwolone: {', '.join(CONTENT_TYPES)}")
            
        if not language or language.lower() == "none":
            row_errors.append("Puste pole 'language' (Wymagane, np. pl, en)")
            
        # Obsługa liczb
        target_length = row.get("target_length")
        if target_length is not None and str(target_length).strip().lower() != "none" and str(target_length).strip() != "":
            try:
                target_length = int(float(target_length))
                if target_length < 0:
                    row_errors.append("target_length musi być większe od zera")
            except Exception as e:
                row_errors.append("target_length nie jest liczbą")
                target_length = None
        else:
            target_length = None
            
        # Boolean parser
        is_existing_str = str(row.get("is_existing_url", "")).strip().lower()
        is_existing = False
        if is_existing_str in ["true", "tak", "1", "yes", "t", "y"]:
            is_existing = True
        elif is_existing_str not in ["false", "nie", "0", "no", "f", "n", "none", "nan", ""]:
            row_errors.append(f"Błędna wartość logiczna w is_existing_url: {is_existing_str}")
            
        # Provider i model
        provider = str(row.get("provider", "") or "").strip().lower()
        if provider and provider != "none":
            if provider not in PROVIDERS:
                row_errors.append(f"Nieznany provider AI: {provider}")
        else:
            provider = None
            
        model = str(row.get("model", "") or "").strip()
        if model == "None" or not model: model = None
            
        priority = row.get("priority")
        if priority is not None and str(priority).strip().lower() != "none" and str(priority).strip() != "":
            try:
                priority = int(float(priority))
            except Exception as e:
                priority = 0
        else:
            priority = 0
            
        # Teksty
        url = str(row.get("url", "") or "").strip()
        if url == "None" or not url: url = None
        
        locale = str(row.get("locale", "") or "").strip()
        if locale == "None" or not locale: locale = language # Ochrona przed brakiem locala
        
        sec_kws = str(row.get("secondary_keywords", "") or "").strip()
        if sec_kws == "None" or not sec_kws: sec_kws = None
        elif len(sec_kws) > 2000:
            row_errors.append(f"Zbyt długie pole secondary_keywords (max 2000 znaków, ma {len(sec_kws)})")
        
        curr_content = str(row.get("current_content", "") or "").strip()
        if curr_content == "None" or not curr_content: curr_content = None
        elif len(curr_content) > 100000:
            row_errors.append(f"Zbyt długie pole current_content (max 100k znaków, ma {len(curr_content)})")
        
        add_notes = str(row.get("additional_notes", "") or "").strip()
        if add_notes == "None" or not add_notes: add_notes = None
        elif len(add_notes) > 5000:
            row_errors.append(f"Zbyt długie pole additional_notes (max 5000 znaków, ma {len(add_notes)})")
        
        # Ostateczny osąd dla wiersza
        if row_errors:
            errors_list.append({
                "Wiersz": row_num,
                "Słowo (main_keyword)": main_keyword if main_keyword else "[Brak]",
                "Znalezione błędy": " | ".join(row_errors)
            })
        else:
            valid_records.append({
                "content_type": content_type,
                "language": language,
                "locale": locale,
                "url": url,
                "is_existing_url": is_existing,
                "main_keyword": main_keyword,
                "secondary_keywords": sec_kws,
                "target_length": target_length,
                "current_content": curr_content,
                "additional_notes": add_notes,
                "provider": provider,
                "model": model,
                "priority": priority
            })
            
    return valid_records, errors_list


def process_import(valid_records, campaign_id, prompt_set_id, status, operator_name, zakres, progress_cb=None):
    """
    Otrzymuje w 100% zwalidowane rekordy i tworzy z nich fizyczne obiekty w bazie danych.
    Kopiuje prompt_snapshots dla uodpornienia zadań na późniejsze zmiany w kampanii.
    Stosuje restrykcje odznaczone w "zakres".
    """
    steps = get_campaign_prompt_steps(prompt_set_id)
    if not steps:
        return False, "Krytyczny Błąd: Wybrany zestaw promptów (szablon AI) nie posiada żadnych kroków do sklonowania."
        
    # Dla importu masowego używamy stanu is_active i aplikujemy nadrzędny "zakres"
    job_step_toggles = {}
    for step in steps:
        chk_val = step["is_active"]
        
        if "Treść na kategorie" not in zakres:
            if step["step_key"] not in ["meta_titles_and_descriptions", "seo_abstract"]:
                chk_val = False
                
        if "Meta Title" not in zakres and "Meta Description" not in zakres:
            if step["step_key"] == "meta_titles_and_descriptions":
                chk_val = False
                
        if "SEO Abstract" not in zakres:
            if step["step_key"] == "seo_abstract":
                chk_val = False
                
        job_step_toggles[step["id"]] = chk_val
    
    success_count = 0
    total = len(valid_records)
    
    for i, rec in enumerate(valid_records):
        # Wzbogacenie o kontekst środowiskowy
        rec["campaign_id"] = campaign_id
        rec["status"] = status
        rec["operator_name"] = operator_name
        
        # Zapis zadania
        job_id = create_content_job(rec)
        if job_id:
            # Zrzut snapshotów i przypięcie ich do zadania
            if create_prompt_snapshots_for_job(job_id, steps, job_step_toggles):
                success_count += 1
                
        # Zmiana UI
        if progress_cb:
            progress_cb(i + 1, total)
            
    return True, f"Pomyślnie utworzono {success_count} zadań z {total} dostarczonych."
