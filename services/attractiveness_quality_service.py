def analyze_attractiveness_quality(job, final_html, strategy_data):
    if not final_html:
        return {"error": "Brak tekstu"}
        
    text_lower = final_html.lower()
    report = {
        "has_cta": False,
        "forbidden_phrases_found": [],
        "generic_phrases_found": [],
        "required_phrases_found": [],
        "required_phrases_missing": []
    }
    
    # Check CTA
    cta = job.get("call_to_action") or (strategy_data.get("call_to_action") if strategy_data else None)
    if cta:
        report["has_cta"] = cta.lower() in text_lower
        
    # Check generic phrases
    generic_phrases = [
        "w dzisiejszych czasach", "warto zwrócić uwagę", "szeroki wybór",
        "wysoka jakość", "idealne rozwiązanie", "dopasowane do potrzeb",
        "profesjonalne podejście", "kompleksowa oferta", "dynamicznie rozwijający się",
        "innowacyjne rozwiązania", "jako sztuczna inteligencja", "jako model językowy",
        "nie mogę", "nie jestem w stanie"
    ]
    
    for phrase in generic_phrases:
        if phrase in text_lower:
            report["generic_phrases_found"].append(phrase)
            
    # Check forbidden
    forbidden_str = strategy_data.get("forbidden_phrases") if strategy_data else ""
    if forbidden_str:
        forbidden_list = [p.strip().lower() for p in forbidden_str.split(",") if p.strip()]
        for phrase in forbidden_list:
            if phrase in text_lower:
                report["forbidden_phrases_found"].append(phrase)
                
    # Check required
    required_str = strategy_data.get("required_phrases") if strategy_data else ""
    if required_str:
        required_list = [p.strip().lower() for p in required_str.split(",") if p.strip()]
        for phrase in required_list:
            if phrase in text_lower:
                report["required_phrases_found"].append(phrase)
            else:
                report["required_phrases_missing"].append(phrase)
                
    return report
