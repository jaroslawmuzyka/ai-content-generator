# Przewodnik Tworzenia Promptów (Prompting Guide)

W systemie obowiązuje jeden, spójny i wysoce czytelny format tworzenia szablonów systemowych dla AI.
Wszystkie nowo tworzone prompty lub edytowane w kampaniach powinny przestrzegać poniższej struktury:

## Struktura Promptu

### System Prompt
Każdy System Prompt musi składać się z następujących sekcji (oznaczonych nagłówkami H1 z użyciem `#`):

1. **# Rola**
Jasne określenie roli, w którą ma wcielić się asystent (np. *Jesteś ekspertem SEO...*).

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

### User Prompt
Powinien zawierać czyste dane opakowane w tagi stylizowane na XML, wewnątrz których system automatycznie podmieni wartości (zmienne).

**Przykładowy szkielet User Promptu:**
```
<język>
{{language}}
</język>

<lokalizacja>
{{locale}}
</lokalizacja>

<typ_treści>
{{content_type}}
</typ_treści>

<fraza_główna>
{{main_keyword}}
</fraza_główna>
```

## Dostępne zmienne

System potrafi automatycznie przetwarzać poniższe zmienne. Jeśli jakiejś brakuje w danym zleceniu, zostanie zastąpiona pustym ciągiem, by zapobiec błędom:

### Dane z zadania:
`{{language}}`, `{{locale}}`, `{{content_type}}`, `{{main_keyword}}`, `{{secondary_keywords}}`, `{{target_length}}`, `{{current_content}}`, `{{additional_notes}}`, `{{url}}`, `{{is_existing_url}}`

### Kontekst dynamiczny / Zewnętrzny:
`{{knowledge}}`, `{{knowledge_graph}}`, `{{example_headings}}`, `{{headings}}` (Wszystkie nagłówki z etapu zarysu), `{{heading}}` (Używany w pętli dla pojedynczej sekcji), `{{already_written_part}}` (Wynik sklejony z dotychczasowych kroków), `{{current_step_output}}` (Wynik bezpośrenio z poprzedniego kroku), `{{context}}`, `{{previous_steps}}` (Słownik JSON wszystkich kroków)

### Dane strategiczne (z modułu Atrakcyjności):
`{{brand_description}}`, `{{target_audience}}`, `{{persona}}`, `{{consumer_insight}}`, `{{customer_language}}`, `{{main_pain_points}}`, `{{main_desires}}`, `{{decision_triggers}}`, `{{brand_tone}}`, `{{brand_archetype}}`, `{{forbidden_phrases}}`, `{{required_phrases}}`, `{{value_proposition}}`, `{{proof_points}}`, `{{call_to_action}}`, `{{content_goal}}`

## Dobre praktyki
1. Zawsze wymuszaj na modelu pisanie w określonym języku dodając na końcu reguły `Wynik wygeneruj w języku wskazanym w polu <język>`. W ten sposób wszystkie prompty systemowe piszemy w 100% po polsku.
2. Zmienne wielowyrazowe zawsze opakowuj w tagi typu `<fraza_główna>{{main_keyword}}</fraza_główna>`.
3. Jeśli dany prompt musi zwrócić ustrukturyzowane dane na potrzeby aplikacji, poproś o kod JSON w oparciu o dokładny klucz-wartość w sekcji "Format odpowiedzi".
