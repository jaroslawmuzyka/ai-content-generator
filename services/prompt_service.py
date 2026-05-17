import streamlit as st
from db.supabase_client import get_supabase_client

def seed_default_prompts():
    """Wypełnia bazę początkowymi, domyślnymi promptami (seed)."""
    client = get_supabase_client()
    if not client:
        return False, "Brak połączenia z bazą danych."
        
    content_types = ["ecommerce_category", "ecommerce_product", "blog_post", "landing_page"]
    
    # 10 etapów bazowych zgodnych z wytycznymi
    steps_template = [
        {
            "order": 10, "key": "input_analysis", "name": "Analiza wejścia", 
            "sys": "Jesteś zaawansowanym analitykiem SEO.", 
            "user": "Przeanalizuj słowo kluczowe '{{main_keyword}}' i dodatkowe: '{{secondary_keywords}}' dla typu {{content_type}}. Uwzględnij notatki: {{additional_notes}}."
        },
        {
            "order": 20, "key": "outline", "name": "Zarys struktury", 
            "sys": "Jesteś ekspertem SEO i architektem treści.", 
            "user": "Na podstawie analizy z kroku {{previous_steps.input_analysis}}, stwórz zarys nagłówków H1, H2, H3 dla treści typu {{content_type}}. Zachowaj kontekst dla języka {{language}} ({{locale}})."
        },
        {
            "order": 30, "key": "section_plan", "name": "Plan sekcji", 
            "sys": "Jesteś wybitnym redaktorem planującym merytoryczne treści.", 
            "user": "Rozwiń poniższy zarys: {{previous_steps.outline}}. Dla każdego nagłówka opisz w 2-3 zdaniach, co dokładnie ma się w nim znaleźć, by odpowiedzieć na intencje użytkownika."
        },
        {
            "order": 40, "key": "main_content", "name": "Główna treść", 
            "sys": "Jesteś copywriterem SEO klasy Premium.", 
            "user": "Napisz treść główną typu {{content_type}} dla słowa kluczowego: {{main_keyword}}. \n\nWykorzystaj szczegółowy plan: {{previous_steps.section_plan}}. Docelowa długość: {{target_length}} znaków. \nGeneruj treść w języku: {{language}} ({{locale}}).\n\nZASADY FORMATOWANIA:\nWygeneruj wyłącznie czysty kod HTML (bez znaczników markdown typu ```html, bez div, span, klas, id i styli inline). \nDozwolone tagi to wyłącznie: h1, h2, h3, p, strong, ul, ol, li, a, table, thead, tbody, tr, th, td. \nZadbaj o nasycenie słowami: {{secondary_keywords}}."
        },
        {
            "order": 50, "key": "faq", "name": "Generowanie FAQ", 
            "sys": "Jesteś ekspertem odpowiadającym na trudne pytania klientów (sekcja FAQ).", 
            "user": "Na podstawie głównej treści: {{previous_steps.main_content}}, wygeneruj 3-5 najważniejszych pytań i odpowiedzi. \nZwróć wynik jako czysty HTML używając nagłówków <h3> dla pytań oraz <p> dla odpowiedzi. Język: {{language}}."
        },
        {
            "order": 60, "key": "meta_title", "name": "Meta Title", 
            "sys": "Jesteś rygorystycznym analitykiem SEO zajmującym się optymalizacją wyników wyszukiwania.", 
            "user": "Napisz chwytliwy, bardzo zachęcający do kliknięcia (wysoki CTR) Meta Title do treści: {{previous_steps.main_content}}. \nSłowo kluczowe to: {{main_keyword}}. \nDługość: maksymalnie 60 znaków. Język: {{language}}."
        },
        {
            "order": 70, "key": "meta_description", "name": "Meta Description", 
            "sys": "Jesteś rygorystycznym analitykiem SEO.", 
            "user": "Napisz zoptymalizowane, sprzedażowe Meta Description. Treść bazy: {{previous_steps.main_content}}. \nSłowo kluczowe to: {{main_keyword}}. \nDługość: maksymalnie 155 znaków. Język: {{language}}."
        },
        {
            "order": 80, "key": "seo_optimization", "name": "Optymalizacja SEO", 
            "sys": "Jesteś skrupulatnym weryfikatorem SEO i ekspertem semantyki HTML.", 
            "user": "Przeanalizuj i popraw ten kod HTML: {{previous_steps.main_content}} oraz FAQ: {{previous_steps.faq}}. \nTwoim celem jest niezwykle naturalne wplecenie w tekst nieużytych dotąd słów kluczowych pobocznych: {{secondary_keywords}}. \nJeśli kod ich nie wymaga, po prostu popraw płynność i styl, oddając ulepszony HTML."
        },
        {
            "order": 90, "key": "html_cleanup", "name": "Czyszczenie HTML", 
            "sys": "Jesteś perfekcyjnym parserem kodu HTML.", 
            "user": "Oczyść bezlitośnie poniższy kod HTML. \nUSUŃ CAŁKOWICIE wszystkie atrybuty class, id, style, role z jakichkolwiek tagów. \nUSUŃ CAŁKOWICIE wszystkie tagi <div>, <span>, <font>. \nPOZOSTAW TYLKO czyste tagi: h1, h2, h3, p, strong, ul, ol, li, a, table, thead, tbody, tr, th, td.\n\nKOD DO OCZYSZCZENIA:\n{{previous_steps.seo_optimization}}"
        },
        {
            "order": 100, "key": "seo_qa", "name": "Kontrola jakości SEO", 
            "sys": "Jesteś zewnętrznym weryfikatorem poprawności JSON i SEO.", 
            "user": "Przeanalizuj finalny kod: {{previous_steps.html_cleanup}}. \nSprawdź, czy występuje w nim słowo: {{main_keyword}}. \nZwróć wynik jako czysty obiekt JSON (bez markdown) zawierający pola: \n- 'main_keyword_found' (boolean)\n- 'secondary_keywords_found' (lista stringów, tych które znalazłeś)\n- 'estimated_length' (liczba całkowita)\n- 'html_clean' (boolean, czy nie ma div/span)"
        }
    ]
    
    try:
        # Sprawdzamy czy są już zainicjowane
        existing = client.table("default_prompt_sets").select("id").limit(1).execute()
        if existing.data:
            return True, "Domyślne prompty są już obecne w bazie. Pomijam inicjalizację."
            
        for ct in content_types:
            set_data = {
                "name": f"Zestaw bazowy: {ct.upper()}",
                "content_type": ct,
                "language": "pl",
                "description": f"Fabryczny zestaw instrukcji optymalny dla {ct}."
            }
            res_set = client.table("default_prompt_sets").insert(set_data).execute()
            set_id = res_set.data[0]["id"]
            
            for s in steps_template:
                step_data = {
                    "default_prompt_set_id": set_id,
                    "step_order": s["order"],
                    "step_key": s["key"],
                    "step_name": s["name"],
                    "system_prompt": s["sys"],
                    "user_prompt": s["user"],
                    "default_provider": "openai",
                    "default_model": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 4000 if s["key"] == "main_content" else 1500,
                    "output_type": "json" if s["key"] == "seo_qa" else "text"
                }
                client.table("default_prompt_steps").insert(step_data).execute()
                
        return True, "Zakończono. Domyślne prompty zostały załadowane do bazy danych."
    except Exception as e:
        return False, f"Błąd podczas instalacji promptów: {str(e)}"


