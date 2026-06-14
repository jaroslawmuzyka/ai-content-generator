import json
import logging
from services.ai_service import generate_ai_response
from services.job_processor import _replace_variables

logger = logging.getLogger(__name__)

STEP_PURPOSES = {
    "seo_input_analysis": "Analiza intencji wyszukiwania i encji",
    "audience_insight": "Profilowanie odbiorcy i consumer insight",
    "creative_angles": "Unikalne kąty narracyjne z hookami",
    "pas_analysis": "Framework PAS: Problem-Agitacja-Rozwiązanie",
    "aida_analysis": "Framework AIDA: Uwaga-Zainteresowanie-Pożądanie-Akcja",
    "fab_analysis": "Framework FAB: Cechy-Zalety-Korzyści",
    "bab_analysis": "Framework BAB: Przed-Po-Most",
    "benefit_mapping": "Mapa Cecha → Korzyść funkcjonalna → Emocjonalna",
    "seo_outline_expanded": "Struktura nagłówków H2/H3 w HTML",
    "seo_section_writer": "Treść każdej sekcji H2",
    "seo_verification": "Weryfikacja redundancji i spójności",
    "readability_perplexity": "Poprawa czytelności tekstu",
    "humanization": "Usunięcie botowych cech tekstu",
    "attractiveness_optimization": "Wzmocnienie perswazji i CTA",
    "meta_title": "Meta title 40-60 znaków",
    "meta_description": "Meta description 140-160 znaków z CTA",
    "faq": "Sekcja FAQ 3-5 pytań w HTML",
    "html_formatting": "Formatowanie HTML (p, ul, strong)",
    "html_cleanup": "Czyszczenie HTML ze zbędnych tagów",
    "seo_qa": "Ocena SEO w JSON",
    "attractiveness_qa": "Ocena atrakcyjności w JSON",
}

_EVAL_SYS = """Jesteś ekspertem oceny jakości promptów i outputów AI.

Oceniasz output wygenerowany przez model na podstawie promptu i danych wejściowych.
Kryteria (każde 0-2 pkt, max 10):
1. Realizacja celu — czy output robi to, co nakazuje prompt?
2. Konkretność — konkretne informacje vs ogólniki?
3. Jakość językowa — naturalność, brak lania wody?
4. Przydatność — solidna podstawa dla kolejnych kroków?
5. Jasność promptu — czy instrukcje są jednoznaczne?

Bądź bezlitosny. Zawyżone oceny są bezużyteczne.
Zwróć WYŁĄCZNIE poprawny JSON bez komentarzy."""

_EVAL_USER = """Etap: {step_name}
Cel: {purpose}

SYSTEM PROMPT (dostarczony do modelu):
{sys_preview}

USER PROMPT (dostarczony do modelu):
{user_preview}

OUTPUT AI:
{output}

DANE TESTOWE: fraza={main_keyword}, język={language}, typ={content_type}

Zwróć JSON:
{{
  "score": <1-10>,
  "verdict": "<excellent|good|needs_improvement|poor>",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvement_suggestions": ["..."]
}}"""

_IMPROVE_SYS = """Jesteś ekspertem inżynierii promptów dla LLM.
Na podstawie oceny outputu przepiszesz prompt, aby generował lepsze wyniki.

Zasady:
1. Zachowaj strukturę (Rola, Cel, Dane, Proces, Zasady, Zakazy, Format)
2. Usuń niejasne instrukcje — zastąp precyzyjnymi
3. Dodaj przykłady tam gdzie prompt jest abstrakcyjny
4. Wzmocnij Zakazy jeśli model generuje niepożądane treści
5. ZACHOWAJ wszystkie {{zmienne}} bez zmian!

Zwróć WYŁĄCZNIE poprawny JSON."""

_IMPROVE_USER = """Etap: {step_name}

AKTUALNY SYSTEM PROMPT:
{system_prompt}

AKTUALNY USER PROMPT:
{user_prompt}

OCENA: {score}/10 ({verdict})
Słabości: {weaknesses}
Sugestie: {suggestions}

Zwróć JSON:
{{
  "improved_system_prompt": "...",
  "improved_user_prompt": "...(zachowaj wszystkie {{{{zmienne}}}})",
  "changes_made": ["..."],
  "rationale": "..."
}}"""


