from bs4 import BeautifulSoup
from services.html_cleaner import validate_clean_html

def analyze_seo_quality(job: dict, final_html: str) -> dict:
    """
    Algorytmiczna weryfikacja wygenerowanej treści zgodnie ze zleceniem.
    Nie używa do tego LLM, działa lokalnie z pomocą BeautifulSoup i parsera tekstowego.
    """
    report = {
        "is_empty": False,
        "is_markdown": False,
        "char_count": 0,
        "target_length": job.get("target_length") or 0,
        "length_diff": 0,
        "main_keyword": job.get("main_keyword") or "",
        "main_keyword_count": 0,
        "secondary_keywords_used": [],
        "secondary_keywords_missing": [],
        "has_h1": False,
        "h2_count": 0,
        "contains_forbidden_tags": False,
        "contains_forbidden_attrs": False
    }
    
    if not final_html or not final_html.strip():
        report["is_empty"] = True
        return report
        
    # Szybka heurystyka: Jeśli model zgłupiał i wypluł standardowego markdowna zamiast html
    if "##" in final_html or "**" in final_html or ("[" in final_html and "](" in final_html):
        report["is_markdown"] = True
        
    soup = BeautifulSoup(final_html, "html.parser")
    
    # 1. Oczyszczamy treść z jakichkolwiek tagów HTML i zliczamy ilość czystego tekstu ze spacjami
    text_only = soup.get_text(separator=" ", strip=True)
    report["char_count"] = len(text_only)
    
    if report["target_length"] > 0:
        report["length_diff"] = report["char_count"] - report["target_length"]
        
    # 2. Liczymy wystąpienia najważniejszej frazy
    main_kw = report["main_keyword"].lower()
    if main_kw:
        report["main_keyword_count"] = text_only.lower().count(main_kw)
        
    # 3. Weryfikacja słów pobocznych
    sec_kws = job.get("secondary_keywords")
    if sec_kws:
        kws_list = [k.strip().lower() for k in sec_kws.split(",") if k.strip()]
        for kw in kws_list:
            if kw in text_only.lower():
                report["secondary_keywords_used"].append(kw)
            else:
                report["secondary_keywords_missing"].append(kw)
                
    # 4. Sprawdzanie struktury
    report["has_h1"] = len(soup.find_all("h1")) > 0
    report["h2_count"] = len(soup.find_all("h2"))
    
    # 5. Podpięcie walidacji czystości kodu (sprawdzi brud przed ewentualnym wyczyszczeniem)
    val_res = validate_clean_html(final_html)
    report["contains_forbidden_tags"] = val_res["contains_forbidden_tags"]
    report["contains_forbidden_attrs"] = val_res["contains_forbidden_attrs"]
    report["forbidden_tags_list"] = val_res.get("forbidden_tags_list", [])
    report["forbidden_attrs_list"] = val_res.get("forbidden_attrs_list", [])
    
    return report
