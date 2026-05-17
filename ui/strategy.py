import streamlit as st
import json
from services.campaign_service import get_campaigns
from services.strategy_repository import get_campaign_strategy, save_campaign_strategy

def render():
    st.title("🎯 Strategia Treści i Marketing")
    st.write("Te dane pomagają modelowi pisać bardziej trafne, mniej generyczne i lepiej dopasowane teksty.")

    camps = get_campaigns()
    if not camps:
        st.warning("⚠️ Najpierw utwórz kampanię w zakładce **Kampanie**, a potem wróć tutaj.")
        return

    camp_options = {c["id"]: c["name"] for c in camps}
    selected_camp_id = st.selectbox(
        "Dla której kampanii edytujesz strategię?",
        list(camp_options.keys()),
        format_func=lambda x: camp_options[x]
    )

    strategy = get_campaign_strategy(selected_camp_id) or {}

    st.divider()

    # Formularz podzielony na zakładki tematyczne
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Marka i oferta",
        "👤 Odbiorca",
        "🎨 Styl i ton",
        "📣 CTA i cel treści",
        "🔤 Frazy wymagane / zakazane"
    ])

    # ------------------------------------------------------------------
    # TAB 1: Marka i oferta
    # ------------------------------------------------------------------
    with tab1:
        st.info("Opisz markę lub sklep tak, jak tłumaczyłbyś nowemu pracownikowi. AI użyje tego jako tła dla wszystkich tekstów tej kampanii.")
        brand_description = st.text_area(
            "Opis marki / sklepu / firmy",
            value=strategy.get("brand_description", ""),
            height=120,
            placeholder="Np. Jesteśmy polskim sklepem z obuwiem sportowym. Specjalizujemy się w produktach Nike, Adidas i Asics. Działamy od 2010 roku.",
            help="Im bardziej konkretny opis, tym lepiej AI zrozumie kontekst."
        )
        value_proposition = st.text_input(
            "Propozycja wartości (Value Proposition)",
            value=strategy.get("value_proposition", ""),
            placeholder="Np. Gwarantujemy dostawę w 24h i 365 dni na zwroty.",
            help="Czym wyróżniacie się na tle konkurencji? Co sprawia, że klient wybiera właśnie Was?"
        )
        proof_points = st.text_area(
            "Dowody wiarygodności (Proof Points)",
            value=strategy.get("proof_points", ""),
            height=80,
            placeholder="Np. 15 000 opinii 5★, certyfikat ISO, oficjalny dystrybutor Nike w Polsce.",
            help="Fakty, liczby, certyfikaty, nagrody — wszystko co buduje zaufanie."
        )

    # ------------------------------------------------------------------
    # TAB 2: Odbiorca
    # ------------------------------------------------------------------
    with tab2:
        st.info("Im dokładniej opiszesz swojego klienta, tym bardziej trafiony będzie język i argumentacja tekstów.")
        target_audience = st.text_area(
            "Grupa docelowa",
            value=strategy.get("target_audience", ""),
            height=80,
            placeholder="Np. Kobiety 25–45 lat, aktywne fizycznie, szukające wygodnych butów do codziennego noszenia i fitnessu.",
            help="Kim jest Twój główny klient?"
        )
        persona = st.text_area(
            "Persona klienta",
            value=strategy.get("persona", ""),
            height=80,
            placeholder="Np. Marta, 32 lata, mama dwójki dzieci, trenuje jogę 3x w tygodniu, ceni ergonomię i modny wygląd.",
            help="Stwórz fikcyjną postać reprezentującą idealnego klienta."
        )
        consumer_insight = st.text_area(
            "Insight konsumencki (prawdziwa motywacja)",
            value=strategy.get("consumer_insight", ""),
            height=80,
            placeholder="Np. Klientki nie kupują butów sportowych — kupują pewność siebie i poczucie, że dbają o siebie.",
            help="Głęboka, emocjonalna prawda o tym, czego naprawdę chce Twój klient."
        )
        customer_language = st.text_area(
            "Język klienta (jak mówią o produkcie)",
            value=strategy.get("customer_language", ""),
            height=80,
            placeholder="Np. 'wygodne tenisówki', 'buty do biegania', 'adidasy na co dzień'.",
            help="Słowa i zwroty, których używają klienci w opiniach i wyszukiwarkach."
        )
        main_pain_points = st.text_area(
            "Bóle / Obawy / Bariery zakupowe",
            value=strategy.get("main_pain_points", ""),
            height=80,
            placeholder="Np. Obawa, że rozmiar będzie zły; brak zaufania do nieznanych marek; wysoka cena.",
            help="Co powstrzymuje klienta przed zakupem?"
        )
        main_desires = st.text_area(
            "Pragnienia i cele klienta",
            value=strategy.get("main_desires", ""),
            height=80,
            placeholder="Np. Chcą wyglądać sportowo bez wysiłku; chcą produktów trwałych i wygodnych.",
            help="Co klient chce osiągnąć lub poczuć po zakupie?"
        )
        decision_triggers = st.text_area(
            "Momenty wyzwalające decyzję zakupową",
            value=strategy.get("decision_triggers", ""),
            height=80,
            placeholder="Np. Sezon letni, start sezonu treningowego, poszukiwanie prezentu, promocja.",
            help="Co sprawia, że klient zaczyna szukać produktu właśnie teraz?"
        )

    # ------------------------------------------------------------------
    # TAB 3: Styl i ton
    # ------------------------------------------------------------------
    with tab3:
        st.info("Ton komunikacji decyduje o tym, czy teksty brzmią jak ekspert, przyjaciel, prestiżowa marka czy luźny influencer.")
        brand_tone = st.text_input(
            "Ton marki",
            value=strategy.get("brand_tone", ""),
            placeholder="Np. Profesjonalny, ale przyjazny. Ekspercki, nie napuszony.",
            help="Np. ekspercki, prosty, empatyczny, premium, techniczny."
        )
        brand_archetype = st.text_input(
            "Archetyp marki (Opcjonalne)",
            value=strategy.get("brand_archetype", ""),
            placeholder="Np. Bohater, Mędrzec, Odkrywca, Towarzysz, Mag...",
            help="Archetyp to 'osobowość' marki wg modeli marketingowych Junga."
        )

        st.markdown("**Frameworki marketingowe do użycia przez AI:**")
        existing_fw = strategy.get("marketing_frameworks") or []
        fw_options = ["AIDA", "PAS", "FAB", "DELTA", "SPICE", "Storytelling", "Archetyp marki", "Rytualizacja marki", "SCAMPER", "Kwiat Lotosu"]
        selected_fw = st.multiselect(
            "Zaznacz frameworki, które AI ma stosować:",
            fw_options,
            default=[f for f in existing_fw if f in fw_options],
            help="AI będzie się starać stosować wybrane frameworki przy tworzeniu tekstów z grupy 'Atrakcyjność'."
        )

    # ------------------------------------------------------------------
    # TAB 4: CTA i cel treści
    # ------------------------------------------------------------------
    with tab4:
        st.info("Określ, co ma zrobić czytelnik po przeczytaniu tekstu — to wpływa na strukturę i argumentację generowanego contentu.")
        content_goal = st.text_input(
            "Główny cel tekstu",
            value=strategy.get("content_goal", ""),
            placeholder="Np. Sprzedaż, Edukacja, Budowanie świadomości marki, Generowanie leadów.",
            help="Np. edukacja, sprzedaż, przejście do kategorii, zapis na konsultację."
        )
        call_to_action = st.text_input(
            "Główne Call To Action (CTA)",
            value=strategy.get("call_to_action", ""),
            placeholder="Np. 'Kup teraz i zyskaj darmową dostawę!', 'Sprawdź pełną kolekcję.'",
            help="Docelowe wezwanie do działania, np. sprawdź ofertę, skontaktuj się, pobierz poradnik."
        )

    # ------------------------------------------------------------------
    # TAB 5: Frazy wymagane i zakazane
    # ------------------------------------------------------------------
    with tab5:
        st.info("Frazy wymagane sprawią, że AI zawsze je uwzględni. Zakazane — że AI ich uniknie. Wpisuj po przecinku.")
        required_phrases = st.text_area(
            "Słowa / frazy WYMAGANE w tekstach (po przecinku)",
            value=strategy.get("required_phrases", ""),
            height=80,
            placeholder="Np. darmowa dostawa, certyfikowany produkt, gwarancja 2 lata",
            help="AI będzie się starać wpleść te frazy naturalnie w tekst."
        )
        forbidden_phrases = st.text_area(
            "Słowa / frazy ZAKAZANE — których AI nie może użyć (po przecinku)",
            value=strategy.get("forbidden_phrases", ""),
            height=80,
            placeholder="Np. najtańszy, byle jaki, okazja, super promocja",
            help="Zwroty, których AI ma unikać w treści."
        )

    # ------------------------------------------------------------------
    # PRZYCISK ZAPISU (poza tabami, zawsze widoczny)
    # ------------------------------------------------------------------
    st.divider()
    if st.button("💾 Zapisz Strategię", type="primary", use_container_width=True):
        data = {
            "brand_description": brand_description,
            "value_proposition": value_proposition,
            "proof_points": proof_points,
            "content_goal": content_goal,
            "call_to_action": call_to_action,
            "target_audience": target_audience,
            "persona": persona,
            "consumer_insight": consumer_insight,
            "customer_language": customer_language,
            "main_pain_points": main_pain_points,
            "main_desires": main_desires,
            "decision_triggers": decision_triggers,
            "brand_tone": brand_tone,
            "brand_archetype": brand_archetype,
            "required_phrases": required_phrases,
            "forbidden_phrases": forbidden_phrases,
            "marketing_frameworks": selected_fw
        }
        if save_campaign_strategy(selected_camp_id, data):
            st.success("✅ Strategia zapisana! Wpłynie ona na jakość wszystkich przyszłych generowań w tej kampanii.")
        else:
            st.error("❌ Nie udało się zapisać strategii. Sprawdź połączenie z Supabase w zakładce Ustawienia.")