# ---------------------------------------------------------------------------
# Zarządzanie promptami (CRUD operacyjny)
# ---------------------------------------------------------------------------

def get_campaign_prompt_sets(campaign_id):
    """Pobiera wszystkie zestawy promptów przypisane do danej kampanii."""
    client = get_supabase_client()
    if not client: return []
    res = client.table("campaign_prompt_sets").select("*").eq("campaign_id", campaign_id).order("created_at").execute()
    return res.data

def get_campaign_prompt_steps(set_id):
    """Pobiera kroki (etapy) konkretnego zestawu."""
    client = get_supabase_client()
    if not client: return []
    res = client.table("campaign_prompt_steps").select("*").eq("campaign_prompt_set_id", set_id).order("step_order").execute()
    return res.data

def get_default_prompt_sets():
    """Pobiera wszystkie bazowe zestawy (tylko do odczytu dla kopiowania)."""
    client = get_supabase_client()
    if not client: return []
    res = client.table("default_prompt_sets").select("*").order("name").execute()
    return res.data

def copy_default_to_campaign(campaign_id, default_set_id, custom_name=None):
    """Kopiuje set domyślny -> set kampanii oraz jego wszystkie kroki."""
    client = get_supabase_client()
    if not client: return False
    
    try:
        # Pobieramy bazowy set
        def_set = client.table("default_prompt_sets").select("*").eq("id", default_set_id).execute().data[0]
        
        # Inserujemy powiązany campaign set
        new_set_data = {
            "campaign_id": campaign_id,
            "name": custom_name or def_set["name"],
            "source_default_prompt_set_id": def_set["id"],
            "content_type": def_set["content_type"],
            "language": def_set["language"]
        }
        new_set = client.table("campaign_prompt_sets").insert(new_set_data).execute().data[0]
        
        # Pobieramy kroki domyślne
        def_steps = client.table("default_prompt_steps").select("*").eq("default_prompt_set_id", default_set_id).execute().data
        
        # Inserty kopiujące (każdy krok z osobna, aby uniknąć problemów z ograniczeniami bazy)
        for ds in def_steps:
            new_step_data = {
                "campaign_prompt_set_id": new_set["id"],
                "step_order": ds["step_order"],
                "step_key": ds["step_key"],
                "step_name": ds["step_name"],
                "system_prompt": ds["system_prompt"],
                "user_prompt": ds["user_prompt"],
                "provider": ds["default_provider"],
                "model": ds["default_model"],
                "temperature": ds["temperature"],
                "max_tokens": ds["max_tokens"],
                "output_type": ds["output_type"],
                "is_active": ds["is_active"]
            }
            client.table("campaign_prompt_steps").insert(new_step_data).execute()
            
        return True
    except Exception as e:
        st.error(f"Kopiowanie nie powiodło się: {str(e)}")
        return False

