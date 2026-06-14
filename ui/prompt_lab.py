import streamlit as st
import json
import difflib
import pandas as pd
from services.prompt_service import get_campaign_prompt_sets, get_campaign_prompt_steps
from services.campaign_service import get_campaigns
from services.strategy_repository import get_campaign_strategy
from services.prompt_lab_service import (
    run_lab_pipeline, evaluate_step, improve_prompt, run_auto_loop
)
from utils.constants import CONTENT_TYPES, LOCALES, PROVIDERS, MODELS_BY_PROVIDER, DEFAULT_MODELS


def _init():
    if "prompt_lab" not in st.session_state or st.session_state["prompt_lab"] is None:
        st.session_state["prompt_lab"] = {"session_id": None, "test_job": {}, "provider": "openai",
                                           "model": "gpt-4o-mini", "strategy_data": None,
                                           "campaign_prompt_set_id": None, "iterations": []}


def _lab(): return st.session_state["prompt_lab"]

def _cur():
    """Zwraca ostatni? iteracj? z wynikami (pomija pending bez outputs)."""
    iters = _lab()["iterations"]
    for it in reversed(iters):
        if it.get("outputs"):  # ma wyniki testu
            return it
    return None

def _pending():
    """Zwraca nast?pn? iteracj? czekaj?c? na uruchomienie testu."""
    iters = _lab()["iterations"]
    for it in reversed(iters):
        if it.get("pending_test") and not it.get("outputs"):
            return it
    return None
def _sc(s): return "🟢" if s >= 8 else ("🟡" if s >= 5 else "🔴")
def _vl(v): return {"excellent":"Doskonały","good":"Dobry","needs_improvement":"Wymaga poprawy","poor":"Słaby"}.get(v, v)

def _diff(a, b):
    d = list(difflib.unified_diff(a.splitlines(keepends=True), b.splitlines(keepends=True),
                                   fromfile="PRZED", tofile="PO", lineterm=""))
    return "".join(d) if d else "(brak zmian)"

def _build_job(main_kw, sec_kw, ct, lang, locale, tlen, notes, cur_content, provider, model, campaign_id, url):
    return {"main_keyword": main_kw, "secondary_keywords": sec_kw, "content_type": ct,
            "language": lang, "locale": locale, "target_length": tlen, "current_content": cur_content,
            "additional_notes": notes, "url": url, "is_existing_url": False,
            "content_goal": "", "call_to_action": "", "campaign_id": campaign_id,
            "target_audience_override": None, "persona_override": None, "tone_override": None,
            "provider": provider, "model": model}


def _job_form(key_prefix):
    c1, c2 = st.columns(2)
    main_kw = c1.text_input("Fraza główna *", key=f"{key_prefix}_kw")
    sec_kw = c2.text_input("Frazy poboczne", key=f"{key_prefix}_sec")
    c3, c4, c5 = st.columns(3)
    ct = c3.selectbox("Typ treści", CONTENT_TYPES, key=f"{key_prefix}_ct")
    lang = c4.selectbox("Język", ["pl","en","de","cs","sk"], key=f"{key_prefix}_lang")
    locale = c5.selectbox("Lokalizacja", list(LOCALES.keys()), key=f"{key_prefix}_loc")
    c6, c7 = st.columns(2)
    tlen = c6.number_input("Długość (znaki)", 0, 20000, 4000, 500, key=f"{key_prefix}_len")
    notes = c7.text_input("Uwagi", key=f"{key_prefix}_notes")
    url = st.text_input("Adres URL do scrapowania JINA (opcjonalnie)", key=f"{key_prefix}_url", help="Jeśli kampania ma ustalone targety JINA, ten URL zostanie zescrapowany.")
    cur = st.text_area("Aktualna treść (opcja)", height=60, key=f"{key_prefix}_cur")
    return main_kw, sec_kw, ct, lang, locale, tlen, notes, url, cur


def _provider_form(key_prefix):
    c1, c2 = st.columns(2)
    prov = c1.selectbox("Provider", PROVIDERS, key=f"{key_prefix}_prov")
    mdl_list = MODELS_BY_PROVIDER.get(prov, [DEFAULT_MODELS.get(prov, "")])
    mdl = c2.selectbox("Model", mdl_list, key=f"{key_prefix}_mdl")
    if any(x in mdl for x in ["gpt-4o", "gpt-4.1", "opus"]) and "mini" not in mdl:
        st.warning("⚠️ Drogi model — do testów promptów zalecamy gpt-4o-mini lub gpt-4.1-mini.")
    return prov, mdl


