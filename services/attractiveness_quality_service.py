from bs4 import BeautifulSoup

# Rozbudowana lista generycznych fraz typowych dla AI-generated content
GENERIC_PHRASES = [
    # Klasyczne AI kliszki
    "w dzisiejszych czasach",
    "warto zwrócić uwagę",
    "nie sposób nie zauważyć",
    "nie ulega wątpliwości",
    "jak powszechnie wiadomo",
    "bez wątpienia",
    "bez wątpliwości",
    "nie ma wątpliwości",
    "coraz więcej osób",
    "z roku na rok",
    "w obecnych czasach",
    "we współczesnym świecie",
    "w dobie cyfryzacji",
    "w erze internetu",
    "dynamicznie rozwijający się",
    "prężnie rozwijający się",
    "innowacyjne rozwiązania",
    "nowoczesne podejście",
    "kompleksowa oferta",
    "szeroki wybór",
    "bogata oferta",
    "wysoka jakość",
    "najwyższa jakość",
    "doskonała jakość",
    "idealne rozwiązanie",
    "dopasowane do potrzeb",
    "dedykowane rozwiązanie",
    "profesjonalne podejście",
    "profesjonalna obsługa",
    "indywidualne podejście",
    "wyjątkowe doświadczenie",
    "niezrównana jakość",
    "doskonały wybór",
    "lider rynku",
    "wiodący dostawca",
    "renomowana firma",
    "sprawdzone rozwiązanie",
    "skuteczne rozwiązanie",
    # AI self-disclosure
    "jako sztuczna inteligencja",
    "jako model językowy",
    "jako asystent ai",
    "nie mogę",
    "nie jestem w stanie",
    "nie posiadam możliwości",
    "nie mam dostępu",
    "moje możliwości",
    "jako ai",
    "oto tekst",
    "poniżej znajdziesz",
    "oczywiście, oto",
    "z przyjemnością",
    "mam nadzieję, że",
    "jeśli masz pytania",
    "daj mi znać",
    # Puste marketingowe
    "kluczowe znaczenie",
    "ogromne znaczenie",
    "niezwykle ważne",
    "niezwykłe możliwości",
    "wiele korzyści",
    "liczne zalety",
    "mnóstwo możliwości",
    "szereg możliwości",
    "różnorodne opcje",
    "bogactwo możliwości",
    "nieograniczone możliwości",
    "pełna kontrola",
    "pełen potencjał",
    "pełne spektrum",
    # Fałszywa pilność
    "nie czekaj",
    "działaj już teraz",
    "skorzystaj już dziś",
    "ostatnia szansa",
    "limitowana oferta",
    # Puste struktury
    "warto pamiętać",
    "warto wiedzieć",
    "należy pamiętać",
    "należy zaznaczyć",
    "warto zaznaczyć",
    "istotne jest",
    "ważne jest",
    "kluczowe jest",
    "co warto wiedzieć",
]

def analyze_attractiveness_quality(job: dict, final_html: str, strategy_data: dict) -> dict:
    """
    Regułowa analiza atrakcyjności i skuteczności marketingowej tekstu.
    Nie używa LLM — działa lokalnie na podstawie listy fraz i reguł.
    """
    report = {
        "has_cta": False,
        "forbidden_phrases_found": [],
        "generic_phrases_found": [],
        "required_phrases_found": [],
        "required_phrases_missing": [],
        "warnings": []
    }

    if not final_html:
        report["warnings"].append("Brak tekstu do analizy atrakcyjności.")
        return report

    # Parsujemy HTML do czystego tekstu do analizy fraz
    soup = BeautifulSoup(final_html, "html.parser")
    text_lower = soup.get_text(separator=" ", strip=True).lower()
    html_lower = final_html.lower()

    # CTA — sprawdzamy zarówno w job (override) jak i strategii kampanii
    cta = (
        job.get("call_to_action") or
        (strategy_data.get("call_to_action") if strategy_data else None) or ""
    )
    if cta:
        report["has_cta"] = cta.lower().strip() in text_lower
        if not report["has_cta"]:
            report["warnings"].append(f"Tekst nie zawiera zdefiniowanego CTA: '{cta}'.")
    else:
        # Brak CTA w strategii — sprawdzamy heurystycznie czy jest jakikolwiek imperativ
        cta_heuristics = ["kup", "zamów", "sprawdź", "pobierz", "zarejestruj", "skontaktuj", "dowiedz się więcej", "wypróbuj"]
        found_heuristic = any(h in text_lower for h in cta_heuristics)
        report["has_cta"] = found_heuristic

    # Generyczne frazy AI
    for phrase in GENERIC_PHRASES:
        if phrase in text_lower:
            report["generic_phrases_found"].append(phrase)

    if report["generic_phrases_found"]:
        report["warnings"].append(
            f"Wykryto {len(report['generic_phrases_found'])} generycznych fraz typowych dla tekstu AI: "
            f"{', '.join(report['generic_phrases_found'][:5])}{'...' if len(report['generic_phrases_found']) > 5 else ''}."
        )

    # Zakazane frazy ze strategii kampanii
    forbidden_str = strategy_data.get("forbidden_phrases") if strategy_data else ""
    if forbidden_str:
        forbidden_list = [p.strip().lower() for p in forbidden_str.split(",") if p.strip()]
        for phrase in forbidden_list:
            if phrase in text_lower:
                report["forbidden_phrases_found"].append(phrase)
        if report["forbidden_phrases_found"]:
            report["warnings"].append(
                f"Wykryto zakazane frazy ze strategii: {', '.join(report['forbidden_phrases_found'])}."
            )

    # Wymagane frazy ze strategii kampanii
    required_str = strategy_data.get("required_phrases") if strategy_data else ""
    if required_str:
        required_list = [p.strip().lower() for p in required_str.split(",") if p.strip()]
        for phrase in required_list:
            if phrase in text_lower:
                report["required_phrases_found"].append(phrase)
            else:
                report["required_phrases_missing"].append(phrase)
        if report["required_phrases_missing"]:
            report["warnings"].append(
                f"Brakuje wymaganych fraz ze strategii: {', '.join(report['required_phrases_missing'])}."
            )

    return report
