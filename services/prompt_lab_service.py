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

SYSTEM PROMPT (fragment):
{sys_preview}

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
        "current_step_output": "", "context": "", "final_html": ""
    }
    results = {}
    last_output = ""

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
                                         "tokens_in": tin, "tokens_out": tout}
                    ok_flag = False
                    break
            if ok_flag:
                previous_outputs[step_key] = final_text.strip()
                last_output = final_text.strip()
                results[step_key] = {"output": final_text.strip(), "skipped": False, "tokens_in": tin, "tokens_out": tout}
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
                                  "tokens_in": res.get("input_tokens", 0), "tokens_out": res.get("output_tokens", 0)}
        else:
            results[step_key] = {"output": "", "error": res.get("error", "Błąd AI"), "skipped": False,
                                  "tokens_in": 0, "tokens_out": 0}
            last_output = ""

    return results


def evaluate_step(step_key, step_name, system_prompt, output_text, job_data, provider, model):
    """Ocenia output kroku. Zwraca dict z oceną."""
    if not (output_text or "").strip():
        return {"score": 0, "verdict": "poor", "strengths": [],
                "weaknesses": ["Brak outputu"], "improvement_suggestions": ["Sprawdź klucze API i konfigurację"]}

    purpose = STEP_PURPOSES.get(step_key, "Nieznany cel etapu")
    prompt = _EVAL_USER.format(
        step_name=step_name, purpose=purpose,
        sys_preview=system_prompt[:600] + ("..." if len(system_prompt) > 600 else ""),
        output=output_text[:2000] + ("..." if len(output_text) > 2000 else ""),
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