def run_lab_pipeline(steps, job_data, provider, model, strategy_data=None, progress_cb=None):
    """Uruchamia pipeline na danych testowych bez zapisu do bazy."""
    try:
        import bs4 as _bs4
    except ImportError:
        _bs4 = None

    previous_outputs = {"__strategy": strategy_data or {}}
    dynamic_vars = {
        "knowledge": "", "knowledge_graph": "", "example_headings": "",
        "headings": "", "heading": "", "already_written_part": "",
        "current_step_output": "", "context": "", "final_html": "",
        "breadcrumbs_list": "", "filters_list": "", "category_content": "", "products_content": ""
    }
    results = {}
    last_output = ""

    # === JINA AI SCRAPING DLA PROMPT LAB ===
    import streamlit as st
    from services.campaign_service import get_campaign_by_id
    campaign = get_campaign_by_id(job_data.get("campaign_id")) if job_data.get("campaign_id") else None
    jina_api_key = st.secrets.get("JINA_API_KEY") if hasattr(st, "secrets") else None

    if job_data.get("url") and jina_api_key and campaign:
        import time
        from services.jina_service import fetch_jina_content, extract_products_with_ai

        if progress_cb: progress_cb("Scrapowanie Jina AI...", 0, len(steps))

        bread_t = campaign.get("jina_breadcrumbs_target")
        filt_t = campaign.get("jina_filters_target")
        cat_t = campaign.get("jina_category_target")
        cat_r = campaign.get("jina_category_remove")
        ret = campaign.get("jina_retain_images", "none")
        eng = campaign.get("jina_engine", "cf-browser-rendering")

        if bread_t:
            if progress_cb: progress_cb("Scrapowanie Okruszków...", 0, len(steps))
            b_c, _ = fetch_jina_content(job_data["url"], jina_api_key, eng, bread_t, None, ret)
            if b_c: dynamic_vars["breadcrumbs_list"] = b_c
            
        if filt_t:
            if progress_cb: progress_cb("Scrapowanie Filtrów...", 0, len(steps))
            time.sleep(2)
            f_c, _ = fetch_jina_content(job_data["url"], jina_api_key, eng, filt_t, None, ret)
            if f_c: dynamic_vars["filters_list"] = f_c
            
        if cat_t:
            if progress_cb: progress_cb("Scrapowanie Kategorii...", 0, len(steps))
            time.sleep(2)
            cat_c, _ = fetch_jina_content(job_data["url"], jina_api_key, eng, cat_t, cat_r, ret)
            if cat_c: 
                dynamic_vars["category_content"] = cat_c
                if progress_cb: progress_cb("Jina AI: Wyciąganie produktów (AI)...", 0, len(steps))
                prods = extract_products_with_ai(cat_c, provider, model, max_items=100)
                if prods:
                    formatted_prods = [f"Produkt: {p['name']}\nURL: {p['url']}" for p in prods]
                    dynamic_vars["products_content"] = "\n\n".join(formatted_prods)

    # =======================================

    for i, step in enumerate(steps):
        step_key = step["step_key"]
        if progress_cb:
            progress_cb(step.get("step_name", step_key), i, len(steps))

        if not step.get("is_active", True):
            results[step_key] = {"output": "", "skipped": True, "tokens_in": 0, "tokens_out": 0}
            continue

        dynamic_vars["current_step_output"] = last_output
        for ok in ["seo_outline_expanded", "seo_outline_h2_only"]:
            if ok in previous_outputs:
                dynamic_vars["headings"] = previous_outputs[ok]
                break
        dynamic_vars["final_html"] = (
            previous_outputs.get("html_cleanup") or
            previous_outputs.get("html_formatting") or
            previous_outputs.get("attractiveness_optimization") or
            previous_outputs.get("seo_section_writer") or ""
        )

        used_provider = step.get("provider") or provider
        used_model = step.get("model") or model

        # Section writer loop
        if step_key == "seo_section_writer" and dynamic_vars["headings"] and _bs4:
            soup = _bs4.BeautifulSoup(dynamic_vars["headings"], "html.parser")
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")] or [dynamic_vars["headings"]]
            final_text = ""
            tin = tout = 0
            ok_flag = True
            for h2 in h2_tags:
                dynamic_vars["heading"] = h2
                dynamic_vars["already_written_part"] = final_text
                sp = _replace_variables(step["system_prompt"], job_data, previous_outputs, dynamic_vars)
                up = _replace_variables(step["user_prompt"], job_data, previous_outputs, dynamic_vars)
                res = generate_ai_response(provider=used_provider, model=used_model, system_prompt=sp,
                                           user_prompt=up, temperature=step.get("temperature", 0.7),
                                           max_tokens=step.get("max_tokens", 2000))
                if res["success"]:
                    final_text += f"<h2>{h2}</h2>\n{res['text'].strip()}\n\n"
                    tin += res.get("input_tokens", 0)
                    tout += res.get("output_tokens", 0)
                else:
                    results[step_key] = {"output": final_text, "error": res.get("error"), "skipped": False,
                                         "tokens_in": tin, "tokens_out": tout,
                                         "system_prompt_used": sp, "user_prompt_used": up}
                    ok_flag = False
                    break
            if ok_flag:
                previous_outputs[step_key] = final_text.strip()
                last_output = final_text.strip()
                results[step_key] = {"output": final_text.strip(), "skipped": False, "tokens_in": tin, "tokens_out": tout,
                                     "system_prompt_used": sp, "user_prompt_used": up}
            continue
            
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
            
            if not combined_html:
                combined_html = previous_outputs.get("seo_section_writer", dynamic_vars.get("final_html", ""))
                
            dynamic_vars["text_humanize"] = combined_html
            previous_outputs[step_key] = combined_html
            last_output = combined_html
            results[step_key] = {"output": combined_html, "skipped": False, "tokens_in": 0, "tokens_out": 0}
            continue

        if str(used_provider).strip().lower() == "system" and str(used_model).strip().lower() == "local":
            previous_outputs[step_key] = ""
            results[step_key] = {"output": "", "skipped": True, "tokens_in": 0, "tokens_out": 0}
            continue

        sp = _replace_variables(step["system_prompt"], job_data, previous_outputs, dynamic_vars)
        up = _replace_variables(step["user_prompt"], job_data, previous_outputs, dynamic_vars)
        res = generate_ai_response(provider=used_provider, model=used_model, system_prompt=sp,
                                   user_prompt=up, temperature=step.get("temperature", 0.7),
                                   max_tokens=step.get("max_tokens", 1500))
        if res["success"]:
            previous_outputs[step_key] = res["text"]
            last_output = res["text"]
            results[step_key] = {"output": res["text"], "skipped": False,
                                  "tokens_in": res.get("input_tokens", 0), "tokens_out": res.get("output_tokens", 0),
                                  "system_prompt_used": sp, "user_prompt_used": up}
        else:
            results[step_key] = {"output": "", "error": res.get("error", "Błąd AI"), "skipped": False,
                                  "tokens_in": 0, "tokens_out": 0, "system_prompt_used": sp, "user_prompt_used": up}
            last_output = ""

    results["__jina"] = {
        "breadcrumbs": dynamic_vars.get("breadcrumbs_list", ""),
        "filters": dynamic_vars.get("filters_list", ""),
        "category": dynamic_vars.get("category_content", ""),
        "products": dynamic_vars.get("products_content", "")
    }
    return results


