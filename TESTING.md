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

## Sekcja 3: Kampanie
- [ ] Przejdź do "Kampanie". 
- [ ] Utwórz nową kampanię, nadaj jej nazwę i parametry domyślne (np. Openrouter, EN).
- [ ] Edytuj opis kampanii z poziomu UI – sprawdź czy zmiany zapisują się w bazie i są natychmiast widoczne po przeładowaniu siatki.
- [ ] Zmień status kampanii na archiwalny. Otwórz moduł "Nowe Zadanie" i sprawdź, czy archiwalna kampania znika z głównej listy rozwijanej.

## Sekcja 4: Prompty
- [ ] Przejdź do "Prompty".
- [ ] W panelu z lewej strony rozwiń "Szablony Systemowe (Domyślne)". Jeśli jest ich 0, przejdź do Ustawień i kliknij "Zainicjuj domyślne prompty".
- [ ] Wybierz z prawej strony dowolną pustą (nowo utworzoną) kampanię.
- [ ] Użyj przycisku klonowania, aby skopiować zestaw domyślny na poczet tej kampanii.
- [ ] Wyedytuj "User Prompt" w dowolnym kroku w kampanii, zapisz i upewnij się, że zmiana dotyczy *tylko* tej kampanii (domyślne szablony w bazie pozostają czyste).

## Sekcja 5: Nowe zadanie
- [ ] Wejdź w "Nowe zadanie". Sprawdź komunikaty ostrzegawcze, gdy nie wybierzesz kampanii z lewego menu, lub kampania nie ma przypisanych promptów roboczych.
- [ ] Uzupełnij formularz wpisując frazę główną i spróbuj zapisać jako "Draft" – po zapisie zadanie NIE powinno wejść w stan gotowości.
- [ ] Ponów próbę z nową frazą, i zapisz je jako "Dodaj do kolejki".

## Sekcja 6: Kolejka
- [ ] Wejdź w zakładkę "Kolejka".
- [ ] Odnajdź utworzone wcześniej zadanie Draft i użyj przycisku by oznaczyć je jako `queued`.
- [ ] Zweryfikuj, czy zadanie płynnie przeniosło się w górę, do sekcji "Gotowe do przetworzenia".
- [ ] W "Przetwarzanie partii" zaznacz przetworzenie 1 sztuki, uruchom pętlę i obserwuj progres. Upewnij się, że w podglądzie (na dole ekranu) poszczególne checkboxy (kroki) powoli oznaczają się na zielono.

## Sekcja 7: AI
- [ ] Uszkódź celowo `OPENAI_API_KEY` w swoim pliku secrets i spróbuj puścić partię (Batch). 
- [ ] System zamiast krwawego Crashu, musi oflagować zadanie statusem `failed`, a pętla powinna bez problemu przejść do kolejnego zadania.
- [ ] Ustaw "Target length" w zadaniu na olbrzymią wartość, a limit tokenów na bardzo mały, by model sprowokował dziwne zwrócenie danych. Upewnij się, że ostateczny błąd zapisał się w zakładce Wyniki i Dashboard.

## Sekcja 8: Wyniki i QA SEO
- [ ] Wejdź do zakładki "Wyniki". Zmień pole filtru z `completed` na `all` albo wklep fragment Słowa Kluczowego w Wyszukiwarkę, żeby złapać przetestowany rekord.
- [ ] Wejdź w sekcję HTML i wykonaj ręczną edycję finalnego tekstu, dodając literówkę do meta title. Kliknij przycisk zapisu i zweryfikuj czy dane w bazie również się zaktualizowały.
- [ ] Przejdź na trzecią zakładkę w wynikach ("Historia"). Sprawdź tabelę "QA Regułowe" – czy poprawnie obliczyła liczbę zrzuconych znaków? Czy zauważyła wszystkie wstawione nagłówki H2? 

## Sekcja 9: Import XLSX
- [ ] Wejdź w moduł "Import XLSX" i kliknij duży guzik do pobrania Szablonu.
- [ ] Wypełnij go lokalnie w Excelu: dodaj 3 poprawne wiersze, 1 wiersz bez frazy głównej i 1 wiersz z błędnie sformułowaną docelową długością (np. z literami).
- [ ] Wgraj plik do aplikacji.
- [ ] System MUSI wychwycić błędy – przejrzyj czerwoną zakładkę blokad. 
- [ ] Zaakceptuj czyste wiersze za pomocą dolnego guzika – upewnij się, że pasek postępu płynnie dojechał do 100%.

## Sekcja 10: Eksport XLSX
- [ ] Przejdź do modułu "Eksport". Ustaw filtry na status `completed`.
- [ ] Opcjonalnie zmniejsz datę od-do. Kliknij "Generuj XLSX".
- [ ] Otwórz pobrany plik na dysku. Powinien zawierać u dołu kilka posegregowanych zakładek (final_contents, meta, faq, steps, errors). Górny wiersz z nazwami powinien być zamrożony.
- [ ] Wróć do aplikacji, na samą górę modułu, wejdź w zakładkę "Historia Pobierań". Znajdź tam własny wygenerowany plik i rozwiń JSONa z logami filtrów, by upewnić się co do celów audytowych.

## Sekcja 11: Przypadki błędów (Timeout Recovery)
- [ ] Posiadając zadania w kolejce, zmień im z poziomu panelu Supabase status na `processing` (aby symulować zombie tasks z "zawieszonymi" instancjami) oraz obniż ich `updated_at` o co najmniej 2-3 godziny wstecz.
- [ ] Kliknij Dashboard i zaobserwuj, czy pętla systemowa (Heartbeat) wykryła problematyczne rekordy, zamieniła ich status na `interrupted` i odpaliła żółto-czerwony baner ostrzegawczy.
- [ ] Użyj przycisku przywracania z banneru, by cofnąć uszkodzone rekordy na bezpieczny status gotowości.

## Sekcja 12: Test przed wdrożeniem na Streamlit Community Cloud
- Zawsze upewnij się, że nie importujesz lokalnych (Windowsowych) ścieżek `C:\` oraz nie tworzysz stałych plików w trakcie pracy – aplikacje chmurowe są "bezstanowe". Wszystko, co generujesz w locie musi lecieć z pamięci (dlatego Export i Import korzysta z `io.BytesIO`).
- Upewnij się, że w `requirements.txt` figurują dokładnie `pandas`, `openpyxl`, `beautifulsoup4`, `openai` oraz `supabase`.
- Po wdrożeniu poproś kilku współpracowników o jednoczesne wejście w kolejkę. Ze względu na zjawisko Rate Limits darmowego chmurowego środowiska mogą wystąpić rzadsze aktualizacje stanu pasków postępu.
