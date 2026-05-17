import streamlit as st
import pandas as pd
from services.campaign_service import get_campaigns
from services.prompt_service import get_campaign_prompt_sets
from services.import_service import generate_template_bytes, validate_uploaded_file, process_import

def render():
    st.title("📥 Import XLSX")
    st.write("Wgraj wiele zadań naraz z pliku Excel.")

    # ------------------------------------------------------------------
    # KROK 1: Pobierz szablon
    # ------------------------------------------------------------------
    st.markdown("### Krok 1 — Pobierz szablon Excel")
    st.write("Pobierz poniższy plik, wypełnij go swoimi danymi i wgraj z powrotem. **Nie zmieniaj nagłówków kolumn!**")

    st.download_button(
        label="📥 Pobierz oficjalny szablon (.xlsx)",
        data=generate_template_bytes(),
        file_name="Import_Szablon_AI_Content.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

    with st.expander("📋 Jakie kolumny muszą być w pliku?"):
        st.markdown("""
| Kolumna | Wymagana | Opis |
|---|---|---|
| `main_keyword` | ✅ TAK | Główna fraza kluczowa |
| `content_type` | ✅ TAK | Typ: `blog_post`, `ecommerce_category`, `ecommerce_product`, `landing_page` |
| `language` | ✅ TAK | Kod języka: `pl`, `en`, `de`, `cs`, `sk` |
| `locale` | Nie | Np. `pl-PL` (domyślnie = language) |
| `url` | Nie | Adres URL (dla optymalizacji istniejącej strony) |
| `secondary_keywords` | Nie | Frazy poboczne, po przecinku |
| `target_length` | Nie | Docelowa długość tekstu w znakach (liczba) |
| `additional_notes` | Nie | Dodatkowe wytyczne dla AI |
| `provider` | Nie | `openai` lub `openrouter` |
| `model` | Nie | Np. `gpt-4o` |
        """)

    st.divider()

    # ------------------------------------------------------------------
    # KROK 2: Konfiguracja (kampania, zestaw promptów, status)
    # ------------------------------------------------------------------
    st.markdown("### Krok 2 — Skonfiguruj import")

    all_camps = get_campaigns("active")
    if not all_camps:
        st.warning("⚠️ Nie masz żadnych aktywnych kampanii. Utwórz kampanię w zakładce **Kampanie**, a następnie wróć tutaj.")
        return

    camp_options = {c["id"]: c["name"] for c in all_camps}

    c1, c2, c3 = st.columns(3)
    selected_camp_id = c1.selectbox(
        "Kampania docelowa",
        list(camp_options.keys()),
        format_func=lambda x: camp_options[x],
        help="Do której kampanii mają trafić importowane zadania?"
    )

    prompt_sets = get_campaign_prompt_sets(selected_camp_id)
    if not prompt_sets:
        st.warning(
            "⚠️ Wybrana kampania nie ma jeszcze zestawu promptów (instrukcji AI). "
            "Przejdź do zakładki **Prompty**, skopiuj domyślny zestaw do tej kampanii, a potem wróć tutaj."
        )
        return

    set_options = {s["id"]: s["name"] for s in prompt_sets}
    selected_set_id = c2.selectbox(
        "Zestaw promptów (Pipeline)",
        list(set_options.keys()),
        format_func=lambda x: set_options[x],
        help="Zestaw instrukcji, które AI użyje do generowania każdego tekstu."
    )

    target_status = c3.selectbox(
        "Status po imporcie",
        ["queued", "draft"],
        help="**Queued** — od razu do kolejki generowania. **Draft** — zapisz, a zatwierdź później."
    )

    st.divider()

    # ------------------------------------------------------------------
    # KROK 3: Wgraj plik
    # ------------------------------------------------------------------
    st.markdown("### Krok 3 — Wgraj wypełniony plik")
    uploaded_file = st.file_uploader(
        "Przeciągnij plik XLSX tutaj lub kliknij 'Browse files'",
        type=["xlsx"],
        help="Akceptujemy wyłącznie pliki w formacie .xlsx (Excel 2007+)."
    )

    if not uploaded_file:
        return

    # ------------------------------------------------------------------
    # KROK 4: Walidacja
    # ------------------------------------------------------------------
    st.markdown("### Krok 4 — Wyniki walidacji")
    with st.spinner("Skanuję plik i sprawdzam poprawność danych..."):
        valid_records, errors_list = validate_uploaded_file(uploaded_file)

    total = len(valid_records) + len(errors_list)
    st.write(f"Przeskanowano łącznie **{total}** wierszy.")

    # Metryki podsumowujące
    mk1, mk2 = st.columns(2)
    mk1.metric("✅ Poprawnych rekordów", len(valid_records))
    mk2.metric("❌ Rekordów z błędami", len(errors_list))

    if errors_list:
        st.markdown("#### Rekordy z błędami (nie zostaną zaimportowane)")
        st.dataframe(
            pd.DataFrame(errors_list),
            use_container_width=True,
            hide_index=True
        )

    if valid_records:
        with st.expander(f"👁️ Podgląd poprawnych rekordów ({len(valid_records)} wierszy, max 50)"):
            st.dataframe(pd.DataFrame(valid_records).head(50), use_container_width=True, hide_index=True)

        st.divider()

        # ------------------------------------------------------------------
        # KROK 5: Dodaj do kolejki
        # ------------------------------------------------------------------
        st.markdown("### Krok 5 — Dodaj poprawne rekordy do systemu")

        if len(errors_list) > 0:
            st.info(f"ℹ️ Błędne rekordy zostaną pominięte. Do systemu trafi **{len(valid_records)}** z **{total}** wierszy.")

        if st.button(
            f"🚀 Importuj {len(valid_records)} rekordów → status '{target_status.upper()}'",
            type="primary",
            use_container_width=True
        ):
            prog_bar = st.progress(0)
            prog_txt = st.empty()

            def on_progress(current, total_c):
                pct = min(100, int((current / total_c) * 100))
                prog_bar.progress(pct)
                prog_txt.info(f"Tworzenie zadania {current} z {total_c}...")

            op_name = st.session_state.get("current_operator", "System Import")

            with st.spinner("Zapisuję do bazy danych..."):
                ok, msg = process_import(
                    valid_records, selected_camp_id, selected_set_id,
                    target_status, op_name, on_progress
                )

            if ok:
                prog_bar.progress(100)
                prog_txt.empty()
                st.success(f"Dodano {len(valid_records)} zadań do kolejki.")
                if target_status == "queued":
                    st.info("➡️ Przejdź teraz do zakładki **Kolejka**, aby uruchomić generowanie AI.")
                else:
                    st.info("➡️ Przejdź do zakładki **Kolejka**, aby ręcznie zatwierdzić zadania Draft i wysłać je do kolejki.")
                st.balloons()
            else:
                prog_txt.error(f"❌ Błąd podczas importu: {msg}\n\nSprawdź połączenie z bazą Supabase w zakładce **Ustawienia**.")
    else:
        st.warning("❌ Plik nie zawiera żadnych poprawnych rekordów. Popraw błędy opisane powyżej i wgraj plik ponownie.")
