import streamlit as st
import json
import difflib
from services.prompt_service import get_campaign_prompt_sets, get_campaign_prompt_steps
from services.campaign_service import get_campaigns
from services.strategy_repository import get_campaign_strategy
from services.prompt_lab_service import run_lab_pipeline, evaluate_step, improve_prompt
from utils.constants import CONTENT_TYPES, LOCALES, PROVIDERS, MODELS_BY_PROVIDER, DEFAULT_MODELS


# ── helpers ──────────────────────────────────────────────────────────────────

def _init_lab():
    if "prompt_lab" not in st.session_state:
        st.session_state["prompt_lab"] = {
            "campaign_prompt_set_id": None,
            "test_job": {},
            "provider": "openai",
            "model": "gpt-4o-mini",
            "strategy_data": None,
            "iterations": [],
        }


def _lab():
    return st.session_state["prompt_lab"]


def _current_iter():
    iters = _lab()["iterations"]
    return iters[-1] if iters else None


def _score_color(score):
    if score >= 8: return "🟢"
    if score >= 5: return "🟡"
    return "🔴"


def _verdict_label(v):
    return {"excellent": "Doskonały", "good": "Dobry",
            "needs_improvement": "Wymaga poprawy", "poor": "Słaby"}.get(v, v)


def _make_diff(old, new):
    """Zwraca prosty diff tekstowy jako string."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile="Przed", tofile="Po", lineterm=""))
    return "".join(diff) if diff else "(brak zmian)"


# ── render ────────────────────────────────────────────────────────────────────

def render():
    _init_lab()
    st.title("🧪 Doskonal prompty")
    st.write("Uruchom testowe generowanie, oceń każdy krok, zatwierdź ulepszenia i iteruj — aż prompty będą idealne.")

    tab_setup, tab_results, tab_improve, tab_history = st.tabs([
        "⚙️ Konfiguracja testu",
        "📊 Wyniki i Ocena",
        "💡 Propozycje ulepszeń",
        "📜 Historia wersji",
    ])

    # =========================================================
    # TAB 1 — KONFIGURACJA
    # =========================================================
    with tab_setup:
        st.subheader("Dane testowe")
        st.caption("Wypełnij dane testowe jak w 'Nowa treść', wybierz zestaw promptów i uruchom pipeline.")

        # Kampania i zestaw promptów
        camps = get_campaigns("all")
        if not camps:
            st.info("ℹ️ Brak kampanii. Utwórz kampanię i dodaj do niej prompty.")
            return

        camp_opts = {c["id"]: c["name"] for c in camps}
        sel_camp = st.selectbox("Kampania:", list(camp_opts.keys()),
                                format_func=lambda x: camp_opts[x], key="lab_camp")

        sets = get_campaign_prompt_sets(sel_camp)
        if not sets:
            st.warning("Ta kampania nie ma zestawów promptów. Przejdź do zakładki Prompty i skopiuj domyślne.")
            return

        set_opts = {s["id"]: s["name"] for s in sets}
        sel_set = st.selectbox("Zestaw promptów:", list(set_opts.keys()),
                               format_func=lambda x: set_opts[x], key="lab_set")

        st.divider()
        st.markdown("##### Dane wejściowe zadania testowego")

        c1, c2 = st.columns(2)
        main_kw = c1.text_input("Fraza główna *", placeholder="np. najlepszy krem do twarzy dla mężczyzn")
        sec_kw = c2.text_input("Frazy poboczne", placeholder="np. krem nawilżający, pielęgnacja skóry")

        c3, c4, c5 = st.columns(3)
        content_type = c3.selectbox("Typ treści *", CONTENT_TYPES)
        language = c4.selectbox("Język *", ["pl", "en", "de", "cs", "sk"])
        locale_opts = list(LOCALES.keys())
        locale = c5.selectbox("Lokalizacja", locale_opts)

        c6, c7 = st.columns(2)
        target_length = c6.number_input("Docelowa długość (znaki)", min_value=0, value=4000, step=500)
        additional_notes = c7.text_input("Dodatkowe uwagi", placeholder="np. pisz do lekarza, użyj tonu eksperckiego")

        current_content = st.text_area("Aktualna treść (opcjonalnie)", height=80,
                                       placeholder="Wklej istniejący tekst jeśli chcesz go uwzględnić w analizie")

        st.divider()
        st.markdown("##### Model AI do testów")

        cp1, cp2 = st.columns(2)
        provider = cp1.selectbox("Provider", PROVIDERS, key="lab_provider")
        model_list = MODELS_BY_PROVIDER.get(provider, [DEFAULT_MODELS.get(provider, "")])
        model = cp2.selectbox("Model", model_list, key="lab_model")

        if any(exp in model for exp in ["gpt-4", "opus", "gpt-4.1"]):
            st.warning("⚠️ Wybrany model jest drogi. Do testów promptów zalecamy gpt-4o-mini.")

        st.divider()

        iter_num = len(_lab()["iterations"]) + 1
        btn_label = f"▶ Uruchom test — Iteracja {iter_num}"

        if st.button(btn_label, type="primary", use_container_width=True):
            if not main_kw.strip():
                st.error("Fraza główna jest wymagana.")
                st.stop()

            steps = get_campaign_prompt_steps(sel_set)
            if not steps:
                st.error("Wybrany zestaw nie ma kroków. Sprawdź prompty kampanii.")
                st.stop()

            strategy_data = get_campaign_strategy(sel_camp)
            job_data = {
                "main_keyword": main_kw.strip(),
                "secondary_keywords": sec_kw.strip(),
                "content_type": content_type,
                "language": language,
                "locale": locale,
                "target_length": target_length,
                "current_content": current_content.strip(),
                "additional_notes": additional_notes.strip(),
                "url": "", "is_existing_url": False,
                "content_goal": "", "call_to_action": "",
                "target_audience_override": None, "persona_override": None, "tone_override": None,
                "provider": provider, "model": model,
            }

            # Build initial prompts snapshot from campaign steps
            prompts_snapshot = {
                s["step_key"]: {"system": s["system_prompt"], "user": s["user_prompt"],
                                 "step_name": s["step_name"], "step_order": s["step_order"],
                                 "is_active": s.get("is_active", True), "temperature": s.get("temperature", 0.7),
                                 "max_tokens": s.get("max_tokens", 1500)}
                for s in steps
            }

            # Save config to lab state
            _lab()["campaign_prompt_set_id"] = sel_set
            _lab()["test_job"] = job_data
            _lab()["provider"] = provider
            _lab()["model"] = model
            _lab()["strategy_data"] = strategy_data

            # Run pipeline
            progress_ph = st.empty()
            prog_bar = st.progress(0)

            def on_progress(step_name, idx, total):
                prog_bar.progress((idx + 1) / max(total, 1))
                progress_ph.info(f"⏳ Krok {idx + 1}/{total}: {step_name}")

            with st.spinner("Uruchamianie pipeline..."):
                outputs = run_lab_pipeline(
                    steps=steps, job_data=job_data,
                    provider=provider, model=model,
                    strategy_data=strategy_data,
                    progress_cb=on_progress
                )

            prog_bar.empty()
            progress_ph.empty()

            new_iteration = {
                "number": iter_num,
                "prompts": prompts_snapshot,
                "outputs": outputs,
                "evaluations": {},
                "proposals": {},
                "approved_keys": [],
            }
            _lab()["iterations"].append(new_iteration)
            st.success(f"✅ Iteracja {iter_num} zakończona! Przejdź do zakładki 'Wyniki i Ocena'.")
            st.rerun()

    # =========================================================
    # TAB 2 — WYNIKI I OCENA
    # =========================================================
    with tab_results:
        iter_data = _current_iter()
        if not iter_data:
            st.info("ℹ️ Uruchom najpierw test w zakładce 'Konfiguracja testu'.")
        else:
            st.subheader(f"Iteracja {iter_data['number']} — Wyniki i Ocena")

            job = _lab()["test_job"]
            provider = _lab()["provider"]
            model = _lab()["model"]

            # Score summary
            evals = iter_data["evaluations"]
            if evals:
                scores = [e.get("score", 0) for e in evals.values() if isinstance(e, dict)]
                avg_score = sum(scores) / len(scores) if scores else 0
                needs_work = sum(1 for s in scores if s < 7)
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Średnia ocena", f"{avg_score:.1f}/10")
                sc2.metric("Kroków z oceną", len(scores))
                sc3.metric("Wymaga poprawy (<7)", needs_work)
                st.divider()

            # Evaluate all button
            col_ev, _ = st.columns([2, 5])
            if col_ev.button("🔍 Oceń wszystkie kroki AI", type="primary"):
                prompts = iter_data["prompts"]
                outputs = iter_data["outputs"]
                steps_to_eval = [k for k in prompts if not outputs.get(k, {}).get("skipped")]
                total = len(steps_to_eval)
                eval_bar = st.progress(0)
                eval_ph = st.empty()
                for idx, sk in enumerate(steps_to_eval):
                    eval_ph.info(f"⏳ Oceniam {idx + 1}/{total}: {prompts[sk]['step_name']}")
                    eval_bar.progress((idx + 1) / max(total, 1))
                    ev = evaluate_step(
                        step_key=sk,
                        step_name=prompts[sk]["step_name"],
                        system_prompt=prompts[sk]["system"],
                        output_text=outputs.get(sk, {}).get("output", ""),
                        job_data=job,
                        provider=provider,
                        model=model
                    )
                    iter_data["evaluations"][sk] = ev
                eval_bar.empty()
                eval_ph.empty()
                st.success("✅ Ocena zakończona! Wyniki poniżej.")
                st.rerun()

            # Display steps
            prompts_snap = iter_data["prompts"]
            outputs_data = iter_data["outputs"]
            sorted_steps = sorted(prompts_snap.keys(),
                                  key=lambda k: prompts_snap[k].get("step_order", 999))

            for sk in sorted_steps:
                step_info = prompts_snap[sk]
                out_info = outputs_data.get(sk, {})
                ev = iter_data["evaluations"].get(sk)

                if out_info.get("skipped"):
                    label = f"⏭️ {step_info['step_name']} (pominięty)"
                elif ev:
                    score = ev.get("score", 0)
                    label = f"{_score_color(score)} Krok {step_info['step_order']}: {step_info['step_name']} — {score}/10 {_verdict_label(ev.get('verdict',''))}"
                else:
                    label = f"⚪ Krok {step_info['step_order']}: {step_info['step_name']} — (nieoceniony)"

                with st.expander(label, expanded=False):
                    out_text = out_info.get("output", "")
                    error = out_info.get("error")
                    if error:
                        st.error(f"❌ Błąd kroku: {error}")
                    elif out_text:
                        st.markdown("**Output:**")
                        st.text_area("", value=out_text[:3000] + ("…" if len(out_text) > 3000 else ""),
                                     height=200, disabled=True, key=f"out_{sk}_{iter_data['number']}")
                        tin = out_info.get("tokens_in", 0)
                        tout = out_info.get("tokens_out", 0)
                        if tin or tout:
                            st.caption(f"Tokeny: {tin} in / {tout} out")
                    else:
                        st.warning("Brak outputu dla tego kroku.")

                    if ev:
                        st.markdown("**Ocena AI:**")
                        ec1, ec2 = st.columns(2)
                        ec1.metric("Score", f"{ev.get('score', 0)}/10")
                        ec2.write(f"**Werdykt:** {_verdict_label(ev.get('verdict', ''))}")
                        if ev.get("strengths"):
                            st.success("✅ Mocne strony: " + " | ".join(ev["strengths"]))
                        if ev.get("weaknesses"):
                            st.error("❌ Słabości: " + " | ".join(ev["weaknesses"]))
                        if ev.get("improvement_suggestions"):
                            st.info("💡 Sugestie do promptu: " + " | ".join(ev["improvement_suggestions"]))

    # =========================================================
    # TAB 3 — PROPOZYCJE ULEPSZEŃ
    # =========================================================
    with tab_improve:
        iter_data = _current_iter()
        if not iter_data:
            st.info("ℹ️ Najpierw uruchom test w zakładce 'Konfiguracja testu'.")
        elif not iter_data["evaluations"]:
            st.info("ℹ️ Najpierw oceń kroki w zakładce 'Wyniki i Ocena'.")
        else:
            st.subheader(f"Iteracja {iter_data['number']} — Propozycje ulepszeń")
            provider = _lab()["provider"]
            model = _lab()["model"]
            prompts_snap = iter_data["prompts"]

            # Steps that need improvement
            steps_needing_work = [
                sk for sk, ev in iter_data["evaluations"].items()
                if isinstance(ev, dict) and ev.get("score", 10) < 9
            ]
            steps_excellent = [
                sk for sk, ev in iter_data["evaluations"].items()
                if isinstance(ev, dict) and ev.get("score", 0) >= 9
            ]

            if steps_excellent:
                st.success(f"✅ {len(steps_excellent)} krok(ów) bez konieczności zmian (≥9/10): " +
                           ", ".join(prompts_snap[sk]["step_name"] for sk in steps_excellent if sk in prompts_snap))

            if not steps_needing_work:
                st.success("🎉 Wszystkie ocenione kroki mają wynik ≥9/10! Nie ma co poprawiać.")
            else:
                # Generate proposals button
                missing_proposals = [sk for sk in steps_needing_work if sk not in iter_data["proposals"]]
                if missing_proposals and st.button(f"🤖 Wygeneruj propozycje dla {len(missing_proposals)} kroków",
                                                   type="primary"):
                    prop_bar = st.progress(0)
                    prop_ph = st.empty()
                    for idx, sk in enumerate(missing_proposals):
                        prop_ph.info(f"⏳ Ulepszam {idx + 1}/{len(missing_proposals)}: {prompts_snap[sk]['step_name']}")
                        prop_bar.progress((idx + 1) / max(len(missing_proposals), 1))
                        prop = improve_prompt(
                            step_key=sk,
                            step_name=prompts_snap[sk]["step_name"],
                            system_prompt=prompts_snap[sk]["system"],
                            user_prompt=prompts_snap[sk]["user"],
                            evaluation=iter_data["evaluations"][sk],
                            provider=provider, model=model
                        )
                        iter_data["proposals"][sk] = {**prop, "approved": False}
                    prop_bar.empty()
                    prop_ph.empty()
                    st.success("✅ Propozycje wygenerowane!")
                    st.rerun()

                # Show proposals
                if iter_data["proposals"]:
                    st.markdown("---")
                    for sk in steps_needing_work:
                        if sk not in iter_data["proposals"]:
                            continue
                        prop = iter_data["proposals"][sk]
                        ev = iter_data["evaluations"].get(sk, {})
                        step_name = prompts_snap[sk]["step_name"]
                        approved = prop.get("approved", False)
                        icon = "✅" if approved else "⬜"

                        with st.expander(f"{icon} Krok: **{step_name}** (ocena: {ev.get('score', '?')}/10)",
                                         expanded=not approved):
                            if prop.get("changes_made"):
                                st.info("📝 Zmiany: " + " | ".join(prop["changes_made"]))
                            if prop.get("rationale"):
                                st.caption(f"Uzasadnienie: {prop['rationale']}")

                            pc1, pc2 = st.columns(2)
                            with pc1:
                                st.markdown("**PRZED (system prompt):**")
                                st.text_area("", value=prompts_snap[sk]["system"], height=300, disabled=True,
                                             key=f"sys_before_{sk}_{iter_data['number']}")
                            with pc2:
                                st.markdown("**PO (system prompt):**")
                                st.text_area("", value=prop.get("improved_system_prompt", ""), height=300,
                                             disabled=True, key=f"sys_after_{sk}_{iter_data['number']}")

                            with st.expander("Pokaż diff (system prompt)"):
                                diff = _make_diff(prompts_snap[sk]["system"],
                                                  prop.get("improved_system_prompt", ""))
                                st.code(diff, language="diff")

                            # Approve toggle
                            new_approved = st.checkbox(
                                f"☑ Zatwierdź ulepszenie dla '{step_name}'",
                                value=approved,
                                key=f"approve_{sk}_{iter_data['number']}"
                            )
                            prop["approved"] = new_approved

                    # Apply approved & create next iteration
                    approved_count = sum(1 for p in iter_data["proposals"].values() if p.get("approved"))
                    if approved_count > 0:
                        st.divider()
                        if st.button(f"✅ Zastosuj {approved_count} zatwierdzonych zmian → Utwórz Iterację {iter_data['number'] + 1}",
                                     type="primary", use_container_width=True):
                            # Build new prompts by applying approved proposals
                            new_prompts = {}
                            for sk, step_info in prompts_snap.items():
                                if sk in iter_data["proposals"] and iter_data["proposals"][sk].get("approved"):
                                    prop = iter_data["proposals"][sk]
                                    new_prompts[sk] = {
                                        **step_info,
                                        "system": prop.get("improved_system_prompt", step_info["system"]),
                                        "user": prop.get("improved_user_prompt", step_info["user"]),
                                    }
                                else:
                                    new_prompts[sk] = step_info

                            # Create new iteration placeholder (test not run yet)
                            new_iter = {
                                "number": iter_data["number"] + 1,
                                "prompts": new_prompts,
                                "outputs": {},
                                "evaluations": {},
                                "proposals": {},
                                "approved_keys": [],
                                "pending_test": True,
                            }
                            _lab()["iterations"].append(new_iter)
                            st.success(f"✅ Iteracja {new_iter['number']} przygotowana! "
                                       "Wróć do 'Konfiguracja testu' i uruchom pipeline z nowymi promptami.")
                            st.info("💡 Wskazówka: W zakładce 'Konfiguracja testu' kliknij ponownie 'Uruchom test' "
                                    "— użyje nowych, ulepszonych promptów z tej iteracji automatycznie.")
                            st.rerun()

    # =========================================================
    # TAB 4 — HISTORIA WERSJI
    # =========================================================
    with tab_history:
        iters = _lab()["iterations"]
        if not iters:
            st.info("ℹ️ Brak historii. Uruchom pierwszą iterację.")
        else:
            st.subheader("Historia iteracji")

            # Summary table
            rows = []
            for it in iters:
                evals = it.get("evaluations", {})
                scores = [e.get("score", 0) for e in evals.values() if isinstance(e, dict) and "score" in e]
                avg = f"{sum(scores)/len(scores):.1f}" if scores else "—"
                approved = sum(1 for p in it.get("proposals", {}).values() if p.get("approved"))
                pending = "⏳ Czeka na test" if it.get("pending_test") and not it.get("outputs") else "✅"
                rows.append({
                    "Iteracja": it["number"],
                    "Średnia ocena": avg,
                    "Ocenionych kroków": len(scores),
                    "Zatwierdzonych zmian": approved,
                    "Status": pending,
                })

            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.divider()

            # Version comparison
            if len(iters) >= 2:
                st.subheader("Porównaj dwie wersje")
                iter_labels = {it["number"]: f"Iteracja {it['number']}" for it in iters}
                hc1, hc2 = st.columns(2)
                ver_a = hc1.selectbox("Wersja A:", list(iter_labels.keys()),
                                      format_func=lambda x: iter_labels[x], key="hist_a")
                ver_b = hc2.selectbox("Wersja B:", list(iter_labels.keys()),
                                      index=len(iters) - 1,
                                      format_func=lambda x: iter_labels[x], key="hist_b")

                iter_a = next((it for it in iters if it["number"] == ver_a), None)
                iter_b = next((it for it in iters if it["number"] == ver_b), None)

                if iter_a and iter_b and ver_a != ver_b:
                    all_steps = list(iter_a["prompts"].keys())
                    for sk in all_steps:
                        pa = iter_a["prompts"].get(sk, {})
                        pb = iter_b["prompts"].get(sk, {})
                        sys_a = pa.get("system", "")
                        sys_b = pb.get("system", "")
                        if sys_a == sys_b:
                            continue  # No change, skip
                        with st.expander(f"📝 {pa.get('step_name', sk)}"):
                            diff = _make_diff(sys_a, sys_b)
                            st.code(diff, language="diff")
                else:
                    st.info("Wybierz dwie różne iteracje do porównania.")

            st.divider()
            # Export to JSON
            if st.button("📥 Eksportuj całą sesję do JSON"):
                export_data = {
                    "test_job": _lab()["test_job"],
                    "iterations": []
                }
                for it in iters:
                    export_data["iterations"].append({
                        "number": it["number"],
                        "prompts": {
                            sk: {"step_name": v["step_name"], "system": v["system"], "user": v["user"]}
                            for sk, v in it["prompts"].items()
                        },
                        "evaluations": it.get("evaluations", {}),
                    })
                st.download_button(
                    "⬇️ Pobierz session.json",
                    data=json.dumps(export_data, ensure_ascii=False, indent=2),
                    file_name="prompt_lab_session.json",
                    mime="application/json"
                )

            # Reset session
            st.divider()
            if st.button("🗑️ Resetuj sesję laboratorium", type="secondary"):
                st.session_state["prompt_lab"] = None
                _init_lab()
                st.success("Sesja zresetowana.")
                st.rerun()
