# Checklista Testów Manualnych MVP

Pełny plan weryfikacji aplikacji przed oddaniem jej pierwszemu zespołowi i publikacją na środowisku produkcyjnym (Streamlit Community Cloud).

## Sekcja 1: Logowanie
- [ ] Wejdź na stronę główną (bez zalogowania system nie pozwala wejść w żaden inny moduł).
- [ ] Wpisz błędne hasło (z `secrets.toml`) – sprawdź czy wyświetla się czytelny komunikat błędu.
- [ ] Wpisz poprawne hasło – sprawdź czy odblokowuje się pole wyboru Operatora.
- [ ] Zmień Operatora z domyślnego na innego z listy, kliknij "Zatwierdź" – powinieneś wylądować w aplikacji, a na pasku bocznym powinno widnieć "Zalogowano jako: ...".

## Sekcja 2: Supabase (Puste Stany)
- [ ] Upewnij się, że odłączenie sieci nie wywala czerwonego ekranu, a zwraca na Dashboardzie błąd o braku połączenia.
- [ ] Przejdź do zakładki "Ustawienia".
- [ ] Upewnij się, że w sekcji "Diagnostyka połączeń" status bazy świeci na zielono.

## Sekcja 3: Pierwsze generowanie treści od zera
**Checklist testu "End-to-End" generowania:**
1. Sprawdź secrets (`.streamlit/secrets.toml`).
2. Sprawdź połączenie z Supabase (Ustawienia -> Diagnostyka).
3. Sprawdź klucze OpenAI/OpenRouter (Ustawienia -> Zmienne Środowiskowe).
4. Utwórz kampanię testową:
   - **Nazwa:** Test SEO content
5. Uzupełnij strategię treści dla nowej kampanii:
   - **Grupa docelowa:** osoby, które chcą kupić materac online, ale nie wiedzą, jaki typ i twardość wybrać
   - **Cel treści:** pomóc użytkownikowi wybrać odpowiedni materac i przejść do kategorii produktów
   - **CTA:** sprawdź dostępne materace w naszym sklepie
   - **Ton:** ekspercki, prosty, pomocny, bez nachalnej sprzedaży
6. Skopiuj domyślne prompty (Zakładka Prompty -> Przywróć z domyślnych v3).
7. Utwórz jedno zadanie testowe (Zakładka Nowe zadanie):
   - **Typ treści:** `blog_post`
   - **Język:** `pl`
   - **Locale:** `pl-PL`
   - **Fraza główna:** `jak wybrać materac do spania`
   - **Frazy dodatkowe:** `materac piankowy`, `materac sprężynowy`, `twardość materaca`, `materac dla pary`, `materac na ból pleców`
   - **Długość:** `5000`
   - **Dodatkowe uwagi:** `Nie strasz użytkownika. Pisz konkretnie. Nie używaj medycznych obietnic. Zadbaj o naturalne porównanie typów materacy.`
8. Sprawdź snapshot promptów w szczegółach zapisanego zadania (w Kolejce kliknij nazwę zadania i wejdź w Logi / Prompty).
9. W zakładce "Kolejka", rozwiń zapisane zadanie i kliknij przycisk **"🧪 Test generowania"**.
10. Sprawdź na bieżąco każdy etap w logach widocznych podczas testu.
11. Przejdź do zakładki "Wyniki" i sprawdź wygenerowany `final_html`.
12. Sprawdź, czy `meta_title` ma odpowiednią formę i długość.
13. Sprawdź `meta_description`.
14. Sprawdź `FAQ` pod kątem czystego kodu HTML (h2, h3, p).
15. Sprawdź SEO QA (zakładka "Historia i logi AI").
16. Sprawdź Attractiveness QA (zakładka "Skuteczność (Atrakcyjność)").
17. Sprawdź eksport XLSX (moduł Eksport).
18. Sprawdź ponowienie błędnego zadania (zmień ręcznie status na 'failed' w bazie i kliknij przycisk "Ponów" w Kolejce).
19. Sprawdź wyłączenie jednego etapu (wyłącz krok w zakładce Prompty, uruchom kolejne zadanie i sprawdź czy ma status "skipped").
20. Sprawdź batch 5 zadań na raz.

## Sekcja 4: Wyniki i Skuteczność Tekstu
- [ ] Wejdź do zakładki "Wyniki". Zmień pole filtru z `completed` na `all` albo wklep fragment Słowa Kluczowego w Wyszukiwarkę, żeby złapać przetestowany rekord.
- [ ] Wejdź w sekcję HTML i wykonaj ręczną edycję finalnego tekstu, dodając literówkę do meta title. Kliknij przycisk zapisu i zweryfikuj czy dane w bazie również się zaktualizowały.
- [ ] Przejdź na zakładkę "Skuteczność (Atrakcyjność)". 
- [ ] Zweryfikuj, czy pojawiła się Ogólna ocena AI (np. 8/10) oraz czy system poprawnie odczytał Reguły Marketingowe (np. wykrył Call To Action).
- [ ] Przejdź na zakładkę "Historia i Logi AI". Sprawdź tabelę "QA Regułowe" – czy poprawnie obliczyła liczbę zrzuconych znaków? Czy zauważyła wszystkie wstawione nagłówki H2? 