def render():
    _init()
    st.title("🧪 Doskonal prompty")
    st.write("Testuj prompty, oceniaj każdy krok AI, zatwierdzaj ulepszenia i iteruj — ręcznie lub automatycznie.")

    tab_manual, tab_auto, tab_results, tab_improve, tab_history = st.tabs([
        "⚙️ Test manualny", "🔄 Auto-pętla", "📊 Wyniki i Ocena", "💡 Propozycje ulepszeń", "📜 Historia"
    ])

    # ── common: campaign/set selector ─────────────────────────────────────────
    camps = get_campaigns("all")
    if not camps:
        for tab in [tab_manual, tab_auto, tab_results, tab_improve, tab_history]:
            with tab:
                st.info("Brak kampanii. Utwórz kampanię i skopiuj do niej prompty.")
        return

    camp_opts = {c["id"]: c["name"] for c in camps}

    # =========================================================
    # TAB 1 — TEST MANUALNY
    # =========================================================
    with tab_manual:
        # ── Banner: pending iteration waiting for test ──────────────
        pending = _pending()
        if pending:
            st.success(f"### 📢 Iteracja {pending['number']} gotowa z ulepszonymi promptami!")
            st.info("Poniżej znajdziesz dane testowe z poprzedniej rundy. Kliknij 'Uruchom test', "
                    "aby przetestować ulepszone prompty — nie musisz nic zmieniać.")
            job_prev = _lab()["test_job"]
            prov_prev = _lab()["provider"]
            mdl_prev = _lab()["model"]
            st.caption(f"🔑 Fraza: **{job_prev.get('main_keyword','')}** | "
                       f"Typ: **{job_prev.get('content_type','')}** | "
                       f"Model: **{mdl_prev}** | "
                       f"Kroków z ulepszonymi promptami: **{len(pending['prompts'])}**")

            from services.prompt_lab_service import _prompts_to_steps
            if st.button(f"▶ Uruchom Iterację {pending['number']} z ulepszonymi promptami",
                         type="primary", use_container_width=True):
                steps_pending = _prompts_to_steps(pending["prompts"])
                ph = st.empty(); bar = st.progress(0)
                def pcb_p(n, i, t): bar.progress((i+1)/max(t,1)); ph.info(f"⏳ {i+1}/{t}: {n}")
                with st.spinner("Pipeline w toku..."):
                    outputs = run_lab_pipeline(steps_pending, job_prev, prov_prev, mdl_prev,
                                              _lab()["strategy_data"], pcb_p)
                bar.empty(); ph.empty()
                pending["outputs"] = outputs
                pending["pending_test"] = False
                
                from services.prompt_lab_db import save_lab_session
                camp_id = _lab().get("test_job", {}).get("campaign_id")
                set_id = _lab().get("campaign_prompt_set_id")
                new_sess_id = save_lab_session(_lab().get("session_id"), camp_id, set_id, _lab())
                if new_sess_id: _lab()["session_id"] = new_sess_id
                
                st.success(f"✅ Iteracja {pending['number']} uruchomiona! Przejdź do '📊 Wyniki i Ocena'.")
                st.rerun()

            st.divider()
            st.subheader("Lub uruchom nową sesję (inne dane testowe / inny zestaw)")

        else:
            st.subheader("Uruchom jednorazowy test")

        sel_camp = st.selectbox("Kampania:", list(camp_opts.keys()),
                                format_func=lambda x: camp_opts[x], key="m_camp")
        sets = get_campaign_prompt_sets(sel_camp)
        if not sets:
            st.warning("Brak zestawów promptów — przejdź do Prompty i skopiuj domyślne.")
        else:
            set_opts = {s["id"]: s["name"] for s in sets}
            sel_set = st.selectbox("Zestaw promptów:", list(set_opts.keys()),
                                   format_func=lambda x: set_opts[x], key="m_set")
            st.divider()
            main_kw, sec_kw, ct, lang, locale, tlen, notes, url, cur_content = _job_form("m")
            prov, mdl = _provider_form("m")
            st.divider()
            iter_n = len(_lab()["iterations"]) + 1
            if st.button(f"▶ Uruchom nową Iterację {iter_n} (z bazy promptów)", type="secondary", use_container_width=True):
                if not main_kw.strip():
                    st.error("Fraza główna jest wymagana.")
                    st.stop()
                steps = get_campaign_prompt_steps(sel_set)
                if not steps:
                    st.error("Brak kroków w zestawie.")
                    st.stop()
                strategy = get_campaign_strategy(sel_camp)
                job = _build_job(main_kw, sec_kw, ct, lang, locale, tlen, notes, cur_content, prov, mdl, sel_camp, url)
                prompts_snap = {
                    s["step_key"]: {"system": s["system_prompt"], "user": s["user_prompt"],
                                    "step_name": s["step_name"], "step_order": s["step_order"],
                                    "is_active": s.get("is_active", True),
                                    "temperature": s.get("temperature", 0.7),
                                    "max_tokens": s.get("max_tokens", 1500),
                                    "provider": s.get("provider"),
                                    "model": s.get("model")}
                    for s in steps
                }
                _lab().update({"campaign_prompt_set_id": sel_set, "test_job": job,
                                "provider": prov, "model": mdl, "strategy_data": strategy})
                ph = st.empty(); bar = st.progress(0)
                def pcb(n, i, t): bar.progress((i+1)/max(t,1)); ph.info(f"⏳ {i+1}/{t}: {n}")
                with st.spinner("Pipeline w toku..."):
                    outputs = run_lab_pipeline(steps, job, prov, mdl, strategy, pcb)
                bar.empty(); ph.empty()
                _lab()["iterations"].append({
                    "number": iter_n, "prompts": prompts_snap,
                    "outputs": outputs, "evaluations": {}, "proposals": {}, "auto": False
                })
                from services.prompt_lab_db import save_lab_session
                new_sess_id = save_lab_session(_lab().get("session_id"), sel_camp, sel_set, _lab())
                if new_sess_id: _lab()["session_id"] = new_sess_id
                
                st.success(f"✅ Iteracja {iter_n} zakończona! Przejdź do '📊 Wyniki i Ocena'.")
                st.rerun()

    # =========================================================
    # TAB 2 — AUTO-PĘTLA
    # =========================================================
    with tab_auto:
        st.subheader("🔄 Automatyczne doskonalenie promptów")

        with st.expander("ℹ️ Jak działa auto-pętla?", expanded=False):
            st.markdown("""
            Auto-pętla wykonuje **N pełnych cykli** bez żadnej ingerencji:

            | Krok | Co się dzieje |
            |------|---------------|
            | 1. Pipeline | Uruchamia generowanie treści z **aktualnymi promptami** |
            | 2. Ocena | AI-Ewaluator ocenia output każdego kroku (1-10) |
            | 3. Ulepszenie | AI-Ulepszacz przepisuje prompty kroków z oceną < progu |
            | 4. Zastosowanie | Ulepszone prompty stają się bazą dla **następnej iteracji** |

            **Iteracja 1** → oryginalne prompty z bazy  
            **Iteracja 2** → prompty poprawione po ocenie iteracji 1  
            **Iteracja 3** → prompty poprawione po ocenie iteracji 2  
            itd.

            Ostatnia iteracja generuje propozycje, ale ich **nie stosuje automatycznie** —  
            możesz je ręcznie przejrzeć w zakładce 💡 Propozycje ulepszeń.
            """)

        sel_camp_a = st.selectbox("Kampania:", list(camp_opts.keys()),
                                   format_func=lambda x: camp_opts[x], key="a_camp")
        sets_a = get_campaign_prompt_sets(sel_camp_a)
        if not sets_a:
            st.warning("Brak zestawów promptów.")
        else:
            set_opts_a = {s["id"]: s["name"] for s in sets_a}
            sel_set_a = st.selectbox("Zestaw promptów:", list(set_opts_a.keys()),
                                     format_func=lambda x: set_opts_a[x], key="a_set")
            st.divider()
            main_kw_a, sec_kw_a, ct_a, lang_a, locale_a, tlen_a, notes_a, url_a, cur_a = _job_form("a")
            prov_a, mdl_a = _provider_form("a")
            st.divider()

            ac1, ac2 = st.columns(2)
            n_iter = ac1.slider("Liczba iteracji automatycznych:", min_value=2, max_value=10, value=3)
            threshold = ac2.slider("Minimalny score bez poprawki:", min_value=6, max_value=10, value=9,
                                   help="Kroki z oceną poniżej tego progu będą ulepszane.")

            st.warning(f"⚠️ Auto-pętla wykona {n_iter} rund × (pipeline + ocena + ulepszenie). "
                       f"Może to zająć kilkanaście minut i wygenerować znaczące koszty API.")

            if st.button(f"🚀 Uruchom {n_iter} automatycznych iteracji", type="primary", use_container_width=True):
                if not main_kw_a.strip():
                    st.error("Fraza główna jest wymagana.")
                    st.stop()
                steps_a = get_campaign_prompt_steps(sel_set_a)
                if not steps_a:
                    st.error("Brak kroków w zestawie.")
                    st.stop()
                strategy_a = get_campaign_strategy(sel_camp_a)
                job_a = _build_job(main_kw_a, sec_kw_a, ct_a, lang_a, locale_a, tlen_a, notes_a, cur_a, prov_a, mdl_a, sel_camp_a, url_a)
                _lab().update({"campaign_prompt_set_id": sel_set_a, "test_job": job_a,
                                "provider": prov_a, "model": mdl_a, "strategy_data": strategy_a})

                auto_ph = st.empty()
                auto_bar = st.progress(0)

                def auto_cb(iter_num, n_total, phase, step_name, idx, total):
                    pct = ((iter_num - 1) / n_total) + (1 / n_total) * (idx / max(total, 1))
                    auto_bar.progress(min(pct, 1.0))
                    phase_labels = {"pipeline": "🏃 Pipeline", "eval": "🔍 Ocena", "improve": "✨ Ulepszanie"}
                    pl = phase_labels.get(phase, phase)
                    sn = f" — {step_name}" if step_name else ""
                    auto_ph.info(f"Iteracja {iter_num}/{n_total} | {pl}{sn}")

                with st.spinner("Auto-pętla w toku — proszę nie zamykać okna..."):
                    new_iters = run_auto_loop(
                        initial_steps=steps_a, job_data=job_a,
                        provider=prov_a, model=mdl_a, strategy_data=strategy_a,
                        n_iterations=n_iter, min_score_threshold=threshold,
                        progress_cb=auto_cb
                    )

                auto_bar.empty(); auto_ph.empty()
                offset = len(_lab()["iterations"])
                for it in new_iters:
                    it["number"] += offset
                    _lab()["iterations"].append(it)

                # ── Rich post-run summary ─────────────────────────────
                st.success(f"✅ Auto-pętla zakończona! Wykonano {len(new_iters)} iteracji.")
                st.markdown("#### Podsumowanie wyników auto-pętli")
                summary_rows = []
                for it in new_iters:
                    evals = it.get("evaluations", {})
                    scores = [e.get("score", 0) for e in evals.values() if isinstance(e, dict) and "score" in e]
                    n_improved = len(it.get("proposals", {}))
                    base_label = "(oryginalne prompty)" if it == new_iters[0] else f"(+{n_improved} ulepszeń z poprzedniej iteracji)"
                    avg_sc = round(sum(scores)/len(scores), 1) if scores else 0
                    summary_rows.append({
                        "Iteracja": f"It.{it['number']}",
                        "Prompty": base_label,
                        "Avg score": avg_sc,
                        "Kroków ocenionych": len(scores),
                        "Kroków ulepszonych": n_improved,
                    })
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

                if len(new_iters) >= 2:
                    first_sc = [e.get("score",0) for e in new_iters[0]["evaluations"].values() if isinstance(e,dict) and "score" in e]
                    last_sc  = [e.get("score",0) for e in new_iters[-1]["evaluations"].values() if isinstance(e,dict) and "score" in e]
                    if first_sc and last_sc:
                        delta = round(sum(last_sc)/len(last_sc) - sum(first_sc)/len(first_sc), 1)
                        arrow = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
                        st.info(f"{arrow} Zmiana średniego score: **{sum(first_sc)/len(first_sc):.1f} → {sum(last_sc)/len(last_sc):.1f}** ({delta:+.1f} pkt)")

                st.info("💡 Ostatnia iteracja ma propozycje ulepszeń gotowe do ręcznego przeglądu "
                        "w zakładce **💡 Propozycje ulepszeń**. Możesz je zatwierdzić i uruchomić kolejną rundę.")
                st.rerun()

    # =========================================================
    # TAB 3 — WYNIKI I OCENA
    # =========================================================
    with tab_results:
        cur = _cur()
        if not cur:
            st.info("Uruchom test (ręczny lub auto).")
        else:
            st.subheader(f"Iteracja {cur['number']} — Wyniki i Ocena")
            job = _lab()["test_job"]; prov = _lab()["provider"]; mdl = _lab()["model"]
            evals = cur["evaluations"]
            if evals:
                scores = [e.get("score",0) for e in evals.values() if isinstance(e,dict)]
                sc1,sc2,sc3 = st.columns(3)
                sc1.metric("Średnia ocena", f"{sum(scores)/len(scores):.1f}/10" if scores else "—")
                sc2.metric("Ocenionych kroków", len(scores))
                sc3.metric("Wymaga poprawy (<7)", sum(1 for s in scores if s<7))
                st.divider()

            jina_data = cur.get("outputs", {}).get("__jina")
            if jina_data and any(jina_data.values()):
                with st.expander("🌐 Podgląd danych pobranych przez Jina AI (Scrapowanie)"):
                    if jina_data.get("breadcrumbs"):
                        st.markdown("**Okruszki (Breadcrumbs):**")
                        st.text_area("", value=jina_data["breadcrumbs"], height=100, disabled=True, key=f"j_b_{cur['number']}")
                    if jina_data.get("filters"):
                        st.markdown("**Filtry (Filters):**")
                        st.text_area("", value=jina_data["filters"], height=150, disabled=True, key=f"j_f_{cur['number']}")
                    if jina_data.get("category"):
                        st.markdown("**Treść Kategorii (Category content):**")
                        st.text_area("", value=jina_data["category"], height=200, disabled=True, key=f"j_c_{cur['number']}")
                    if jina_data.get("products"):
                        st.markdown("**Produkty (Products links/names):**")
                        st.text_area("", value=jina_data["products"], height=200, disabled=True, key=f"j_p_{cur['number']}")

            if st.button("🔍 Oceń wszystkie kroki", type="primary"):
                prompts = cur["prompts"]
                outputs = cur["outputs"]
                bar2 = st.progress(0); ph2 = st.empty()
                keys = [k for k in prompts if not outputs.get(k,{}).get("skipped")]
                for i,sk in enumerate(keys):
                    ph2.info(f"Oceniam ({prov}/{mdl}) {i+1}/{len(keys)}: {prompts[sk]['step_name']}")
                    bar2.progress((i+1)/max(len(keys),1))
                    cur["evaluations"][sk] = evaluate_step(
                        sk, prompts[sk]["step_name"], 
                        outputs.get(sk,{}).get("system_prompt_used", prompts[sk]["system"]),
                        outputs.get(sk,{}).get("user_prompt_used", prompts[sk]["user"]),
                        outputs.get(sk,{}).get("output",""), job, prov, mdl)
                bar2.empty(); ph2.empty()
                st.success("Ocena zakończona!"); st.rerun()

            sorted_keys = sorted(cur["prompts"].keys(), key=lambda k: cur["prompts"][k].get("step_order",999))
            for sk in sorted_keys:
                si = cur["prompts"][sk]; oi = cur["outputs"].get(sk,{}); ev = cur["evaluations"].get(sk)
                p_prov = si.get('provider') or prov
                p_mdl = si.get('model') or mdl
                if oi.get("skipped"):
                    lbl = f"⏭️ {si['step_name']} (pominięty) | {p_prov}/{p_mdl}"
                elif ev:
                    lbl = f"{_sc(ev.get('score',0))} Krok {si['step_order']}: {si['step_name']} — {ev.get('score',0)}/10 {_vl(ev.get('verdict',''))} | {p_prov}/{p_mdl}"
                else:
                    lbl = f"⚪ Krok {si['step_order']}: {si['step_name']} — (nieoceniony) | {p_prov}/{p_mdl}"
                with st.expander(lbl):
                    out = oi.get("output","")
                    if oi.get("error"):
                        st.error(f"❌ {oi['error']}")
                    elif out:
                        st.text_area("Output:", value=out[:3000]+("…" if len(out)>3000 else ""),
                                     height=180, disabled=True, key=f"o_{sk}_{cur['number']}")
                        tin,tout = oi.get("tokens_in",0), oi.get("tokens_out",0)
                        if tin or tout: st.caption(f"Tokeny: {tin} in / {tout} out")
                    if ev:
                        ec1,ec2 = st.columns(2)
                        ec1.metric("Score", f"{ev.get('score',0)}/10")
                        ec2.write(f"**{_vl(ev.get('verdict',''))}**")
                        if ev.get("strengths"): st.success("✅ " + " | ".join(ev["strengths"]))
                        if ev.get("weaknesses"): st.error("❌ " + " | ".join(ev["weaknesses"]))
                        if ev.get("improvement_suggestions"): st.info("💡 " + " | ".join(ev["improvement_suggestions"]))

            st.divider()
            st.subheader("📝 Końcowa treść")
            last_sk = sorted_keys[-1] if sorted_keys else None
            final_content = ""
            if last_sk:
                for k in reversed(sorted_keys):
                    if not cur["outputs"].get(k, {}).get("skipped") and cur["outputs"].get(k, {}).get("output"):
                        final_content = cur["outputs"][k]["output"]
                        break
                        
            if final_content:
                tab_html, tab_raw = st.tabs(["Renderowany HTML", "Kod HTML"])
                with tab_html:
                    meta_dict = cur.get("outputs", {}).get("__meta", {})
                    m_title = meta_dict.get("title", "")
                    m_desc = meta_dict.get("description", "")
                    if m_title or m_desc:
                        st.markdown(f"<h2>{m_title or 'Brak Meta Title'}</h2><em>{m_desc or 'Brak Meta Description'}</em><hr>", unsafe_allow_html=True)
                        
                    safe_html = final_content.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")
                    st.markdown(safe_html, unsafe_allow_html=True)
                with tab_raw:
                    st.text_area("Gotowa treść", value=final_content, height=300, disabled=True, key=f"fc_{cur['number']}")
            else:
                st.info("Brak końcowej treści do wyświetlenia.")

    # =========================================================
    # TAB 4 — PROPOZYCJE ULEPSZEŃ
    # =========================================================
    with tab_improve:
        cur = _cur()
        if not cur:
            st.info("Uruchom test.")
        elif not cur["evaluations"]:
            st.info("Najpierw oceń kroki w zakładce 'Wyniki i Ocena'.")
        else:
            st.subheader(f"Iteracja {cur['number']} — Propozycje ulepszeń")
            prov = _lab()["provider"]; mdl = _lab()["model"]
            prompts_snap = cur["prompts"]
            needs_work = [sk for sk,ev in cur["evaluations"].items()
                          if isinstance(ev,dict) and ev.get("score",10)<9]
            perfect = [sk for sk,ev in cur["evaluations"].items()
                       if isinstance(ev,dict) and ev.get("score",0)>=9]
            if perfect:
                st.success(f"✅ {len(perfect)} krok(ów) bez zmian (≥9/10): " +
                           ", ".join(prompts_snap[sk]["step_name"] for sk in perfect if sk in prompts_snap))
            if not needs_work:
                st.success("🎉 Wszystkie kroki ≥9/10!"); 
            else:
                missing = [sk for sk in needs_work if sk not in cur["proposals"]]
                if missing:
                    if st.button(f"🤖 Wygeneruj propozycje dla {len(missing)} kroków", type="primary"):
                        pb = st.progress(0); pph = st.empty()
                        for i,sk in enumerate(missing):
                            pph.info(f"Ulepszam {i+1}/{len(missing)}: {prompts_snap[sk]['step_name']}")
                            pb.progress((i+1)/max(len(missing),1))
                            prop = improve_prompt(sk, prompts_snap[sk]["step_name"],
                                                  prompts_snap[sk]["system"], prompts_snap[sk]["user"],
                                                  cur["evaluations"][sk], prov, mdl)
                            cur["proposals"][sk] = {**prop, "approved": False}
                        pb.empty(); pph.empty()
                        st.success("Propozycje gotowe!"); st.rerun()

                if cur["proposals"]:
                    # ── Hurtowe zatwierdzanie ────────────────────────────
                    ba1, ba2, _ = st.columns([2, 2, 4])
                    if ba1.button("✅ Zatwierdź wszystkie", type="primary"):
                        for sk in cur["proposals"]: cur["proposals"][sk]["approved"] = True
                        st.rerun()
                    if ba2.button("❌ Odrzuć wszystkie"):
                        for sk in cur["proposals"]: cur["proposals"][sk]["approved"] = False
                        st.rerun()
                    st.markdown("---")

                    for sk in needs_work:
                        if sk not in cur["proposals"]: continue
                        prop = cur["proposals"][sk]
                        ev = cur["evaluations"].get(sk, {})
                        sname = prompts_snap[sk]["step_name"]
                        approved = prop.get("approved", False)

                        with st.expander(f"{'✅' if approved else '⬜'} **{sname}** — ocena: {ev.get('score','?')}/10", expanded=not approved):
                            if prop.get("changes_made"):
                                st.info("📝 Zmiany: " + " | ".join(prop["changes_made"]))

                            # ── System Prompt PRZED / PO ─────────────────
                            st.markdown("##### 🔧 System Prompt")
                            sp1, sp2 = st.columns(2)
                            sp1.markdown("**PRZED:**")
                            sp1.text_area("", value=prompts_snap[sk]["system"], height=250, disabled=True,
                                          key=f"sbef_{sk}_{cur['number']}")
                            sp2.markdown("**PO:**")
                            sp2.text_area("", value=prop.get("improved_system_prompt",""), height=250, disabled=True,
                                          key=f"saft_{sk}_{cur['number']}")
                            with st.expander("Diff — System Prompt"):
                                st.code(_diff(prompts_snap[sk]["system"], prop.get("improved_system_prompt","")), language="diff")

                            # ── User Prompt PRZED / PO ───────────────────
                            st.markdown("##### 📨 User Prompt")
                            up1, up2 = st.columns(2)
                            up1.markdown("**PRZED:**")
                            up1.text_area("", value=prompts_snap[sk]["user"], height=150, disabled=True,
                                          key=f"ubef_{sk}_{cur['number']}")
                            up2.markdown("**PO:**")
                            up2.text_area("", value=prop.get("improved_user_prompt",""), height=150, disabled=True,
                                          key=f"uaft_{sk}_{cur['number']}")
                            with st.expander("Diff — User Prompt"):
                                st.code(_diff(prompts_snap[sk]["user"], prop.get("improved_user_prompt","")), language="diff")

                            # Approve checkbox
                            prop["approved"] = st.checkbox(f"☑ Zatwierdź zmianę dla '{sname}'",
                                                           value=approved, key=f"appr_{sk}_{cur['number']}")

                    approved_count = sum(1 for p in cur["proposals"].values() if p.get("approved"))
                    if approved_count > 0:
                        st.divider()
                        if st.button(f"✅ Zastosuj {approved_count} zmian → Iteracja {cur['number']+1}",
                                     type="primary", use_container_width=True):
                            new_prompts = {}
                            for sk, info in prompts_snap.items():
                                p = cur["proposals"].get(sk)
                                if p and p.get("approved"):
                                    new_prompts[sk] = {**info,
                                                       "system": p.get("improved_system_prompt", info["system"]),
                                                       "user": p.get("improved_user_prompt", info["user"])}
                                else:
                                    new_prompts[sk] = dict(info)
                            next_num = cur["number"] + 1
                            _lab()["iterations"].append({
                                "number": next_num, "prompts": new_prompts,
                                "outputs": {}, "evaluations": {}, "proposals": {}, "pending_test": True
                            })
                            from services.prompt_lab_db import save_lab_session
                            c_id = _lab().get("test_job", {}).get("campaign_id")
                            s_id = _lab().get("campaign_prompt_set_id")
                            new_s_id = save_lab_session(_lab().get("session_id"), c_id, s_id, _lab())
                            if new_s_id: _lab()["session_id"] = new_s_id
                            
                            st.session_state["lab_next_iter_ready"] = next_num
                            st.rerun()

        # Banner po zatwierdzeniu (poza blokiem proposals)
        if st.session_state.get("lab_next_iter_ready"):
            next_n = st.session_state["lab_next_iter_ready"]
            st.divider()
            st.success(f"✅ Iteracja {next_n} przygotowana z ulepszonymi promptami!")
            st.info("⬆️ **Co teraz?** Przejdź do pierwszej zakładki **'⚙️ Test manualny'** "
                    f"i kliknij '▶ Uruchom Iterację {next_n} z ulepszonymi promptami'. "
                    "Dane testowe z poprzedniej rundy są już zapisane.")
            if st.button("🗑️ Zamknij tę informację"):
                st.session_state["lab_next_iter_ready"] = None
                st.rerun()

        if cur:
            st.divider()
            st.subheader("💾 Zapisz bieżące prompty do kampanii")
            st.write("Skopiuj prompty z tej iteracji do nowego zestawu w bieżącej kampanii.")
            from services.prompt_service import save_lab_prompts_to_campaign
            c1, c2 = st.columns([3, 1])
            new_set_name = c1.text_input("Nazwa nowego zestawu", value=f"Ulepszony po iteracji {cur['number']}")
            if c2.button("Zapisz", use_container_width=True):
                camp_id = _lab().get("test_job", {}).get("campaign_id")
                set_id = _lab().get("campaign_prompt_set_id")
                if camp_id and set_id:
                    if save_lab_prompts_to_campaign(camp_id, set_id, new_set_name, cur["prompts"]):
                        st.success("Pomyślnie zapisano nowy zestaw promptów w kampanii!")
                else:
                    st.error("Nie można zapisać: brak wybranej kampanii. Wykonaj nową iterację z wybraną kampanią z listy.")

    # =========================================================
    # TAB 5 — HISTORIA
    # =========================================================
    with tab_history:
        st.subheader("🗄️ Baza historycznych sesji")
        from services.prompt_lab_db import load_lab_sessions
        db_sessions = load_lab_sessions()
        if db_sessions:
            s_options = {s["id"]: f"Zaktualizowano: {s.get('updated_at','')} (ID Sesji: {s['id']})" for s in db_sessions}
            sel_sess = st.selectbox("Wybierz sesję do przywrócenia:", list(s_options.keys()), format_func=lambda x: s_options[x])
            if st.button("Przywróć wybraną sesję z bazy", type="primary"):
                for s in db_sessions:
                    if s["id"] == sel_sess:
                        st.session_state["prompt_lab"] = s["session_data"]
                        st.session_state["prompt_lab"]["session_id"] = s["id"]
                        st.success("Przywrócono sesję! Możesz przejrzeć zakładki Wyników i Ulepszeń.")
                        st.rerun()
        else:
            st.info("Brak zapisanych sesji w bazie.")

        st.divider()
        st.subheader("📜 Historia iteracji (bieżąca sesja)")
        iters = _lab()["iterations"]
        if not iters:
            st.info("Brak iteracji w bieżącej sesji.")
        else:

            # ── Summary table ─────────────────────────────────────────
            rows = []
            for it in iters:
                ev = it.get("evaluations", {})
                sc = [e.get("score", 0) for e in ev.values() if isinstance(e, dict) and "score" in e]
                rows.append({
                    "Iteracja": f"It.{it['number']}",
                    "Tryb": "🔄 Auto" if it.get("auto") else "✋ Ręczny",
                    "Prompty": "oryginalne" if (it.get("auto") and _lab()["iterations"].index(it) == next(
                        (j for j, x in enumerate(_lab()["iterations"]) if x.get("auto")), -1))
                               else ("ulepszone (auto)" if it.get("auto") else "ulepszone (ręczne)"),
                    "Avg score": round(sum(sc) / len(sc), 1) if sc else None,
                    "Ocenione kroków": len(sc),
                    "Ulepszone kroków": len(it.get("proposals", {})),
                    "Status": "⏳ Czeka na test" if it.get("pending_test") and not it.get("outputs") else "✅ Ukończona",
                })
            df_summary = pd.DataFrame(rows)
            st.dataframe(df_summary, use_container_width=True, hide_index=True)

            # ── Scoring evolution ──────────────────────────────────────
            # Collect per-step scores across all evaluated iterations
            iters_with_evals = [it for it in iters if it.get("evaluations")]
            if len(iters_with_evals) >= 1:
                st.divider()
                st.subheader("📈 Ewolucja scoringu per krok")
                st.caption("Jak zmieniał się wynik oceny każdego kroku pipeline w kolejnych iteracjach.")

                # Build a dict: step_key → {iter_num: score}
                all_step_keys = {}
                for it in iters_with_evals:
                    for sk, ev in it["evaluations"].items():
                        if isinstance(ev, dict) and "score" in ev:
                            sname = it["prompts"].get(sk, {}).get("step_name", sk)
                            all_step_keys[sk] = sname

                if all_step_keys:
                    # Build DataFrame: rows=iterations, cols=step names
                    score_data = {}
                    for it in iters_with_evals:
                        iter_label = f"It.{it['number']}"
                        score_data[iter_label] = {}
                        for sk, sname in all_step_keys.items():
                            ev = it["evaluations"].get(sk)
                            score_data[iter_label][sname] = ev.get("score") if isinstance(ev, dict) else None

                    df_scores = pd.DataFrame(score_data).T  # rows=iterations, cols=steps
                    df_scores.index.name = "Iteracja"

                    # Line chart
                    st.line_chart(df_scores, height=320)

                    # ── Per-step detail table ─────────────────────────
                    st.markdown("##### Tabela szczegółowa — Score per krok per iteracja")

                    # Build long-form table with color indicators
                    detail_rows = []
                    sorted_steps = sorted(all_step_keys.items(),
                                          key=lambda x: iters_with_evals[0]["prompts"].get(x[0], {}).get("step_order", 999))
                    for sk, sname in sorted_steps:
                        row = {"Krok": sname}
                        for it in iters_with_evals:
                            ev = it["evaluations"].get(sk)
                            sc_val = ev.get("score") if isinstance(ev, dict) else None
                            row[f"It.{it['number']}"] = sc_val
                        detail_rows.append(row)

                    df_detail = pd.DataFrame(detail_rows).set_index("Krok")

                    # Color cells: red <5, yellow 5-7, green >=8
                    def color_score(val):
                        if val is None or (isinstance(val, float) and pd.isna(val)):
                            return "color: gray"
                        v = int(val)
                        if v >= 8:
                            return "background-color: #1a7a2e; color: white"
                        elif v >= 5:
                            return "background-color: #7a6a00; color: white"
                        else:
                            return "background-color: #7a1a1a; color: white"

                    st.dataframe(
                        df_detail.style.map(color_score),
                        use_container_width=True
                    )

                    # ── Delta: first vs last iteration ───────────────
                    if len(iters_with_evals) >= 2:
                        st.markdown("##### Zmiana score: Iteracja 1 → Ostatnia")
                        first = iters_with_evals[0]
                        last = iters_with_evals[-1]
                        delta_rows = []
                        for sk, sname in sorted_steps:
                            ev_first = first["evaluations"].get(sk)
                            ev_last = last["evaluations"].get(sk)
                            sc_first = ev_first.get("score") if isinstance(ev_first, dict) else None
                            sc_last = ev_last.get("score") if isinstance(ev_last, dict) else None
                            if sc_first is not None and sc_last is not None:
                                delta = sc_last - sc_first
                                arrow = "🟢 +" if delta > 0 else ("🔴 " if delta < 0 else "⚪ ")
                                delta_rows.append({
                                    "Krok": sname,
                                    f"It.{first['number']} (start)": sc_first,
                                    f"It.{last['number']} (finał)": sc_last,
                                    "Zmiana": f"{arrow}{delta:+d}",
                                })
                        if delta_rows:
                            st.dataframe(pd.DataFrame(delta_rows), use_container_width=True, hide_index=True)

            # ── Prompt diff between two iterations ────────────────────
            if len(iters_with_evals) >= 2:
                st.divider()
                st.subheader("Porównaj prompty dwóch iteracji")
                iter_map = {it["number"]: it for it in iters}
                hc1, hc2 = st.columns(2)
                va = hc1.selectbox("Wersja A:", sorted(iter_map.keys()), key="ha")
                vb = hc2.selectbox("Wersja B:", sorted(iter_map.keys()), index=len(iters)-1, key="hb")
                if va != vb:
                    ia = iter_map[va]; ib = iter_map[vb]
                    changed = [sk for sk in ia["prompts"] if sk in ib["prompts"] and
                               (ia["prompts"][sk]["system"] != ib["prompts"][sk]["system"] or
                                ia["prompts"][sk]["user"] != ib["prompts"][sk]["user"])]
                    if not changed:
                        st.info("Brak różnic między wybranymi iteracjami.")
                    else:
                        for sk in changed:
                            pa = ia["prompts"][sk]; pb = ib["prompts"][sk]
                            with st.expander(f"📝 {pa.get('step_name', sk)}"):
                                st.markdown("**System Prompt diff:**")
                                st.code(_diff(pa["system"], pb["system"]), language="diff")
                                if pa["user"] != pb["user"]:
                                    st.markdown("**User Prompt diff:**")
                                    st.code(_diff(pa["user"], pb["user"]), language="diff")

            st.divider()
            if st.button("📥 Eksportuj sesję do JSON"):
                export = {"test_job": _lab()["test_job"], "iterations": [
                    {"number": it["number"],
                     "prompts": {sk: {"step_name": v["step_name"], "system": v["system"], "user": v["user"]}
                                 for sk, v in it["prompts"].items()},
                     "evaluations": it.get("evaluations", {})}
                    for it in iters
                ]}
                st.download_button("⬇️ Pobierz session.json",
                                   data=json.dumps(export, ensure_ascii=False, indent=2),
                                   file_name="prompt_lab_session.json", mime="application/json")

            st.divider()
            if st.button("🗑️ Resetuj sesję", type="secondary"):
                st.session_state["prompt_lab"] = None
                _init()
                st.success("Sesja zresetowana."); st.rerun()

