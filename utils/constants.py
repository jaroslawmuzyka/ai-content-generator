# Globalne stałe używane w aplikacji
APP_TITLE = "AI Content Generator"

# Domyślna lista operatorów (fallback, jeśli brakuje w secrets)
DEFAULT_OPERATORS = [
    "Operator 1",
    "Operator 2",
    "Admin"
]

CONTENT_TYPES = [
    "ecommerce_category",
    "ecommerce_product",
    "blog_post",
    "landing_page",
    "ecommerce_category_mm"
]

LOCALES = {
    "pl-PL": "pl",
    "en-US": "en",
    "en-GB": "en",
    "de-DE": "de",
    "cs-CZ": "cs",
    "sk-SK": "sk"
}

PROVIDERS = [
    "openai",
    "openrouter"
]

# Zaktualizowane listy modeli wg specyfikacji
MODELS_BY_PROVIDER = {
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
        "gpt-5.4-nano",
        "gpt-5.4-mini",
        "gpt-5.4"
    ],
    "openrouter": [
        "openai/gpt-4o-mini",
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-flash-1.5"
    ]
}

# Domyślne wybory na wypadek braku przypisania modelu
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "openrouter": "anthropic/claude-3.5-sonnet"
}

# Standaryzacja statusów w aplikacji
JOB_STATUSES = [
    "all",
    "queued",
    "processing",
    "needs_review",
    "completed",
    "failed",
    "draft",
    "interrupted"
]