def evaluate_step(step_key, step_name, system_prompt_used, user_prompt_used, output_text, job_data, provider, model):
    """Ocenia output kroku. Zwraca dict z oceną."""
    if not (output_text or "").strip():
        return {"score": 0, "verdict": "poor", "strengths": [],
                "weaknesses": ["Brak outputu"], "improvement_suggestions": ["Sprawdź klucze API i konfigurację"]}

    purpose = STEP_PURPOSES.get(step_key, "Nieznany cel etapu")
    sys_pr = system_prompt_used[:5000] + ("..." if len(system_prompt_used) > 5000 else "")
    usr_pr = user_prompt_used[:5000] + ("..." if len(user_prompt_used) > 5000 else "")
    
    prompt = _EVAL_USER.format(
        step_name=step_name, purpose=purpose,
        sys_preview=sys_pr,
        user_preview=usr_pr,
        output=output_text[:30000] + ("..." if len(output_text) > 30000 else ""),
        main_keyword=job_data.get("main_keyword", ""),
        language=job_data.get("language", ""),
        content_type=job_data.get("content_type", "")
    )
    res = generate_ai_response(provider=provider, model=model, system_prompt=_EVAL_SYS,
                               user_prompt=prompt, temperature=0.3, max_tokens=800)
    if not res["success"]:
        return {"score": 0, "verdict": "poor", "strengths": [], "weaknesses": [res.get("error", "Błąd API")],
                "improvement_suggestions": []}
    try:
        text = res["text"]
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"evaluate_step JSON parse error: {e}")
        return {"score": 0, "verdict": "poor", "strengths": [], "weaknesses": ["Błąd parsowania oceny"],
                "improvement_suggestions": []}


def improve_prompt(step_key, step_name, system_prompt, user_prompt, evaluation, provider, model):
    """Proponuje ulepszoną wersję promptu. Zwraca dict z propozycją."""
    prompt = _IMPROVE_USER.format(
        step_name=step_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        score=evaluation.get("score", 0),
        verdict=evaluation.get("verdict", ""),
        weaknesses="; ".join(evaluation.get("weaknesses", [])),
        suggestions="; ".join(evaluation.get("improvement_suggestions", []))
    )
    res = generate_ai_response(provider=provider, model=model, system_prompt=_IMPROVE_SYS,
                               user_prompt=prompt, temperature=0.4, max_tokens=3000)
    if not res["success"]:
        return {"improved_system_prompt": system_prompt, "improved_user_prompt": user_prompt,
                "changes_made": [], "rationale": f"Błąd API: {res.get('error')}"}
    try:
        text = res["text"]
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"improve_prompt JSON parse error: {e}")
        return {"improved_system_prompt": system_prompt, "improved_user_prompt": user_prompt,
                "changes_made": ["Błąd parsowania propozycji"], "rationale": ""}


