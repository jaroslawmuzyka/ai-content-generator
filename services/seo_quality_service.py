from bs4 import BeautifulSoup
from services.html_cleaner import validate_clean_html
import re

# Progi ostrzeżeń dla długości tekstu (% odchylenia od target_length)
_TOO_SHORT_THRESHOLD = 0.5   # < 50% target = za krótki
_TOO_LONG_THRESHOLD = 1.5    # > 150% target = za długi

# Optymalne długości meta pól (znaki)
_META_TITLE_MIN = 40
_META_TITLE_MAX = 65
_META_DESC_MIN = 120
_META_DESC_MAX = 165


def _count_text_chars(html: str) -> int:
    """Zwraca liczbę znaków czystego tekstu (bez HTML)."""
    if not html:
        return 0
    soup = BeautifulSoup(html, "html.parser")
    return len(soup.get_text(separator=" ", strip=True))


def _detect_duplicate_headings(html: str) -> list:
    """Zwraca listę zduplikowanych nagłówków H2."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    h2_texts = [h.get_text(strip=True).lower() for h in soup.find_all("h2")]
    seen = set()
    duplicates = []
    for text in h2_texts:
        if text in seen:
            duplicates.append(text)
        seen.add(text)
    return duplicates


def _detect_faq_repeating_headings(faq_html: str, main_html: str) -> list:
    """Sprawdza, czy pytania FAQ nie duplikują dosłownie nagłówków głównego tekstu."""
    if not faq_html or not main_html:
        return []
    soup_faq = BeautifulSoup(faq_html, "html.parser")
    soup_main = BeautifulSoup(main_html, "html.parser")

    faq_questions = {h.get_text(strip=True).lower() for h in soup_faq.find_all(["h2", "h3", "strong", "b"])}
    main_headings = {h.get_text(strip=True).lower() for h in soup_main.find_all(["h2", "h3"])}

    return list(faq_questions & main_headings)


def _detect_repeated_sentences(text: str, min_length: int = 60) -> list:
    """Wykrywa powtarzające się zdania dłuższe niż min_length znaków."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen = {}
    repeated = []
    for s in sentences:
        s_clean = s.strip().lower()
        if len(s_clean) >= min_length:
            if s_clean in seen:
                repeated.append(s.strip()[:100])
            else:
                seen[s_clean] = True
    return repeated


