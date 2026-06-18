import json
import re
from db.supabase_client import get_supabase_client
from services.ai_service import generate_ai_response
from services.html_cleaner import clean_html
from services.seo_quality_service import analyze_seo_quality
from services.job_repository import (
    get_job_by_id,
    update_job_status,
    get_job_snapshots,
    get_next_queued_jobs
)
from services.strategy_repository import get_campaign_strategy
from services.attractiveness_quality_service import analyze_attractiveness_quality

# -------------------------------------------------------------------------
# PROCESOR AI (PIPELINE ZADANIA ORAZ PARTII ZADAŃ)
# Odizolowana od zapytań CRUD warstwa czysto decyzyjna/algorytmiczna
# -------------------------------------------------------------------------

# Maksymalna długość już napisanej części przekazywana do promptu (w znakach).
# Ogranicza koszty API i ryzyko przekroczenia okna kontekstowego.
_MAX_ALREADY_WRITTEN_CHARS = 3000


def _strip_html_tags(text: str) -> str:
    """Usuwa tagi HTML z tekstu — używane do czyszczenia meta title / description."""
    if not text:
        return ""
    cleaned = re.sub(r'<[^>]+>', '', text)
    return cleaned.strip()


def _strip_markdown_blocks(text: str) -> str:
    """Usuwa bloki ```html...``` i ``` ``` z odpowiedzi modelu."""
    if not text:
        return ""
    text = re.sub(r'```[a-zA-Z]*\s*', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()


def _replace_variables(prompt_text, job, previous_outputs, dynamic_vars=None):
    if not prompt_text:
        return ""

    if not dynamic_vars:
        dynamic_vars = {}

    # Obcinamy already_written_part do max N znaków (z tyłu), by nie przeciążać okna kontekstowego
    already_written_raw = str(dynamic_vars.get("already_written_part", ""))
    if len(already_written_raw) > _MAX_ALREADY_WRITTEN_CHARS:
        already_written_raw = "[...poprzednie sekcje obcięte...]\n" + already_written_raw[-_MAX_ALREADY_WRITTEN_CHARS:]

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
        "{{is_existing_url}}": str(job.get("is_existing_url") or ""),
        "{{knowledge}}": str(dynamic_vars.get("knowledge", "")),
        "{{knowledge_graph}}": str(dynamic_vars.get("knowledge_graph", "")),
        "{{example_headings}}": str(dynamic_vars.get("example_headings", "")),
        "{{headings}}": str(dynamic_vars.get("headings", "")),
        "{{heading}}": str(dynamic_vars.get("heading", "")),
        "{{already_written_part}}": already_written_raw,
        "{{current_step_output}}": str(dynamic_vars.get("current_step_output", "")),
        "{{context}}": str(dynamic_vars.get("context", "")),
        "{{text_humanize}}": str(dynamic_vars.get("text_humanize", "")),
        "{{breadcrumbs_list}}": str(dynamic_vars.get("breadcrumbs_list", "")),
        "{{filters_list}}": str(dynamic_vars.get("filters_list", "")),
        "{{products_content}}": str(dynamic_vars.get("products_content", "")),
        # Wstrzykiwanie final_html do etapów QA
        "{{final_html}}": str(dynamic_vars.get("final_html", ""))
    }

    strategy = previous_outputs.get("__strategy", {})
    replacements.update({
        "{{brand_description}}": str(strategy.get("brand_description") or ""),
        "{{target_audience}}": str(job.get("target_audience_override") or strategy.get("target_audience") or ""),
        "{{persona}}": str(job.get("persona_override") or strategy.get("persona") or ""),
        "{{consumer_insight}}": str(strategy.get("consumer_insight") or ""),
        "{{customer_language}}": str(strategy.get("customer_language") or ""),
        "{{main_pain_points}}": str(strategy.get("main_pain_points") or ""),
        "{{main_desires}}": str(strategy.get("main_desires") or ""),
        "{{decision_triggers}}": str(strategy.get("decision_triggers") or ""),
        "{{brand_tone}}": str(job.get("tone_override") or strategy.get("brand_tone") or ""),
        "{{brand_archetype}}": str(strategy.get("brand_archetype") or ""),
        "{{forbidden_phrases}}": str(strategy.get("forbidden_phrases") or ""),
        "{{required_phrases}}": str(strategy.get("required_phrases") or ""),
        "{{value_proposition}}": str(strategy.get("value_proposition") or ""),
        "{{proof_points}}": str(strategy.get("proof_points") or ""),
        "{{content_goal}}": str(job.get("content_goal") or strategy.get("content_goal") or ""),
        "{{call_to_action}}": str(job.get("call_to_action") or strategy.get("call_to_action") or "")
    })

    for key, val in replacements.items():
        prompt_text = prompt_text.replace(key, val)

    # Dynamiczne podstawianie {{previous_steps.NAZWA_KROKU}}
    matches = re.findall(r'\{\{previous_steps\.([a-zA-Z0-9_]+)\}\}', prompt_text)
    for step_key in matches:
        output_val = previous_outputs.get(step_key, "")
        if isinstance(output_val, dict):
            output_val = json.dumps(output_val, ensure_ascii=False, indent=2)
        prompt_text = prompt_text.replace(f"{{{{previous_steps.{step_key}}}}}", str(output_val))

    # Skrócone aliasy dla najważniejszych kroków
    direct_aliases = ["outline", "section_plan", "main_content", "faq", "meta_title", "meta_description"]
    for alias in direct_aliases:
        if f"{{{{{alias}}}}}" in prompt_text:
            output_val = previous_outputs.get(alias, "")
            prompt_text = prompt_text.replace(f"{{{{{alias}}}}}", str(output_val))

    # {{previous_steps}} — dump wszystkich kroków
    if "{{previous_steps}}" in prompt_text:
        all_outputs = "\n\n".join([
            f"--- Wynik etapu: {k} ---\n{v}"
            for k, v in previous_outputs.items()
            if k != "__strategy"
        ])
        prompt_text = prompt_text.replace("{{previous_steps}}", all_outputs)

    return prompt_text


