import re
from bs4 import BeautifulSoup

# Globalne ustawienia dla dozwolonych elementów wg specyfikacji
ALLOWED_TAGS = {'h1', 'h2', 'h3', 'p', 'strong', 'b', 'ul', 'ol', 'li', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'}

def clean_html(html: str) -> str:
    """
    Czyści kod HTML z niedozwolonych znaczników i atrybutów.
    Usuwa tagi <script> i <style> w całości.
    Dla innych nieznanych tagów np. <span> - wyciąga z nich tekst i usuwa samą obwolutę.
    Dla dozwolonych tagów usuwa style, klasy, id i eventy JS.
    """
    if not html:
        return ""
        
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Całkowite usunięcie tagów (wraz z ich zawartością tekstową)
    for tag in soup(["script", "style", "head", "title", "meta"]):
        tag.decompose()
        
    # 2. Iteracja po wszystkich pozostałych znacznikach
    for tag in soup.find_all(True):
        
        # Jeśli tag jest na liście zakazanych (np. span, div, font, itp)
        # unwrap() po cichu usunie sam znacznik zachowując tekst w środku
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue
            
        # 3. Jeśli tag jest dozwolony, czyścimy jego atrybuty
        attrs_to_remove = []
        for attr in tag.attrs:
            attr_lower = attr.lower()
            # Wywalamy id, class, style i wszystkie eventy JS
            if attr_lower in ['style', 'class', 'id'] or attr_lower.startswith('on'):
                attrs_to_remove.append(attr)
                
        for attr in attrs_to_remove:
            del tag.attrs[attr]
            
    return str(soup)

def validate_clean_html(html: str) -> dict:
    """
    Funkcja analityczna, sprawdzająca co konkretnie jest zanieczyszczone.
    Nie modyfikuje HTML-a, po prostu zwraca raport.
    """
    if not html:
        return {"contains_forbidden_tags": False, "contains_forbidden_attrs": False, "forbidden_tags_list": [], "forbidden_attrs_list": []}
        
    soup = BeautifulSoup(html, "html.parser")
    
    forbidden_tags_found = []
    forbidden_attrs_found = []
    
    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            forbidden_tags_found.append(tag.name)
            
        for attr in tag.attrs:
            attr_lower = attr.lower()
            if attr_lower in ['style', 'class', 'id'] or attr_lower.startswith('on'):
                forbidden_attrs_found.append(f"{tag.name}[{attr}]")
                
    return {
        "contains_forbidden_tags": len(forbidden_tags_found) > 0,
        "contains_forbidden_attrs": len(forbidden_attrs_found) > 0,
        "forbidden_tags_list": list(set(forbidden_tags_found)),
        "forbidden_attrs_list": list(set(forbidden_attrs_found))
    }
