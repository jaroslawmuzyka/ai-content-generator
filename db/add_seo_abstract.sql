ALTER TABLE content_jobs ADD COLUMN IF NOT EXISTS seo_abstract text;

DO $$
DECLARE
    sys_prompt TEXT := 'Act as an experienced SEO copywriter for ecommerce category pages.

Your task is to generate a short SEO Abstract: an informative introductory text displayed directly below the H1 heading and above the product listing.

The SEO Abstract must:
* Be written in the requested language.
* Be optimized naturally for the main keyword.
* Sound factual, helpful, and category-specific.
* Mention what users can compare in this category.
* End with practical purchase criteria relevant to the category.
* Use exactly 3 sentences.
* Be between 350 and 450 characters including spaces.
* Avoid marketing clichés, sales slogans, exaggerated claims, and calls to action.
* Avoid brand names unless the category or main keyword is explicitly brand-specific.
* Avoid repeating the same phrases from previously generated content.
* Avoid keyword stuffing.
* Do not invent technical details that are not supported by the keyword or product list.
* If the product list is limited or unclear, write in a safe, general, category-level way.
* Do not use HTML.
* Return only valid JSON.

Output format:
{
"seoAbstract": "SEO Abstract"
}';

    usr_prompt TEXT := 'You are creating an SEO Abstract for an ecommerce category page.

Language: {{language}}
Main keyword: {{main_keyword}}

The text should be displayed directly below the H1 heading and above the product listing.

Create one SEO Abstract based on the main keyword and the product list below.

The abstract should follow this structure:

1. Sentence 1: define or explain the category and what distinguishes it.
2. Sentence 2: describe what the user can compare in this category, based on typical product attributes and the product list.
3. Sentence 3: mention the most important purchase criteria for this category.

Keep the tone informative, neutral, and useful for users who are comparing products.

Do not use brand names unless the main keyword or category is brand-specific.
Do not list individual products.
Do not add promotional phrases such as “best choice”, “top quality”, “great prices”, “buy now”, or similar.
Do not mention the ecommerce store name.
Do not exceed 450 characters.
Return only valid JSON.

## Product list

{{products_content}}';
BEGIN
    INSERT INTO default_prompt_steps (
        default_prompt_set_id, step_order, step_key, step_name,
        system_prompt, user_prompt, max_tokens, default_provider, default_model, is_active, stage_group
    )
    SELECT id, 42, 'seo_abstract', 'SEO Abstract',
    sys_prompt, usr_prompt, 4000, 'openai', 'gpt-4o', true, 'seo'
    FROM default_prompt_sets
    WHERE NOT EXISTS (
        SELECT 1 FROM default_prompt_steps 
        WHERE default_prompt_steps.default_prompt_set_id = default_prompt_sets.id 
        AND default_prompt_steps.step_key = 'seo_abstract'
    );

    INSERT INTO campaign_prompt_steps (
        campaign_prompt_set_id, step_order, step_key, step_name,
        system_prompt, user_prompt, max_tokens, provider, model, is_active, stage_group
    )
    SELECT id, 42, 'seo_abstract', 'SEO Abstract',
    sys_prompt, usr_prompt, 4000, 'openai', 'gpt-4o', true, 'seo'
    FROM campaign_prompt_sets
    WHERE NOT EXISTS (
        SELECT 1 FROM campaign_prompt_steps 
        WHERE campaign_prompt_steps.campaign_prompt_set_id = campaign_prompt_sets.id 
        AND campaign_prompt_steps.step_key = 'seo_abstract'
    );
END $$;