def process_single_job(job_id, progress_callback=None):
    client = get_supabase_client()
    if not client:
        return False, "Nie udało się połączyć z bazą danych. Sprawdź ustawienia Supabase w zakładce Ustawienia."

    job = get_job_by_id(job_id)
    if not job:
        return False, "Nie znaleziono zadania w bazie danych."

    client.table("content_jobs").update({
        "status": "processing",
        "started_at": "now()",
        "error_message": None
    }).eq("id", job_id).execute()

    steps = get_job_snapshots(job_id)
    if not steps:
        update_job_status(job_id, "failed", "Zadanie nie posiada snapshotów promptów. Usuń i utwórz zadanie ponownie.")
        return False, "Brak przypisanych kroków AI do zadania."

    existing_steps_res = client.table("content_job_steps").select("*").eq("job_id", job_id).execute()
    existing_steps = {s["step_key"]: s for s in existing_steps_res.data}

    strategy_data = get_campaign_strategy(job["campaign_id"])
    previous_outputs = {"__strategy": strategy_data or {}}
    total_steps = len(steps)

    import urllib.parse
    domain_name = ""
    if job.get("url"):
        parsed = urllib.parse.urlparse(job["url"])
        domain_name = parsed.netloc.replace("www.", "")

    loc_map = {"pl-PL": "polski", "en-US": "angielski", "en-GB": "angielski", "de-DE": "niemiecki", "cs-CZ": "czeski", "sk-SK": "słowacki"}
    lang_val = loc_map.get(job.get("locale") or "pl-PL", "polski")

    dynamic_vars = {
        "knowledge": "",
        "knowledge_graph": "",
        "example_headings": "",
        "headings": "",
        "heading": "",
        "already_written_part": "",
        "current_step_output": "",
        "context": "",
        "final_html": "",
        "category_content": "",
        "products_content": "",
        "domain": domain_name,
        "domain_name": domain_name,
        "language": lang_val,
        "domain_description": "", # Puste, chyba że potrzebne, zostawiam miejsce
        "breadcrumbs_list": "",
        "filters_list": ""
    }

    last_output = ""

    # === JINA AI SCRAPING ===
    # Pobieranie konfiguracji kampanii do scrapowania
    import streamlit as st
    from services.campaign_service import get_campaign_by_id
    campaign = get_campaign_by_id(job["campaign_id"])
    jina_api_key = st.secrets.get("JINA_API_KEY") if hasattr(st, "secrets") else None
    
    if job.get("url") and jina_api_key and campaign:
        import time
        from services.jina_service import fetch_jina_content, extract_product_links_with_ai
        
        if progress_callback:
            progress_callback("Scrapowanie Kategorii przez Jina AI...", 0, total_steps)
            
        # -------------------------------------------------------
        # Pobieranie danych z Jina AI dla kampanii
        # -------------------------------------------------------
        dynamic_vars["breadcrumbs_list"] = ""
        dynamic_vars["filters_list"] = ""
        dynamic_vars["category_content"] = ""
        dynamic_vars["products_content"] = ""

        bread_t = campaign.get("jina_breadcrumbs_target")
        filt_t = campaign.get("jina_filters_target")
        cat_t = campaign.get("jina_category_target")
        cat_r = campaign.get("jina_category_remove")
        ret = campaign.get("jina_retain_images", "none")
        eng = campaign.get("jina_engine", "cf-browser-rendering")

        def _save_jina_step(job_id, step_order, step_key, step_name, content, error_msg=None):
            status = "completed" if content else "failed"
            out = content if content else f"❌ Brak danych z JINA.\nBłąd: {error_msg}"
            payload = {
                "job_id": job_id, "step_order": step_order, "step_key": step_key, "step_name": step_name,
                "status": status, "output_text": out, "provider": "jina", "model": "reader", "completed_at": "now()"
            }
            if step_key in existing_steps:
                client.table("content_job_steps").update(payload).eq("id", existing_steps[step_key]["id"]).execute()
            else:
                client.table("content_job_steps").insert(payload).execute()

        if bread_t:
            if progress_callback: progress_callback("Scrapowanie Okruszków...", 0, total_steps)
            b_c, b_err = fetch_jina_content(job["url"], jina_api_key, eng, bread_t, None, ret)
            if b_c: dynamic_vars["breadcrumbs_list"] = b_c
            _save_jina_step(job_id, 1, "jina_breadcrumbs", "Scrapowanie Okruszków (JINA)", b_c, b_err)
            if b_err:
                client.table("content_jobs").update({"status": "failed", "error_message": f"Błąd Jina (Okruszki): {b_err}"}).eq("id", job_id).execute()
                return False, f"Przerwano: Jina AI zwróciła błąd dla Okruszków: {b_err}"
            
        if filt_t:
            if progress_callback: progress_callback("Scrapowanie Filtrów...", 0, total_steps)
            time.sleep(3)
            f_c, f_err = fetch_jina_content(job["url"], jina_api_key, eng, filt_t, None, ret)
            if f_c: dynamic_vars["filters_list"] = f_c
            _save_jina_step(job_id, 2, "jina_filters", "Scrapowanie Filtrów (JINA)", f_c, f_err)
            if f_err:
                client.table("content_jobs").update({"status": "failed", "error_message": f"Błąd Jina (Filtry): {f_err}"}).eq("id", job_id).execute()
                return False, f"Przerwano: Jina AI zwróciła błąd dla Filtrów: {f_err}"
            
        time.sleep(3)
        cat_content, cat_err = fetch_jina_content(job["url"], jina_api_key, eng, cat_t, cat_r, ret)
        _save_jina_step(job_id, 3, "jina_category", "Scrapowanie Kategorii (JINA)", cat_content, cat_err)
        if cat_err:
            client.table("content_jobs").update({"status": "failed", "error_message": f"Błąd Jina (Kategoria): {cat_err}"}).eq("id", job_id).execute()
            return False, f"Przerwano: Jina AI zwróciła błąd dla Kategorii: {cat_err}"
        
        if cat_content:
            dynamic_vars["category_content"] = cat_content
            
            provider = job.get("provider") or "openai"
            model = job.get("model") or "gpt-4o-mini"
            from services.jina_service import extract_products_with_ai
            
            if progress_callback:
                progress_callback("Jina AI: Wyciąganie nazw produktów (AI)...", 0, total_steps)
                
            products = extract_products_with_ai(cat_content, provider, model, max_items=100)
            if products:
                formatted_products = [f"Produkt: {p['name']}\nURL: {p['url']}" for p in products]
                dynamic_vars["products_content"] = "\n\n".join(formatted_products)
                _save_jina_step(job_id, 4, "jina_extract_names", "Wyciąganie nazw i URL produktów z Kategorii (AI)", dynamic_vars["products_content"])
            else:
                _save_jina_step(job_id, 4, "jina_extract_names", "Wyciąganie nazw i URL produktów z Kategorii (AI)", None, "Brak produktów")
                
            # [ZAKOMENTOWANY STARY KOD - SCRAPOWANIE PODSTRON PRODUKTÓW]
            # from services.jina_service import extract_product_links_with_ai
            # links = extract_product_links_with_ai(cat_content, provider, model, max_links=50)
            # if links:
            #     _save_jina_step(job_id, 4, "jina_extract_links", "Wyciąganie linków produktów z Kategorii (AI)", "\n".join(links))
            # prods_text = []
            # prods_err = []
            # for idx, link in enumerate(links):
            #     if progress_callback: progress_callback(f"Scrapowanie Produktu {idx+1}/{len(links)}...", 0, total_steps)
            #     p_text, p_err = fetch_jina_content(link, jina_api_key, eng, prod_t, prod_r, ret)
            #     if p_text: prods_text.append(f"--- Produkt: {link} ---\n{p_text}")
            #     elif p_err: prods_err.append(f"Produkt {link}: {p_err}")
            #     time.sleep(1)
            # if prods_text:
            #     dynamic_vars["products_content"] = "\n\n".join(prods_text)
            # err_msg = "\n".join(prods_err) if prods_err else None
            # _save_jina_step(job_id, 5, "jina_products", "Scrapowanie zawartości wszystkich produktów (JINA)", dynamic_vars["products_content"] if prods_text else None, err_msg)
            # [KONIEC ZAKOMENTOWANEGO KODU]
    # ========================

    for i, step in enumerate(steps):
        step_key = step["step_key"]

        if progress_callback:
            progress_callback(step["step_name"], i, total_steps)

        client.table("content_jobs").update({"current_step_key": step_key}).eq("id", job_id).execute()

        # Pomiń wyłączone kroki
        if not step["is_active"]:
            if step_key not in existing_steps:
                client.table("content_job_steps").insert({
                    "job_id": job_id, "step_order": step["step_order"],
                    "step_key": step_key, "step_name": step["step_name"],
                    "status": "skipped", "output_text": ""
                }).execute()
            else:
                client.table("content_job_steps").update({"status": "skipped"}).eq(
                    "id", existing_steps[step_key]["id"]
                ).execute()
            continue

        # Wznowienie — jeśli krok już był ukończony, użyj jego outputu
        if step_key in existing_steps and existing_steps[step_key]["status"] == "completed":
            out_text = existing_steps[step_key].get("output_text", "")
            out_json = existing_steps[step_key].get("output_json")
            previous_outputs[step_key] = out_json if out_json else out_text
            last_output = out_text
            continue

        # Aktualizacja zmiennych kontekstowych przed każdym krokiem
        dynamic_vars["current_step_output"] = last_output

        # Ustalenie nagłówków z poprzednich etapów outline
        if "seo_outline_expanded" in previous_outputs:
            dynamic_vars["headings"] = previous_outputs["seo_outline_expanded"]
        elif "seo_outline_h2_only" in previous_outputs:
            dynamic_vars["headings"] = previous_outputs["seo_outline_h2_only"]
        elif "seo_outline_questions" in previous_outputs:
            dynamic_vars["headings"] = previous_outputs["seo_outline_questions"]

        # Wstrzykujemy aktualny final_html dla etapów QA
        # Priorytety: html_cleanup > html_formatting > attractiveness_optimization > seo_section_writer > main_content
        dynamic_vars["final_html"] = (
            previous_outputs.get("html_cleanup") or
            previous_outputs.get("html_formatting") or
            previous_outputs.get("attractiveness_optimization") or
            previous_outputs.get("seo_section_writer") or
            previous_outputs.get("main_content") or
            ""
        )

        # -------------------------------------------------------
        # SPECJALNE ZACHOWANIE: Łączenie kroków 12 i 13 przed Stuffing
        # -------------------------------------------------------
        if step_key == "stuffing":
            import json
            part1_key = next((s["step_key"] for s in steps if "First part" in s["step_name"]), None)
            part2_key = next((s["step_key"] for s in steps if "Continue part" in s["step_name"]), None)
            
            part1_str = previous_outputs.get(part1_key, "") if part1_key else ""
            part2_str = previous_outputs.get(part2_key, "") if part2_key else ""
            
            combined_html = ""
            for p_str in [part1_str, part2_str]:
                if isinstance(p_str, str) and p_str.strip():
                    try:
                        # Może być osadzone w blokach markdown
                        if "```json" in p_str:
                            p_str = p_str.split("```json")[1].split("```")[0].strip()
                        elif "```" in p_str:
                            p_str = p_str.split("```")[1].strip()
                            
                        arr = json.loads(p_str)
                        if isinstance(arr, list):
                            for item in arr:
                                h_name = item.get("heading_name", "")
                                h_tag = item.get("tag", "h2").lower()
                                content = item.get("Content", item.get("content", ""))
                                if h_name and content:
                                    combined_html += f"<{h_tag}>{h_name}</{h_tag}>\n<p>{content}</p>\n\n"
                    except Exception as e:
                        pass
            
            dynamic_vars["text_humanize"] = combined_html
            
            client.table("content_job_steps").insert({
                "job_id": job_id, "step_order": step["step_order"], "step_key": step_key,
                "step_name": step["step_name"], "status": "completed",
                "output_text": combined_html,
                "provider": "system", "model": "local", "completed_at": "now()"
            }).execute()
            previous_outputs[step_key] = combined_html
            continue

        # -------------------------------------------------------
        # PĘTLA dla seo_section_writer — pisze po jednym H2
        # -------------------------------------------------------
        if step_key == "seo_section_writer" and dynamic_vars["headings"]:
            import bs4
            soup = bs4.BeautifulSoup(dynamic_vars["headings"], "html.parser")
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
            if not h2_tags:
                h2_tags = [dynamic_vars["headings"]]

            written_sections = []
            final_text = ""
            total_in = 0
            total_out = 0

            for h_idx, h2 in enumerate(h2_tags):
                dynamic_vars["heading"] = h2
                dynamic_vars["already_written_part"] = final_text

                sys_prompt = _replace_variables(step["system_prompt_snapshot"], job, previous_outputs, dynamic_vars)
                usr_prompt = _replace_variables(step["user_prompt_snapshot"], job, previous_outputs, dynamic_vars)

                ai_res = generate_ai_response(
                    provider=step["provider"] or job["provider"],
                    model=step["model"] or job["model"],
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    temperature=step["temperature"],
                    max_tokens=step["max_tokens"]
                )

                if ai_res["success"]:
                    clean_res = ai_res["text"].strip()
                    # Model czasem ignoruje zakaz i dodaje H2 — usuwamy je
                    if "<h2>" in clean_res.lower():
                        soup_res = bs4.BeautifulSoup(clean_res, "html.parser")
                        for h2_tag in soup_res.find_all("h2"):
                            h2_tag.extract()
                        clean_res = str(soup_res).strip()

                    final_text += f"<h2>{h2}</h2>\n{clean_res}\n\n"
                    total_in += ai_res.get("input_tokens", 0)
                    total_out += ai_res.get("output_tokens", 0)
                else:
                    error_msg = f"Przerwano etap '{step_key}' (nagłówek: {h2}): {ai_res['error']}"
                    update_job_status(job_id, "failed", error_msg)
                    return False, error_msg

            step_record = {
                "job_id": job_id, "step_order": step["step_order"],
                "step_key": step_key, "step_name": step["step_name"],
                "provider": step["provider"] or job["provider"],
                "model": step["model"] or job["model"],
                "system_prompt_used": sys_prompt, "user_prompt_used": usr_prompt,  # zapisuje tylko ostatni prompt
                "input_tokens": total_in, "output_tokens": total_out,
                "status": "completed",
                "output_text": final_text.strip(),
                "completed_at": "now()"
            }

            previous_outputs[step_key] = final_text.strip()
            last_output = final_text.strip()

            if step_key in existing_steps:
                client.table("content_job_steps").update(step_record).eq("id", existing_steps[step_key]["id"]).execute()
            else:
                res_ins = client.table("content_job_steps").insert(step_record).execute()
                if res_ins.data:
                    existing_steps[step_key] = res_ins.data[0]
            continue

        # -------------------------------------------------------
        # Zwykłe (pojedyncze) wywołanie etapu
        # -------------------------------------------------------
        sys_prompt = _replace_variables(step["system_prompt_snapshot"], job, previous_outputs, dynamic_vars)
        usr_prompt = _replace_variables(step["user_prompt_snapshot"], job, previous_outputs, dynamic_vars)

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
            raw_text = ai_res["text"]

            # Usuń potencjalne markdown code blocks z wyników HTML
            if step.get("output_type") == "html":
                raw_text = _strip_markdown_blocks(raw_text)

            step_record["status"] = "completed"
            step_record["output_text"] = raw_text
            step_record["completed_at"] = "now()"

            # Parsowanie JSON dla etapów o typie json lub znanych kluczach
            parsed_json = None
            is_json_step = (
                step.get("output_type") == "json" or
                step_key in ["seo_qa", "attractiveness_qa"]
            )
            if is_json_step:
                try:
                    json_str = raw_text
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_str)
                    step_record["output_json"] = parsed_json
                except Exception as json_err:
                    # Zapisz warning ale kontynuuj — nie przerywaj zadania przez nievalidny JSON
                    step_record["error_message"] = (
                        f"[WARNING] JSON parse error: {str(json_err)[:200]}. "
                        f"Raw output zapisany w output_text."
                    )
                    parsed_json = None

            previous_outputs[step_key] = parsed_json if parsed_json else raw_text
            last_output = raw_text

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

            error_msg = f"Etap '{step_key}' zakończył się błędem: {ai_res['error']}"
            update_job_status(job_id, "failed", error_msg)
            return False, error_msg

    # -------------------------------------------------------
    # SKŁADANIE FINALU
    # -------------------------------------------------------
    final_fields = {
        "status": "completed",
        "completed_at": "now()",
        "error_message": None,
        "current_step_key": "done"
    }

    # Mapowanie final_html z kolejności priorytetów
    if "html_cleanup" in previous_outputs:
        final_fields["final_html"] = previous_outputs["html_cleanup"]
    elif "formatting" in previous_outputs:
        final_fields["final_html"] = previous_outputs["formatting"]
    elif "html_formatting" in previous_outputs:
        final_fields["final_html"] = previous_outputs["html_formatting"]
    elif "attractiveness_optimization" in previous_outputs:
        final_fields["final_html"] = previous_outputs["attractiveness_optimization"]
    elif "seo_section_writer" in previous_outputs:
        final_fields["final_html"] = previous_outputs["seo_section_writer"]
    elif "main_content" in previous_outputs:
        final_fields["final_html"] = previous_outputs["main_content"]

    # Czyszczenie finalnego HTML
    if final_fields.get("final_html"):
        html_warnings = []
        original_html = final_fields["final_html"]
        
        # 1. Usuń markdown code blocks (```html ... ```)
        if "```" in original_html:
            html_warnings.append("Wykryto i usunięto bloki markdown (code fences) z kodu HTML.")
        final_fields["final_html"] = _strip_markdown_blocks(original_html)
        
        # 2. Wyczyść przez bs4
        from services.html_cleaner import validate_clean_html
        val_report = validate_clean_html(final_fields["final_html"])
        if val_report.get("contains_forbidden_tags") or val_report.get("contains_forbidden_attrs"):
            html_warnings.append(f"Usunięto niedozwolone tagi: {val_report.get('forbidden_tags_list')} lub atrybuty: {val_report.get('forbidden_attrs_list')}.")
            
        final_fields["final_html"] = clean_html(final_fields["final_html"])
        
        if html_warnings:
            existing_err = final_fields.get("error_message") or ""
            final_fields["error_message"] = existing_err + "\n[HTML WARNING] " + " ".join(html_warnings)
            final_fields["error_message"] = final_fields["error_message"].strip()

    # FAQ — osobne pole
    if "faq" in previous_outputs:
        raw_faq = previous_outputs["faq"]
        if raw_faq:
            raw_faq = _strip_markdown_blocks(raw_faq)
        final_fields["faq_html"] = clean_html(raw_faq) if raw_faq else ""

    # Meta title i description
    meta_key = next((s["step_key"] for s in steps if "Meta titles" in s.get("step_name", "")), "meta_titles_and_descriptions")
    
    out_meta = previous_outputs.get(meta_key)
    if isinstance(out_meta, str):
        import json
        try:
            out_meta = json.loads(_strip_markdown_blocks(out_meta))
        except:
            pass
            
    if isinstance(out_meta, dict):
        final_fields["meta_title"] = str(out_meta.get("title1", "")).strip()
        final_fields["meta_description"] = str(out_meta.get("metaDescription1", "")).strip()
    else:
        final_fields["meta_title"] = ""
        final_fields["meta_description"] = ""

    # SEO Abstract
    abs_key = next((s["step_key"] for s in steps if "SEO Abstract" in s.get("step_name", "")), "seo_abstract")
    out_abs = previous_outputs.get(abs_key)
    if isinstance(out_abs, str):
        import json
        try:
            out_abs = json.loads(_strip_markdown_blocks(out_abs))
        except:
            pass
            
    if isinstance(out_abs, dict):
        final_fields["seo_abstract"] = str(out_abs.get("seoAbstract", "")).strip()
    else:
        final_fields["seo_abstract"] = ""

    # -------------------------------------------------------
    # QA Regułowe (bez LLM) — pełna analiza
    # -------------------------------------------------------
    qa_report = analyze_seo_quality(
        job,
        final_fields.get("final_html", ""),
        faq_html=final_fields.get("faq_html", ""),
        meta_title=final_fields.get("meta_title", ""),
        meta_description=final_fields.get("meta_description", "")
    )

    if "seo_qa" in previous_outputs:
        final_fields["seo_report_json"] = {
            "ai_report": (
                previous_outputs["seo_qa"]
                if isinstance(previous_outputs["seo_qa"], dict)
                else {"raw": previous_outputs["seo_qa"]}
            ),
            "rules_qa": qa_report
        }
    else:
        final_fields["seo_report_json"] = {"rules_qa": qa_report}

    # QA Atrakcyjności
    attr_qa = previous_outputs.get("attractiveness_qa")
    rules_attr = analyze_attractiveness_quality(job, final_fields.get("final_html", ""), strategy_data)

    if attr_qa and isinstance(attr_qa, dict):
        final_fields["attractiveness_score"] = attr_qa.get("overall_score", 0)
        final_fields["attractiveness_report_json"] = {
            "ai_report": attr_qa,
            "rules_qa": rules_attr
        }
    elif attr_qa:
        final_fields["attractiveness_report_json"] = {
            "ai_report": {"raw": attr_qa},
            "rules_qa": rules_attr
        }
    else:
        final_fields["attractiveness_report_json"] = {
            "rules_qa": rules_attr
        }

    client.table("content_jobs").update(final_fields).eq("id", job_id).execute()

    if progress_callback:
        progress_callback("Zakończono", total_steps, total_steps)

    return True, "Zadanie wygenerowane pomyślnie!"


def process_job_batch(limit, campaign_id=None, job_ids=None, batch_progress_cb=None, job_progress_cb=None):
    """
    Uruchamia pętlę procesu dla N zadań (limit) lub po określonych ID.
    Dzięki temu pojedyncze błędy nie zatrzymują całej partii.
    """
    if job_ids:
        from services.job_repository import get_jobs_by_ids
        jobs = get_jobs_by_ids(job_ids)
    else:
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
            update_job_status(
                job["id"], "failed",
                f"Krytyczny błąd podczas przetwarzania partii: {str(e)}"
            )

    if batch_progress_cb:
        batch_progress_cb(total, total, None, success_count, error_count)

    return total, success_count, error_count
