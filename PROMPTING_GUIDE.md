# Przewodnik Tworzenia Promptów (Prompting Guide)

W systemie obowiązuje jeden, spójny i wysoce czytelny format tworzenia szablonów systemowych dla AI.
Wszystkie nowo tworzone prompty lub edytowane w kampaniach powinny przestrzegać poniższej struktury:

## Struktura Promptu

### System Prompt
Każdy System Prompt musi składać się z następujących sekcji (oznaczonych nagłówkami H1 z użyciem `#`):

1. **# Rola**
Jasne określenie roli, w którą ma wcielić się asystent (np. *Jesteś ekspertem SEO i analitykiem zachowań konsumentów...*).

2. **# Główny cel**
Krótki opis zadania w tym konkretnym etapie (np. *Twoim zadaniem jest stworzyć strukturę nagłówków...*).

3. **# Dane wejściowe**
Lista tagów XML-like, które model otrzyma w User Prompcie (np. *Otrzymasz dane w tagach: <fraza_główna>...*).

4. **# Proces działania**
Przedstawienie sekwencji kroków, krok po kroku (najlepiej w postaci numerycznej lub jasnych bulletów). 

5. **# Zasady**
Listy pozytywnych instrukcji (np. *Używaj naturalnego języka*).

6. **# Zakazy**
Wyraźna lista rzeczy zakazanych, rozpoczynająca się sformułowaniem "Nie wolno:" (np. *Nie wymyślaj faktów*).

7. **# Format odpowiedzi**
Określenie typu zwracanego formatu (np. HTML, zwykły tekst, JSON).

8. **# Kontrola końcowa**
Checklista samokontroli dla AI przed odesłaniem odpowiedzi (np. *Przed zwróceniem odpowiedzi sprawdź, czy: ...*).

---

## Jak pisać dobre prompty w tym narzędziu

1. **Język promptów systemowych:** Prompty domyślne są zawsze pisane po polsku dla wygody edycji przez zespół. Aby model wygenerował treść w docelowym języku (np. po niemiecku), używamy instrukcji w `system_prompt`:
   > *Wynik wygeneruj w języku wskazanym w tagu <język>.*
2. **Krótko i na temat:** Zamiast długich esejów stosuj jasne punkty (bullets). AI lepiej czyta struktury list i tagów.
3. **XML-like tags dla User Promptu:** Przekazując zmienne w User Prompcie, ZAWSZE otaczaj je odpowiednimi tagami z polskimi nazwami (np. `<język>`, `<lokalizacja>`, `<fraza_główna>`). Dzięki temu model wyraźnie oddziela instrukcję (system prompt) od analizowanych danych (user prompt).

**Przykład idealnego System Promptu:**
```markdown
# Rola
Jesteś doświadczonym SEO Copywriterem.

# Główny cel
Napisz angażujący tag meta title.

# Dane wejściowe
<język>
<fraza_główna>

# Zasady
- Wynik wygeneruj w języku wskazanym w <język>.
- Używaj silnych czasowników.

# Format odpowiedzi
Zwróć wyłącznie sam tekst, bez tagów HTML.
```

**Przykład idealnego User Promptu:**
```xml
<język>
{{language}}
</język>

<fraza_główna>
{{main_keyword}}
</fraza_główna>
```

---

## Lista zakazanych fraz generycznych

Aby unikać tzw. "AI slangu" i pisania lania wody, System Prompty powinny często zabraniać używania pustych stwierdzeń. Przykładowa (i polecana) lista zakazanych zwrotów to m.in.:
- w dzisiejszych czasach
- warto zwrócić uwagę
- szeroki wybór / bogaty asortyment
- wysoka jakość
- idealne rozwiązanie
- dopasowane do potrzeb
- profesjonalne podejście
- kompleksowa oferta
- dynamicznie rozwijający się
- innowacyjne rozwiązania
- kluczowe znaczenie
- na koniec / podsumowując

Zamiast tych słów, wymuszaj na modelu stosowanie konkretnych danych, cech lub jasnych korzyści funkcyjnych i emocjonalnych.

---

## Dostępne zmienne w aplikacji

Aplikacja dynamicznie podstawia pod poniższe zmienne konkretne wartości z bazy lub wyników poprzednich etapów.

### Podstawowe zlecenia (Zadania):
- `{{language}}` — Kod języka lub nazwa (np. pl)
- `{{locale}}` — Opcjonalna lokalizacja (np. pl-PL)
- `{{content_type}}` — Typ treści (np. blog_post)
- `{{main_keyword}}` — Główna fraza
- `{{secondary_keywords}}` — Poboczne frazy
- `{{target_length}}` — Docelowa długość tekstu
- `{{current_content}}` — Istniejąca treść do poprawy
- `{{additional_notes}}` — Dodatkowe notatki
- `{{url}}` — Docelowy adres URL
- `{{is_existing_url}}` — (true/false)

### Zmienne Dynamiczne (Pipeline AI):
- `{{knowledge}}` — Dodatkowa wiedza RAG (jeśli zdefiniowana)
- `{{knowledge_graph}}` — Ekstrakcja powiązań (z Senuto/zewnętrznych)
- `{{example_headings}}` — Przykładowe nagłówki
- `{{headings}}` — Wszystkie nagłówki wygenerowane w etapie zarysu (Outline)
- `{{heading}}` — Bieżący nagłówek (używany wyłącznie w iteracyjnym etapie pisania sekcji - `seo_section_writer`)
- `{{already_written_part}}` — Ostatnie 3000 znaków wygenerowanego już tekstu (dla kontekstu w sekcjach)
- `{{current_step_output}}` — Wynik poprzedniego etapu
- `{{context}}` — Dodatkowy kontekst do sekcji
- `{{final_html}}` — Końcowy, wyczyszczony kod HTML całego tekstu (używany m.in. na etapie generowania FAQ, meta tagów oraz systemów QA)
- `{{previous_steps}}` — Zbiorczy "dump" wyników z poprzednich kroków, używany w analizach wieloetapowych

### Strategia Kampanii (Moduł Atrakcyjności):
- `{{brand_description}}` — Opis marki
- `{{target_audience}}` — Grupa docelowa (nadpisywana przez poziom zadania, jeśli określona)
- `{{persona}}` — Persona docelowa
- `{{consumer_insight}}` — Ukryte motywacje / Insight
- `{{customer_language}}` — Sposób mówienia odbiorcy
- `{{main_pain_points}}` — Bóle klienta
- `{{main_desires}}` — Pragnienia klienta
- `{{decision_triggers}}` — Wyzwalacze decyzji zakupowych
- `{{brand_tone}}` — Ton głosu marki
- `{{brand_archetype}}` — Archetyp marki
- `{{forbidden_phrases}}` — Zakazane zwroty klienta
- `{{required_phrases}}` — Wymagane zwroty klienta
- `{{value_proposition}}` — Unikalna propozycja wartości
- `{{proof_points}}` — Argumenty uwiarygadniające / RTB
- `{{call_to_action}}` — Główny wzywacz do działania (CTA)
- `{{content_goal}}` — Cel biznesowy publikacji

---

## Podsumowanie dobrych praktyk
1. Mów dokładnie co model MA zrobić, i co mu ZABRONIONE ("Nie wolno: ...").
2. Nie zostawiaj w `system_prompt` zmiennych, przenieś wszystkie zmienne (`{{zmienna}}`) do `user_prompt` i opakuj tagami.
3. Gdy aktualizujesz domyślne prompty przez panel narzędzia (dla danej kampanii), upewnij się, że zachowujesz spójność używanych zmiennych ze zmiennymi dostępnymi na danym kroku pipeline'u.