def analyze_seo_quality(job: dict, final_html: str, faq_html: str = "", meta_title: str = "", meta_description: str = "") -> dict:
    """
    Algorytmiczna weryfikacja wygenerowanej treści zgodnie ze zleceniem.
    Nie używa LLM — działa lokalnie z pomocą BeautifulSoup i parsera tekstowego.
    """
    report = {
        # Podstawowe pola
        "is_empty": False,
        "is_markdown": False,
        "char_count": 0,
        "target_length": job.get("target_length") or 0,
        "length_diff": 0,
        "length_percent_diff": None,
        "too_short_warning": False,
        "too_long_warning": False,

        # Frazy
        "main_keyword": job.get("main_keyword") or "",
        "main_keyword_count": 0,
        "secondary_keywords_used": [],
        "secondary_keywords_missing": [],

        # Struktura HTML
        "has_h1": False,
        "h2_count": 0,
        "duplicate_headings": [],

        # HTML cleanliness
        "contains_forbidden_tags": False,
        "contains_forbidden_attrs": False,
        "forbidden_tags_list": [],
        "forbidden_attrs_list": [],

        # Redundancja
        "repeated_sentences": [],

        # FAQ
        "faq_repeating_headings": [],

        # Meta
        "meta_title_length": 0,
        "meta_title_ok": None,
        "meta_description_length": 0,
        "meta_description_ok": None,

        # Ogólne
        "warnings": []
    }

    if not final_html or not final_html.strip():
        report["is_empty"] = True
        report["warnings"].append("Finalny HTML jest pusty!")
        return report

    # Markdown heurystyka
    if "##" in final_html or "**" in final_html or ("[" in final_html and "](" in final_html):
        report["is_markdown"] = True
        report["warnings"].append("Wykryto znaczniki Markdown w HTML — model zwrócił niepoprawny format.")

    soup = BeautifulSoup(final_html, "html.parser")
    text_only = soup.get_text(separator=" ", strip=True)
    report["char_count"] = len(text_only)

    # Długość i odchylenie
    target = report["target_length"]
    if target > 0:
        report["length_diff"] = report["char_count"] - target
        pct = report["char_count"] / target
        report["length_percent_diff"] = round((pct - 1) * 100, 1)

        if pct < _TOO_SHORT_THRESHOLD:
            report["too_short_warning"] = True
            report["warnings"].append(f"Tekst jest zbyt krótki: {report['char_count']} znaków zamiast {target} (< 50% docelowej długości).")
        elif pct > _TOO_LONG_THRESHOLD:
            report["too_long_warning"] = True
            report["warnings"].append(f"Tekst jest zbyt długi: {report['char_count']} znaków zamiast {target} (> 150% docelowej długości).")

    # Fraza główna
    main_kw = report["main_keyword"].lower()
    if main_kw:
        count = text_only.lower().count(main_kw)
        report["main_keyword_count"] = count
        if count == 0:
            report["warnings"].append(f"Fraza główna '{main_kw}' nie pojawia się w tekście!")

    # Frazy poboczne
    sec_kws = job.get("secondary_keywords")
    if sec_kws:
        kws_list = [k.strip().lower() for k in sec_kws.split(",") if k.strip()]
        for kw in kws_list:
            if kw in text_only.lower():
                report["secondary_keywords_used"].append(kw)
            else:
                report["secondary_keywords_missing"].append(kw)

    # Struktura nagłówków
    report["has_h1"] = len(soup.find_all("h1")) > 0
    report["h2_count"] = len(soup.find_all("h2"))

    # Duplikaty nagłówków
    report["duplicate_headings"] = _detect_duplicate_headings(final_html)
    if report["duplicate_headings"]:
        report["warnings"].append(f"Wykryto zduplikowane nagłówki H2: {report['duplicate_headings']}")

    # Powtarzające się zdania
    report["repeated_sentences"] = _detect_repeated_sentences(text_only)
    if report["repeated_sentences"]:
        report["warnings"].append(f"Wykryto powtarzające się zdania ({len(report['repeated_sentences'])} wystąpień).")

    # FAQ kontra nagłówki główne
    if faq_html:
        report["faq_repeating_headings"] = _detect_faq_repeating_headings(faq_html, final_html)
        if report["faq_repeating_headings"]:
            report["warnings"].append(f"FAQ powtarza dokładnie nagłówki z tekstu głównego: {report['faq_repeating_headings']}")

    # Meta Title
    if meta_title:
        mt_len = len(meta_title.strip())
        report["meta_title_length"] = mt_len
        report["meta_title_ok"] = _META_TITLE_MIN <= mt_len <= _META_TITLE_MAX
        if not report["meta_title_ok"]:
            report["warnings"].append(f"Meta title ma {mt_len} znaków (zalecane {_META_TITLE_MIN}–{_META_TITLE_MAX}).")

    # Meta Description
    if meta_description:
        md_len = len(meta_description.strip())
        report["meta_description_length"] = md_len
        report["meta_description_ok"] = _META_DESC_MIN <= md_len <= _META_DESC_MAX
        if not report["meta_description_ok"]:
            report["warnings"].append(f"Meta description ma {md_len} znaków (zalecane {_META_DESC_MIN}–{_META_DESC_MAX}).")

    # HTML cleanliness
    val_res = validate_clean_html(final_html)
    report["contains_forbidden_tags"] = val_res["contains_forbidden_tags"]
    report["contains_forbidden_attrs"] = val_res["contains_forbidden_attrs"]
    report["forbidden_tags_list"] = val_res.get("forbidden_tags_list", [])
    report["forbidden_attrs_list"] = val_res.get("forbidden_attrs_list", [])

    return report
