import streamlit as st
import time
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError
from utils.constants import DEFAULT_MODELS

def get_ai_client(provider):
    """
    Zwraca odpowiednio skonfigurowanego klienta kompatybilnego z biblioteką OpenAI.
    Zwraca krotkę: (klient, None) w przypadku sukcesu, lub (None, 'komunikat błędu') przy niepowodzeniu.
    """
    if provider == "openai":
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            return None, "Brak klucza OPENAI_API_KEY w pliku .streamlit/secrets.toml. Skonfiguruj go, aby używać modeli OpenAI."
        # Standardowy klient OpenAI
        return OpenAI(api_key=api_key), None
        
    elif provider == "openrouter":
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        if not api_key:
            return None, "Brak klucza OPENROUTER_API_KEY w pliku .streamlit/secrets.toml. Skonfiguruj go, aby używać modeli OpenRouter."
        
        # OpenRouter używa w pełni kompatybilnego API z OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        return client, None
        
    return None, f"Nieznany provider AI: '{provider}'."


def generate_ai_response(provider, model, system_prompt, user_prompt, temperature=0.7, max_tokens=None, retries=2):
    """
    Ustandaryzowany punkt wejścia do generowania treści przez modele AI.
    Ukrywa logikę bibliotek oraz radzi sobie z typowymi błędami (timeout, rate limit).
    
    Zwraca słownik o ujednoliconej strukturze:
    {
        "success": bool,
        "text": str (tylko gdy success == True),
        "input_tokens": int lub None,
        "output_tokens": int lub None,
        "error": str (tylko gdy success == False)
    }
    """
    result = {
        "success": False,
        "text": None,
        "input_tokens": None,
        "output_tokens": None,
        "error": None
    }
    
    if not provider:
        result["error"] = "Nie przekazano nazwy providera API."
        return result
        
    client, err_msg = get_ai_client(provider)
    if not client:
        result["error"] = err_msg
        return result
        
    # Dobór bezpiecznego modelu domyślnego, gdyby podano pustą wartość
    if not model:
        model = DEFAULT_MODELS.get(provider)
        if not model:
            result["error"] = f"Brak domyślnego modelu dla providera: {provider}."
            return result

    # Kompilacja struktury wiadomości
    messages = []
    if system_prompt and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    
    if not user_prompt or not user_prompt.strip():
        result["error"] = "Polecenie (user_prompt) nie może być puste."
        return result
        
    messages.append({"role": "user", "content": user_prompt.strip()})

    # Przygotowanie pakietu parametrów
    kwargs = {
        "model": model,
        "messages": messages,
    }
    
    if "gpt-5.4-mini" in model or "o1" in model or "o3" in model:
        # Te modele nie obsługują parametru temperature, lub wymagają 1. 
        # API OpenAI (np. o3-mini) obsługuje reasoning_effort
        kwargs["reasoning_effort"] = "low"
    else:
        kwargs["temperature"] = temperature
    if max_tokens:
        if "gpt-5" in model or "o1" in model or "o3" in model:
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
        
    # OpenRouter wymaga dodatkowych nagłówków identyfikujących w celu zliczania statystyk
    if provider == "openrouter":
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://localhost", 
            "X-Title": "AI Content Generator (Streamlit)",
        }

    # Mechanizm Retry z Backoffem na wypadek problemów sieciowych i blokad rate limit
    for attempt in range(retries + 1):
        try:
            # Synchroniczne żądanie do API
            response = client.chat.completions.create(
                timeout=90, # 90 sekund limitu na długie generowanie artykułów SEO
                **kwargs
            )
            
            # Ekstrakcja danych
            text = response.choices[0].message.content
            if not text or not text.strip():
                result["error"] = "Dostawca API zwrócił pustą odpowiedź."
                return result
                
            result["text"] = text
            result["success"] = True
            
            # W zależności od modelu i providera metadane użycia mogą (rzadko) nie istnieć
            if hasattr(response, 'usage') and response.usage:
                result["input_tokens"] = getattr(response.usage, 'prompt_tokens', None)
                result["output_tokens"] = getattr(response.usage, 'completion_tokens', None)
                
            return result
            
        except RateLimitError as e:
            error_msg = f"API odrzuciło zapytanie: Zbyt wiele zapytań (Rate Limit). Detale: {str(e)}"
            if attempt < retries:
                time.sleep((attempt + 1) * 3) # Czekamy i ponawiamy (exponential backoff)
                continue
            result["error"] = error_msg
            
        except APIConnectionError as e:
            error_msg = f"Brak stabilnego połączenia internetowego z serwerem dostawcy ({provider}). Detale: {str(e)}"
            if attempt < retries:
                time.sleep((attempt + 1) * 2)
                continue
            result["error"] = error_msg
            
        except APIStatusError as e:
            # To zazwyczaj błąd 400 (Bad Request) - zły model, token przekroczony itp. lub 500
            error_msg = f"Serwer API zgłosił błąd [Status {e.status_code}]: {str(e)}"
            if e.status_code == 401:
                error_msg = "Nieprawidłowy klucz API (Błąd 401). Sprawdź ustawienia w secrets.toml."
            elif e.status_code == 404:
                error_msg = f"Nie znaleziono modelu (Błąd 404). Model '{model}' może być niedostępny dla tego klucza."
            elif e.status_code == 400:
                error_msg = f"Błędne zapytanie (Błąd 400) dla modelu '{model}'. Szczegóły: {str(e)}"
            
            if e.status_code >= 500 and attempt < retries:
                # Warto powtarzać tylko błędy leżące po stronie dostawcy (zaczynające się na 5xx)
                time.sleep((attempt + 1) * 2)
                continue
            result["error"] = error_msg
            break
            
        except Exception as e:
            # Wychwytuje wszystkie inne dziwne błędy systemowe
            result["error"] = f"Napotkano nieznany wyjątek Pythona: {str(e)}"
            break
            
    return result