def restore_campaign_prompt_set(campaign_set_id):
    """Usuwa aktualne kroki zestawu i wkleja na nowo jego stan początkowy z bazy domyślnej."""
    client = get_supabase_client()
    if not client: return False
    
    try:
        camp_set = client.table("campaign_prompt_sets").select("source_default_prompt_set_id").eq("id", campaign_set_id).execute().data[0]
        source_id = camp_set.get("source_default_prompt_set_id")
        
        if not source_id: 
            st.error("Ten zestaw nie posiada połączenia z żadnym domyślnym zestawem bazowym.")
            return False
        
        # Kasujemy edytowane kroki
        client.table("campaign_prompt_steps").delete().eq("campaign_prompt_set_id", campaign_set_id).execute()
        
        # Kopiujemy świeże
        def_steps = client.table("default_prompt_steps").select("*").eq("default_prompt_set_id", source_id).execute().data
        for ds in def_steps:
            new_step_data = {
                "campaign_prompt_set_id": campaign_set_id,
                "step_order": ds["step_order"],
                "step_key": ds["step_key"],
                "step_name": ds["step_name"],
                "system_prompt": ds["system_prompt"],
                "user_prompt": ds["user_prompt"],
                "provider": ds["default_provider"],
                "model": ds["default_model"],
                "temperature": ds["temperature"],
                "max_tokens": ds["max_tokens"],
                "output_type": ds["output_type"],
                "is_active": ds["is_active"]
            }
            client.table("campaign_prompt_steps").insert(new_step_data).execute()
        return True
    except Exception as e:
        st.error(f"Nie powiodło się przywracanie: {str(e)}")
        return False

def update_campaign_prompt_step(step_id, data):
    """Modyfikuje poszczególne parametry etapu/kroku."""
    client = get_supabase_client()
    if not client: return False
    try:
        client.table("campaign_prompt_steps").update(data).eq("id", step_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu kroku: {str(e)}")
        return False

def update_campaign_prompt_set(set_id, data):
    """Zmienia parametry nadrzędnego zestawu, np. jego nazwę."""
    client = get_supabase_client()
    if not client: return False
    try:
        client.table("campaign_prompt_sets").update(data).eq("id", set_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu zestawu: {str(e)}")
        return False
