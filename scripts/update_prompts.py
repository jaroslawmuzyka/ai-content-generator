import sys
import os

# Dodaj ścieżkę do głównego katalogu aplikacji, by móc importować jej moduły
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import get_supabase_client
from services.prompt_templates_mm import PROMPTS_MM

def update_prompts_in_db():
    client = get_supabase_client()
    if not client:
        print("Brak połączenia z bazą danych Supabase.")
        return

    print("Rozpoczynam aktualizację promptów w bazie danych...")
    
    # Krok 1: Pobierz definicje dla meta_titles_and_descriptions oraz seo_abstract
    meta_step = next((s for s in PROMPTS_MM if s["key"] == "meta_titles_and_descriptions"), None)
    abstract_step = next((s for s in PROMPTS_MM if s["key"] == "seo_abstract"), None)
    
    if not meta_step or not abstract_step:
        print("Nie znaleziono definicji kroków w prompt_templates_mm.py")
        return

    # Słownik ułatwiający aktualizację
    updates = {
        "meta_titles_and_descriptions": {
            "system_prompt": meta_step["sys"],
            "user_prompt": meta_step["user"]
        },
        "seo_abstract": {
            "system_prompt": abstract_step["sys"],
            "user_prompt": abstract_step["user"]
        }
    }

    try:
        for step_key, data in updates.items():
            print(f"\nAktualizacja kroku: {step_key}")
            
            # Aktualizacja default_prompt_steps
            res_def = client.table("default_prompt_steps") \
                .update(data) \
                .eq("step_key", step_key) \
                .execute()
            print(f" Zaktualizowano default_prompt_steps: {len(res_def.data)} wierszy.")

            # Aktualizacja campaign_prompt_steps
            res_camp = client.table("campaign_prompt_steps") \
                .update(data) \
                .eq("step_key", step_key) \
                .execute()
            print(f" Zaktualizowano campaign_prompt_steps: {len(res_camp.data)} wierszy.")
            
        print("\n✅ Wszystkie prompty zostały pomyślnie zaktualizowane w bazie danych!")
        
    except Exception as e:
        print(f"\n❌ Wystąpił błąd podczas aktualizacji bazy: {str(e)}")

if __name__ == "__main__":
    update_prompts_in_db()