## Sekcja 5: Import XLSX
- [ ] Wejdź w moduł "Import XLSX" i kliknij duży guzik do pobrania Szablonu.
- [ ] Wypełnij go lokalnie w Excelu: dodaj 3 poprawne wiersze, 1 wiersz bez frazy głównej i 1 wiersz z błędnie sformułowaną docelową długością (np. z literami).
- [ ] Wgraj plik do aplikacji.
- [ ] System MUSI wychwycić błędy – przejrzyj czerwoną zakładkę blokad. 
- [ ] Zaakceptuj czyste wiersze za pomocą dolnego guzika – upewnij się, że pasek postępu płynnie dojechał do 100%.

## Sekcja 6: Eksport XLSX
- [ ] Przejdź do modułu "Eksport". Ustaw filtry na status `completed`.
- [ ] Opcjonalnie zmniejsz datę od-do. Kliknij "Generuj XLSX".
- [ ] Otwórz pobrany plik na dysku. Powinien zawierać u dołu kilka posegregowanych zakładek (final_contents, meta, faq, seo_qa, attractiveness_qa, steps, errors). Górny wiersz z nazwami powinien być zamrożony.
- [ ] Wróć do aplikacji, na samą górę modułu, wejdź w zakładkę "Historia Pobierań". Znajdź tam własny wygenerowany plik i rozwiń JSONa z logami filtrów, by upewnić się co do celów audytowych.

## Sekcja 7: Przypadki błędów (Timeout Recovery)
- [ ] Posiadając zadania w kolejce, zmień im z poziomu panelu Supabase status na `processing` (aby symulować zombie tasks z "zawieszonymi" instancjami) oraz obniż ich `updated_at` o co najmniej 2-3 godziny wstecz.
- [ ] Kliknij Dashboard i zaobserwuj, czy pętla systemowa (Heartbeat) wykryła problematyczne rekordy, zamieniła ich status na `interrupted` i odpaliła żółto-czerwony baner ostrzegawczy.
- [ ] Użyj przycisku przywracania z banneru, by cofnąć uszkodzone rekordy na bezpieczny status gotowości.

## Sekcja 8: Test przed wdrożeniem na Streamlit Community Cloud
- Zawsze upewnij się, że nie importujesz lokalnych (Windowsowych) ścieżek `C:\` oraz nie tworzysz stałych plików w trakcie pracy – aplikacje chmurowe są "bezstanowe". Wszystko, co generujesz w locie musi lecieć z pamięci (dlatego Export i Import korzysta z `io.BytesIO`).
- Upewnij się, że w `requirements.txt` figurują dokładnie `pandas`, `openpyxl`, `beautifulsoup4`, `openai` oraz `supabase`.
- Po wdrożeniu poproś kilku współpracowników o jednoczesne wejście w kolejkę. Ze względu na zjawisko Rate Limits darmowego chmurowego środowiska mogą wystąpić rzadsze aktualizacje stanu pasków postępu.

## Sekcja 9: Testy odporności aplikacji (Error Handling)
**Checklista negatywna (Crash-testy):**
- [ ] Zmień celowo nazwę zmiennej `SUPABASE_URL` w `.streamlit/secrets.toml` i odśwież stronę. **Oczekiwane:** UI wyświetli czerwony komunikat o braku wymaganych sekretów i bezpiecznie zatrzyma działanie (bez długiego tracebacka).
- [ ] Zmień klucz API `OPENAI_API_KEY` na niepoprawny i uruchom zadanie. **Oczekiwane:** Etap AI w zadaniu zwróci błąd w logach: "Nieprawidłowy klucz API (Błąd 401)", a następnie zadanie oznaczy się jako `failed`.
- [ ] Wymuś błąd modelu (np. wybierz nieistniejący model `gpt-10` w ustawieniach). **Oczekiwane:** Błąd 404 w logach z czytelnym wyjaśnieniem, proces nie wysypie aplikacji, lecz zakończy to jedno zadanie błędem.
- [ ] Wykonaj wdrożenie zepsutego pliku XLSX (pustego) do modułu "Import". **Oczekiwane:** Ostrzeżenie "Plik Excel jest pusty", bez wrzucania "pustych" wartości do bazy.
- [ ] Stwórz duplikaty tych samych fraz kluczowych w importowanym pliku XLSX. **Oczekiwane:** Wypisze błędy w czerwonej tabelce "Duplikat frazy 'main_keyword'", nie importując zepsutych wierszy.
- [ ] Wyeksportuj zadania z bardzo długą tabelą (symulacja limitów Excela). **Oczekiwane:** Arkusze eksportują się poprawnie, a zbyt długie teksty (>32700 znaków) są bezpiecznie obcinane z adnotacją.
- [ ] Uruchom batch (np. 5 zadań), podczas którego jednemu z nich wpiszesz ręcznie w bazi status błędu lub wywołasz timeout. **Oczekiwane:** Pętla nie przerwie generowania kolejnych 4 zadań, a na koniec zwróci "Sukcesy: 4, Błędy: 1".
- [ ] Sprawdź raport błędu AI w tabeli `content_job_steps` po wygenerowaniu uszkodzonego markupa Markdown przez AI (```html...). **Oczekiwane:** Finalny HTML w bazie zostanie pomyślnie oczyszczony, a w tabeli z zadaniem pojawi się `error_message` z dopiskiem "[HTML WARNING] Wykryto i usunięto bloki markdown...".