def _prompts_to_steps(prompts_snap):
    """Konwertuje snapshot promptów z lab na listę kroków dla run_lab_pipeline."""
    steps = []
    for sk, info in prompts_snap.items():
        steps.append({
            "step_key": sk,
            "step_name": info.get("step_name", sk),
            "step_order": info.get("step_order", 999),
            "system_prompt": info["system"],
            "user_prompt": info["user"],
            "is_active": info.get("is_active", True),
            "temperature": info.get("temperature", 0.7),
            "max_tokens": info.get("max_tokens", 1500),
            "provider": info.get("provider"),
            "model": info.get("model"),
        })
    steps.sort(key=lambda s: s["step_order"])
    return steps


def run_auto_loop(initial_steps, job_data, provider, model, strategy_data,
                  n_iterations, min_score_threshold=9, progress_cb=None):
    """
    Uruchamia automatyczną pętlę: test → ocena → ulepszenie → zastosowanie, N razy.
    Zwraca listę iteracji (dict) z pełnymi danymi każdej rundy.
    """
    # Build initial prompts snapshot
    current_prompts = {
        s["step_key"]: {
            "system": s["system_prompt"],
            "user": s["user_prompt"],
            "step_name": s.get("step_name", s["step_key"]),
            "step_order": s.get("step_order", 999),
            "is_active": s.get("is_active", True),
            "temperature": s.get("temperature", 0.7),
            "max_tokens": s.get("max_tokens", 1500),
            "provider": s.get("provider"),
            "model": s.get("model"),
        }
        for s in initial_steps
    }

    all_iterations = []

    for iter_num in range(1, n_iterations + 1):
        iter_result = {
            "number": iter_num,
            "prompts": {k: dict(v) for k, v in current_prompts.items()},
            "outputs": {},
            "evaluations": {},
            "proposals": {},
            "auto": True,
        }

        # ── FAZA 1: Pipeline ──────────────────────────────────────────
        if progress_cb:
            progress_cb(iter_num, n_iterations, "pipeline", None, 0, 0)

        steps_list = _prompts_to_steps(current_prompts)
        total_steps = len(steps_list)

        def pipeline_cb(step_name, idx, total):
            if progress_cb:
                progress_cb(iter_num, n_iterations, "pipeline", step_name, idx, total)

        outputs = run_lab_pipeline(steps_list, job_data, provider, model, strategy_data, pipeline_cb)
        iter_result["outputs"] = outputs

        # ── FAZA 2: Ocena ─────────────────────────────────────────────
        active_keys = [sk for sk, info in current_prompts.items() if info.get("is_active", True)]
        for idx, sk in enumerate(active_keys):
            if progress_cb:
                progress_cb(iter_num, n_iterations, "eval", current_prompts[sk]["step_name"], idx, len(active_keys))
            ev = evaluate_step(
                step_key=sk,
                step_name=current_prompts[sk]["step_name"],
                system_prompt_used=outputs.get(sk, {}).get("system_prompt_used", current_prompts[sk]["system"]),
                user_prompt_used=outputs.get(sk, {}).get("user_prompt_used", current_prompts[sk]["user"]),
                output_text=outputs.get(sk, {}).get("output", ""),
                job_data=job_data,
                provider=provider,
                model=model
            )
            iter_result["evaluations"][sk] = ev

        # ── FAZA 3: Ulepszenie kroków poniżej progu ───────────────────
        steps_to_improve = [
            sk for sk, ev in iter_result["evaluations"].items()
            if ev.get("score", 10) < min_score_threshold
        ]
        for idx, sk in enumerate(steps_to_improve):
            if progress_cb:
                progress_cb(iter_num, n_iterations, "improve", current_prompts[sk]["step_name"], idx, len(steps_to_improve))
            prop = improve_prompt(
                step_key=sk,
                step_name=current_prompts[sk]["step_name"],
                system_prompt=current_prompts[sk]["system"],
                user_prompt=current_prompts[sk]["user"],
                evaluation=iter_result["evaluations"][sk],
                provider=provider,
                model=model
            )
            iter_result["proposals"][sk] = {**prop, "approved": True}

        all_iterations.append(iter_result)

        # ── FAZA 4: Zastosuj ulepszenia jako baza kolejnej iteracji ───
        if iter_num < n_iterations:
            new_prompts = {}
            for sk, info in current_prompts.items():
                prop = iter_result["proposals"].get(sk)
                if prop:
                    new_prompts[sk] = {
                        **info,
                        "system": prop.get("improved_system_prompt", info["system"]),
                        "user": prop.get("improved_user_prompt", info["user"]),
                    }
                else:
                    new_prompts[sk] = dict(info)
            current_prompts = new_prompts

    return all_iterations
