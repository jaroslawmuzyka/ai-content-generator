import streamlit as st
import pandas as pd
from services.dashboard_service import get_dashboard_metrics, get_recent_jobs, get_recent_errors, mark_interrupted_jobs, restore_interrupted_jobs
from services.campaign_service import get_campaigns
from services.export_service import get_export_history

def render():
    st.title("🎛️ Panel główny")
    st.write("Tu sprawdzisz stan kampanii, kolejki i ostatnich wygenerowanych treści.")
    
    # -------------------------------------------------------------
    # 1. ZABEZPIECZENIE TYLNE (HEARTBEAT) I CZYSZCZENIE "ZOMBIE" ZADAŃ
    # -------------------------------------------------------------
    with st.spinner("Skanowanie bazy..."):
        interrupted_count = mark_interrupted_jobs()
    if interrupted_count > 0:
        st.warning(f"⚠️ **Interwencja Systemu:** Wykryto {interrupted_count} 'zawieszonych' zadań. (Operator prawdopodobnie zamknął przeglądarkę podczas generowania AI). Zamieniono ich status z `processing` na `interrupted`.", icon="🧹")
        
    metrics = get_dashboard_metrics()
    if not metrics:
        st.error("Brak połączenia z chmurą Supabase. Moduły są nieaktywne.")
        return
        
    counts = metrics["jobs_counts"]
    
    # -------------------------------------------------------------
    # 2. METRYKI LICZBOWE (KPIs)
    # -------------------------------------------------------------
    st.markdown("### 📊 Status Produkcji")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📌 Aktywne Kampanie", metrics.get("active_campaigns", 0))
    c2.metric("📦 W Kolejce (Queued)", counts.get("queued", 0))
    c3.metric("⚙️ Przetwarzane", counts.get("processing", 0))
    c4.metric("✅ Gotowe (Completed)", counts.get("completed", 0))
    
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("🚨 Z Błędem (Failed)", counts.get("failed", 0))
    c6.metric("🛑 Przerwane (Interrupted)", counts.get("interrupted", 0))
    c7.metric("👁️ Wymaga Uwagi (Needs Review)", counts.get("needs_review", 0))
    c8.metric("📝 Szkice (Draft)", counts.get("draft", 0))
    
    st.divider()
    
    # -------------------------------------------------------------
    # 3. CO ZROBIĆ DALEJ? (Przewodnik krok po kroku)
    # -------------------------------------------------------------
    st.markdown("### 🧭 Co zrobić dalej?")
    
    active_camp_id = st.session_state.get('active_campaign_id')
    
    # Onboarding Checklist
    has_campaigns = metrics.get("active_campaigns", 0) > 0
    has_active_camp = bool(active_camp_id)
    has_prompts = False
    has_jobs = counts.get("queued", 0) > 0 or counts.get("processing", 0) > 0 or counts.get("completed", 0) > 0 or counts.get("failed", 0) > 0
    has_completed = counts.get("completed", 0) > 0
    
    if has_active_camp:
        from services.prompt_service import get_campaign_prompt_sets
        prompt_sets = get_campaign_prompt_sets(active_camp_id)
        has_prompts = len(prompt_sets) > 0
        
    st.markdown("### 🏁 Zaczynamy (Checklista)")
    
    st.checkbox("1. Utwórz kampanię", value=has_campaigns, disabled=True)
    st.checkbox("2. Uzupełnij strategię treści (opcjonalnie, ale zalecane)", value=False, disabled=True) # It's hard to dynamically check if strategy is filled, so we'll leave it as unchecked/informational or just don't check it dynamically. Wait, we can check if it exists but let's just make it a visual list.
    st.checkbox("3. Skopiuj prompty do kampanii", value=has_prompts, disabled=True)
    st.checkbox("4. Dodaj nową treść (pojedynczą lub import z XLSX)", value=has_jobs, disabled=True)
    st.checkbox("5. Uruchom kolejkę generowania", value=counts.get("processing", 0) > 0 or has_completed, disabled=True)
    st.checkbox("6. Sprawdź wynik generowania", value=has_completed, disabled=True)
    st.checkbox("7. Pobierz eksport", value=len(get_export_history()) > 0, disabled=True)

    st.divider()

    # Pomocnicza logika co pokazać
    if not has_campaigns:
        st.info("👋 **Brak kampanii.** Utwórz pierwszą kampanię, żeby zacząć generować treści.")
    elif not has_active_camp:
        st.info("🎯 **Masz kampanie w bazie, ale żadna nie jest aktywna.** Wybierz kampanię w lewym menu.")
    elif not has_prompts:
        st.warning("⚠️ **Ta kampania nie ma jeszcze promptów.** Skopiuj domyślny zestaw promptów, a potem dostosuj go do kampanii.")
    elif counts.get("queued", 0) > 0:
        st.success(f"🚀 Masz **{counts.get('queued')}** zadań w kolejce! Przejdź do zakładki **Kolejka generowania** i uruchom przetwarzanie.")
    elif counts.get("failed", 0) > 0 or counts.get("interrupted", 0) > 0:
        st.error("🚨 Wykryto błędy lub przerwane zadania. Przejdź do zakładki **Kolejka generowania**, przefiltruj status 'Failed' / 'Interrupted' i ponów próby.")
    elif not has_jobs:
        st.info("ℹ️ **Nie ma jeszcze zadań w tej kampanii.** Dodaj pojedynczą treść lub zaimportuj plik XLSX.")
    else:
        st.info("✅ Wszystko gotowe! Sprawdź **Wyniki treści** lub zleć kolejne zadania.")
            
    st.divider()
    
    # Akcja naprawcza
    if counts.get("interrupted", 0) > 0:
        st.error("W systemie zalegają zadania o statusie `interrupted`. Zostały one brutalnie zerwane przez brak połączenia/wyłączenie karty.", icon="🛑")
        if st.button("🔄 Przywróć przerwane zadania do kolejki (`queued`)", type="primary"):
            c = restore_interrupted_jobs()
            st.success(f"Zregenerowano {c} zadań i wrzucono na początek kolejki!")
            st.rerun()
            
    # -------------------------------------------------------------
    # 4. LISTY OSTATNICH ZDARZEŃ (WIDOK DZIELONY)
    # -------------------------------------------------------------
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.subheader("Ostatnie zadania w bazie")
        recent = get_recent_jobs(15)
        if not recent:
            st.info("Brak aktywności maszyny. Dodaj zadania by zobaczyć tutaj ruch.")
        else:
            df_recent = pd.DataFrame(recent)
            camps = get_campaigns("all")
            camp_map = {c["id"]: c["name"] for c in camps}
            
            # Formaty i podmiany IDków na nazwy dla ludzi
            df_recent["kampania"] = df_recent["campaign_id"].map(camp_map)
            df_recent["Data"] = df_recent["created_at"].str[:16].str.replace("T", " ")
            
            df_recent = df_recent[["Data", "kampania", "main_keyword", "status", "operator_name"]]
            df_recent.columns = ["Data Zlecenia", "Kampania", "Fraza (Pillar)", "Status", "Operator"]
            
            # Wbudowana w nowsze Streamlit ładna, czysta tabela bez IDkow rzędów
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
            
    with c_right:
        st.subheader("Log Błędów Krytycznych")
        errors = get_recent_errors(5)
        if not errors:
            st.success("Hura! Wszystkie logi AI są czyste od błędów.", icon="🥳")
        else:
            for e in errors:
                st.error(f"**{e['main_keyword']}** ({e['created_at'][:16].replace('T',' ')}) \n\n {e['error_message']}")
                
        st.subheader("Ostatnie Pobrania")
        exports = get_export_history()[:5]
        if not exports:
            st.info("Nie eksportowano jeszcze żadnych paczek XLSX do klientów.")
        else:
            for ex in exports:
                st.caption(f"📥 `{ex['file_name']}` (Pobrano przez: **{ex['operator_name']}** dnia {ex['created_at'][:16].replace('T',' ')})")
