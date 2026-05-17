import streamlit as st
import pandas as pd
from services.dashboard_service import get_dashboard_metrics, get_recent_jobs, get_recent_errors, mark_interrupted_jobs, restore_interrupted_jobs
from services.campaign_service import get_campaigns
from services.export_service import get_export_history

def render():
    st.title("🎛️ Dashboard")
    st.write("Panel kontrolny i nadzór nad postępami całego zespołu. Widok aktualizowany po odświeżeniu.")
    
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
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📌 Aktywne Kampanie", metrics.get("active_campaigns", 0))
    c2.metric("📦 W Kolejce", counts.get("queued", 0))
    c3.metric("⚙️ Przetwarzane", counts.get("processing", 0))
    c4.metric("👁️ Do Przeglądu", counts.get("needs_review", 0))
    c5.metric("✅ Zakończone", counts.get("completed", 0))
    c6.metric("🚨 Błędy", counts.get("failed", 0) + counts.get("interrupted", 0))
    
    st.divider()
    
    # Akcja naprawcza
    if counts.get("interrupted", 0) > 0:
        st.error("W systemie zalegają zadania o statusie `interrupted`. Zostały one brutalnie zerwane przez brak połączenia/wyłączenie karty.", icon="🛑")
        if st.button("🔄 Przywróć przerwane zadania do kolejki (`queued`)", type="primary"):
            c = restore_interrupted_jobs()
            st.success(f"Zregenerowano {c} zadań i wrzucono na początek kolejki!")
            st.rerun()
            
    # -------------------------------------------------------------
    # 3. LISTY OSTATNICH ZDARZEŃ (WIDOK DZIELONY)
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
