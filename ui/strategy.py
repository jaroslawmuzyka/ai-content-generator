import streamlit as st
import json
from services.campaign_service import get_campaigns
from services.strategy_repository import get_campaign_strategy, save_campaign_strategy

def render():
    st.header("Strategia Treści i Marketing")
    st.write("Skonfiguruj strategię marketingową, personę i insight, które napędzą prompty z grupy Atrakcyjność.")
    
    camps = get_campaigns()
    if not camps:
        st.info("Najpierw utwórz kampanię w zakładce Kampanie.")
        return
        
    camp_options = {c["id"]: c["name"] for c in camps}
    selected_camp_id = st.selectbox("Wybierz kampanię", list(camp_options.keys()), format_func=lambda x: camp_options[x])
    
    strategy = get_campaign_strategy(selected_camp_id) or {}
    
    with st.form("strategy_form"):
        st.subheader("1. Marka / Oferta")
        brand_description = st.text_area("Opis marki", value=strategy.get("brand_description", ""))
        value_proposition = st.text_input("Propozycja wartości (Value Proposition)", value=strategy.get("value_proposition", ""))
        proof_points = st.text_area("Dowody / Proof points", value=strategy.get("proof_points", ""))
        content_goal = st.text_input("Główny cel treści (np. edukacja, sprzedaż)", value=strategy.get("content_goal", ""))
        call_to_action = st.text_input("Główne Call To Action (CTA)", value=strategy.get("call_to_action", ""))
        
        st.subheader("2. Odbiorca")
        target_audience = st.text_area("Grupa docelowa", value=strategy.get("target_audience", ""))
        persona = st.text_area("Persona", value=strategy.get("persona", ""))
        consumer_insight = st.text_area("Insight konsumencki", value=strategy.get("consumer_insight", ""))
        customer_language = st.text_area("Język klienta (jak mówią klienci)", value=strategy.get("customer_language", ""))
        main_pain_points = st.text_area("Problemy / Obawy / Bariery", value=strategy.get("main_pain_points", ""))
        main_desires = st.text_area("Pragnienia / Cele", value=strategy.get("main_desires", ""))
        decision_triggers = st.text_area("Momenty wyzwalające decyzję", value=strategy.get("decision_triggers", ""))
        
        st.subheader("3. Ton i styl")
        brand_tone = st.text_input("Ton marki", value=strategy.get("brand_tone", ""))
        brand_archetype = st.text_input("Archetyp marki", value=strategy.get("brand_archetype", ""))
        required_phrases = st.text_area("Słowa wymagane (po przecinku)", value=strategy.get("required_phrases", ""))
        forbidden_phrases = st.text_area("Słowa zakazane (po przecinku)", value=strategy.get("forbidden_phrases", ""))
        
        st.subheader("4. Frameworki marketingowe")
        existing_fw = strategy.get("marketing_frameworks") or ["AIDA", "PAS", "FAB", "DELTA", "SPICE", "Archetyp marki"]
        fw_options = ["AIDA", "PAS", "FAB", "DELTA", "SPICE", "Storytelling", "Archetyp marki", "Rytualizacja marki", "SCAMPER", "Kwiat Lotosu"]
        selected_fw = st.multiselect("Zaznacz używane frameworki", fw_options, default=[f for f in existing_fw if f in fw_options])
        
        submitted = st.form_submit_button("Zapisz Strategię", type="primary")
        
        if submitted:
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
                st.success("Zapisano strategię!")
