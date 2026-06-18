-- Aktualizacja modelu dla zadania generowania Metatagów
UPDATE default_prompt_steps
SET default_model = 'gpt-5.4-mini', temperature = NULL
WHERE step_key = 'meta_titles_and_descriptions';

UPDATE campaign_prompt_steps
SET model = 'gpt-5.4-mini', temperature = NULL
WHERE step_key = 'meta_titles_and_descriptions';

-- Aktualizacja modelu dla zadania generowania SEO Abstract
UPDATE default_prompt_steps
SET default_model = 'gpt-5.4-mini', temperature = NULL
WHERE step_key = 'seo_abstract';

UPDATE campaign_prompt_steps
SET model = 'gpt-5.4-mini', temperature = NULL
WHERE step_key = 'seo_abstract';
