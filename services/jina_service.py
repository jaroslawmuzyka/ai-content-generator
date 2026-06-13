import requests
import re
import json
import logging
import streamlit as st
from services.ai_service import generate_ai_response

logger = logging.getLogger("ai_content_generator.jina")

def fetch_jina_content(url, api_key, engine="cf-browser-rendering", target_selector=None, remove_selector=None, retain_images="none"):
    """
    Pobiera treść ze strony korzystając z Jina AI Reader API.
    """
    jina_url = f"https://r.jina.ai/{url}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Engine": engine,
        "X-Retain-Images": retain_images
    }
    
    if target_selector and target_selector.strip():
        headers["X-Target-Selector"] = target_selector.strip()
        
    if remove_selector and remove_selector.strip():
        headers["X-Remove-Selector"] = remove_selector.strip()
        
    try:
        response = requests.get(jina_url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Błąd podczas pobierania treści przez Jina AI z url {url}: {e}")
        return None

def extract_links_from_markdown(markdown_text):
    """
    Wyszukuje i zwraca wszystkie linki z markdownu np. [tekst](url).
    Zwraca tylko poprawne linki (zaczynające się od http lub https).
    """
    links = []
    # Szuka wzorca [cokolwiek](link)
    pattern = r'\[.*?\]\((https?://[^\s\)]+)\)'
    found = re.findall(pattern, markdown_text)
    
    # Zabezpieczenie przed duplikatami i czyszczenie
    seen = set()
    for link in found:
        if link not in seen:
            seen.add(link)
            links.append(link)
            
    return links

def extract_product_links_with_ai(markdown_text, provider, model, max_links=50):
    """
    Wysyła pobrany markdown do modelu AI, by ten wyselekcjonował
    rzeczywiste linki do produktów (pomijając stopki, nawigację itd.).
    Zwraca listę URL-i produktów.
    """
    system_prompt = f"""
Jesteś asystentem ekstrakcji danych z formatu Markdown.
Twoim zadaniem jest znalezienie i wyciągnięcie linków do produktów sklepowych z podanego tekstu ze strony kategorii.
Zignoruj wszystkie linki do stron typu: kontakt, o nas, regulamin, koszyk, inne kategorie.
Szukaj wyłącznie linków kierujących do pojedynczych stron produktowych.
Maksymalna liczba linków do pobrania to: {max_links}.

Zwróć wynik TYLKO i WYŁĄCZNIE jako czysty, poprawny JSON (tablicę stringów z url-ami). Bez markdownowych bloków ```json.
Przykład oczekiwanej odpowiedzi:
[
  "https://sklep.pl/produkt-1",
  "https://sklep.pl/produkt-2"
]
    """
    
    # Skrócenie markdownu, by uniknąć ewentualnego przekroczenia tokenów wejściowych (max ~40000 znaków to ok 10k tokenów)
    # Zostawiamy zapas, zazwyczaj lista produktów jest w pierwszej połowie kodu.
    short_markdown = markdown_text[:80000] 
    
    ai_res = generate_ai_response(
        provider=provider,
        model=model,
        system_prompt=system_prompt.strip(),
        user_prompt=f"Oto markdown ze strony kategorii:\n\n{short_markdown}",
        temperature=0.0, # chcemy deterministyczny wynik
        max_tokens=4000
    )
    
    if not ai_res["success"]:
        logger.error(f"Błąd AI podczas ekstrakcji linków: {ai_res['error']}")
        return []
        
    try:
        raw_text = ai_res["text"].strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        links = json.loads(raw_text.strip())
        if isinstance(links, list):
            # Limit do 50 jak użytkownik chciał (zapas)
            return links[:max_links]
    except Exception as e:
        logger.error(f"Nie udało się zdekodować JSON z linkami od AI: {e}\nOdpowiedź AI: {ai_res.get('text')}")
        
    return []
