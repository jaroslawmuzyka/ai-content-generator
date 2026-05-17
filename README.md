# AI Content Generator

Aplikacja webowa w Streamlit do wewnętrznego, masowego generowania treści SEO z użyciem modeli AI (OpenAI/OpenRouter). Aplikacja opiera się na zewnętrznej relacyjnej bazie Supabase, co rozwiązuje problem ulotności danych na darmowych hostingach. Posiada wbudowaną kolejkę zadań, QA SEO (liczenie znaków, fraz) oraz QA atrakcyjności marketingowej tekstu.

---

## 1. Konfiguracja Secrets

Aplikacja wymaga pliku `.streamlit/secrets.toml` w głównym folderze (dla środowiska lokalnego) lub ustawienia zmiennych **Secrets** w panelu chmury Streamlit. 

```toml
# Hasło główne blokujące dostęp do UI
APP_PASSWORD = "moje_trudne_haslo"

# Lista dostępnych operatorów (nazw własnych pracowników)
OPERATORS = ["Anna", "Jan", "System"]

# Parametry dostępowe Supabase (Wymagane)
SUPABASE_URL = "https://xxxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Klucze API dostawców (Przynajmniej jeden jest wymagany do generowania)
OPENAI_API_KEY = "sk-proj-..."
OPENROUTER_API_KEY = "sk-or-v1-..."
```

---

## 2. Supabase Schema (Struktura Bazy)

W katalogu `db/schema.sql` znajduje się pełny zrzut struktury tabel bazy danych. Przed pierwszym użyciem musisz go wdrożyć do panelu "SQL Editor" w nowym projekcie Supabase.
Baza składa się z:
- `campaigns` - Definiuje grupy/paczki zadań.
- `campaign_content_strategy` - Przechowuje globalne reguły marketingowe, personę i cele.
- `prompt_sets` / `prompt_steps` - Hierarchiczne zestawy promptów instruktażowych (Domyślne Systemowe vs Per Kampania).
- `content_jobs` - Główny obiekt pojedynczego wygenerowanego tekstu (przechowuje finalny HTML, Meta Tagi, Status zadania).
- `content_job_steps` - Poszczególne logi API zapisywane w trakcie iteracyjnego generowania konkretnego zadania.
- `job_prompt_snapshots` - "Zrzuty" (Snapshoty) promptów przypięte historycznie do momentu uruchomienia konkretnego zadania.
- `exports` - Historia wyeksportowanych paczek w XLSX.

---

## 3. Zasilanie (Seed) Promptów Systemowych

Aby aplikacja potrafiła cokolwiek wygenerować na nowej bazie danych, musisz zasilić tabelę promptów domyślnych (tzw. bazę wiedzy AI aplikacji).

1. Uruchom aplikację.
2. Zaloguj się poprawnym hasłem.
3. Przejdź do lewego menu: **Ustawienia**.
4. W sekcji "Zarządzanie bazą danych" kliknij przycisk **"Zainicjuj Domyślne Prompty"**.
System pobierze zawartość sztywnych plików `prompt_templates_pX.py` z kodu i wrzuci je bezpiecznie w formacie JSON do Supabase.

---

## 4. Ograniczenia darmowego Streamlit Community Cloud

Aplikacja jest przystosowana pod darmowe środowisko Streamlita, jednak posiada architektoniczne ograniczenia:
1. **Brak procesów w tle:** Na darmowym serwerze Streamlit kod nie może kontynuować działania po zamknięciu karty w przeglądarce. Pasek ładowania na ekranie "Kolejki" **musi być cały czas na widoku**.
2. **Timeout sieciowy (504):** Jeśli uruchomisz partię 500 zadań bez przerwy z wolnym modelem (np. Opus), Streamlit może ubić proces z powodu przekroczenia czasu ładowania widoku (Network Timeout). **Zalecamy przetwarzanie małych paczek (10-20 zadań jednocześnie).**
3. Jeśli proces "zamrozi" się i wyjdziesz z karty, zadanie zostaje jako `processing`. System w zakładce Panel główny posiada automatyczny wykrywacz takich "zombie zadań" i pozwoli na ich zrestartowanie po upływie godziny.

---

## 5. Uruchomienie lokalne

1. Utwórz wirtualne środowisko: `python -m venv venv`
2. Aktywuj środowisko: `venv\Scripts\activate` (Windows)
3. Zainstaluj biblioteki: `pip install -r requirements.txt`
4. Utwórz plik `secrets.toml`: `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`
5. Wpisz poprawne klucze API i Supabase w wyżej wymienionym pliku.
6. Uruchom platformę wpisując w terminalu: `streamlit run app.py`

---

## 6. Deployment Streamlit

Aby wdrożyć narzędzie dla swojego zespołu publicznie (Community Cloud):
1. Umieść kod aplikacji we własnym repozytorium GitHub (ukrywając w `.gitignore` pliki z katalogu `.streamlit/`).
2. Wejdź na [share.streamlit.io](https://share.streamlit.io/) i podepnij to repozytorium.
3. Wskaż `app.py` jako plik wejściowy.
4. **ZANIM KLIKNIESZ DEPLOY:** Rozwiń z dołu sekcję *Advanced Settings -> Secrets* i wklej surowy tekst odpowiadający formatowi z `.streamlit/secrets.toml.example` uzupełniony Twoimi autentycznymi kluczami.
5. Deploy.

---

## 7. Pierwszy test generowania

Zanim przekażesz aplikację copywriterom, przeprowadź test end-to-end:
1. Zaloguj się, przejdź do zakładki **Kampanie** i stwórz nową (np. "Wiosenna Wyprzedaż").
2. Wejdź w **Prompty** i kliknij w duży niebieski przycisk po prawej ("Skopiuj do tej kampanii"), by kampania otrzymała systemowe instrukcje pisania od AI.
3. Wejdź w **Nowa treść** i uzupełnij tylko główne słowo kluczowe: "kurtki wiosenne". Zjedź na dół, zaznacz tryb szybkiego generowania i zatwierdź **"Dodaj do Kolejki"**.
4. Idź do **Kolejka generowania**, znajdź swoje zadanie i kliknij uruchom partię 1 zadania. Zaczekaj aż pasek postępu dojdzie do 100%.
5. Sprawdź treść w zakładce **Wyniki treści** i jeśli tekst jest poprawny — zadanie zakończone, system stoi stabilnie!
