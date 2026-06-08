import streamlit as st
from db.supabase_client import get_supabase_client

from services.prompt_templates_p1 import PROMPTS_P1
from services.prompt_templates_p2 import PROMPTS_P2
from services.prompt_templates_p3 import PROMPTS_P3

def seed_default_prompts():
    client = get_supabase_client()
    if not client:
        return False, "Brak połączenia z bazą danych."
        
    content_types = ["ecommerce_category", "ecommerce_product", "blog_post", "landing_page"]
    
    steps_template = PROMPTS_P1 + PROMPTS_P2 + PROMPTS_P3
    
    try:
        existing = client.table("default_prompt_sets").select("id").limit(1).execute()
        if existing.data:
            pass
            
        for ct in content_types:
            set_data = {
                "name": f"Zestaw bazowy v3 (Standard XML): {ct.upper()}",
                "content_type": ct,
                "language": "pl",
                "description": f"Zestaw 13 rygorystycznych promptów SEO oraz Atrakcyjności (System/User separation)."
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
                    "default_provider": None,
                    "default_model": None,
                    "temperature": 0.7,
                    "max_tokens": s["max_tokens"],
                    "output_type": s["output_type"],
                    "stage_group": s.get("stage_group", "seo")
                }
                client.table("default_prompt_steps").insert(step_data).execute()
                
        return True, "Zakończono. Domyślne prompty zostały załadowane do bazy danych."
    except Exception as e:
        return False, f"Błąd podczas instalacji promptów: {str(e)}"

# ---------------------------------------------------------------------------
# Zarządzanie promptami (CRUD operacyjny)
# ---------------------------------------------------------------------------

def get_campaign_prompt_sets(campaign_id):
    client = get_supabase_client()
    if not client: return []
    res = client.table("campaign_prompt_sets").select("*").eq("campaign_id", campaign_id).order("created_at").execute()
    return res.data

def get_campaign_prompt_steps(set_id):
    client = get_supabase_client()
    if not client: return []
    res = client.table("campaign_prompt_steps").select("*").eq("campaign_prompt_set_id", set_id).order("step_order").execute()
    return res.data

def get_default_prompt_sets():
    client = get_supabase_client()
    if not client: return []
    res = client.table("default_prompt_sets").select("*").order("name").execute()
    return res.data

def copy_default_to_campaign(campaign_id, default_set_id, custom_name=None):
    client = get_supabase_client()
    if not client: return False
    
    try:
        def_set = client.table("default_prompt_sets").select("*").eq("id", default_set_id).execute().data[0]
        
        new_set_data = {
            "campaign_id": campaign_id,
            "name": custom_name or def_set["name"],
            "source_default_prompt_set_id": def_set["id"],
            "content_type": def_set["content_type"],
            "language": def_set["language"]
        }
        new_set = client.table("campaign_prompt_sets").insert(new_set_data).execute().data[0]
        
        def_steps = client.table("default_prompt_steps").select("*").eq("default_prompt_set_id", default_set_id).execute().data
        
        for ds in def_steps:
            new_step_data = {
                "campaign_prompt_set_id": new_set["id"],
                "step_order": ds["step_order"],
                "step_key": ds["step_key"],
                "step_name": ds["step_name"],
                "system_prompt": ds["system_prompt"],
                "user_prompt": ds["user_prompt"],
                "provider": ds["default_provider"] or None,
                "model": ds["default_model"] or None,
                "temperature": ds["temperature"],
                "max_tokens": ds["max_tokens"],
                "output_type": ds["output_type"],
                "is_active": ds["is_active"],
                "stage_group": ds.get("stage_group", "seo")
            }
            client.table("campaign_prompt_steps").insert(new_step_data).execute()
            
        return True
    except Exception as e:
        st.error(f"Kopiowanie nie powiodło się: {str(e)}")
        return False

def restore_campaign_prompt_set(campaign_set_id):
    client = get_supabase_client()
    if not client: return False
    
    try:
        camp_set = client.table("campaign_prompt_sets").select("source_default_prompt_set_id").eq("id", campaign_set_id).execute().data[0]
        source_id = camp_set.get("source_default_prompt_set_id")
        
        if not source_id: 
            st.error("Ten zestaw nie posiada połączenia z żadnym domyślnym zestawem bazowym.")
            return False
        
        client.table("campaign_prompt_steps").delete().eq("campaign_prompt_set_id", campaign_set_id).execute()
        
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
                "is_active": ds["is_active"],
                "stage_group": ds.get("stage_group", "seo")
            }
            client.table("campaign_prompt_steps").insert(new_step_data).execute()
        return True
    except Exception as e:
        st.error(f"Nie powiodło się przywracanie: {str(e)}")
        return False

def update_campaign_prompt_step(step_id, data):
    client = get_supabase_client()
    if not client: return False
    try:
        client.table("campaign_prompt_steps").update(data).eq("id", step_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu kroku: {str(e)}")
        return False

def update_campaign_prompt_set(set_id, data):
    client = get_supabase_client()
    if not client: return False
    try:
        client.table("campaign_prompt_sets").update(data).eq("id", set_id).execute()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu zestawu: {str(e)}")
        return False
