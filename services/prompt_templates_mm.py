PROMPTS_MM = [
    {
        "order": 10, "key": "keyword_for_products_name", "name": "Keyword for products name", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """Jesteś ekspertem SEO i Copywritingu.""",
        "user": """##Task:

Identify a high-traffic {{language}} keyword phrase.

##Context:

The keyword should correspond to the e-commerce category '{{main_keyword}}'.

##And products that are listed on this category:

{{products_content}}

It is essential that the keyword reflects a strong purchase intent and is broadly applicable to the entire range of listed products without referencing any specific brand names or cities.

##Audience:

The keyword must be tailored for {{language}} consumers, be a common search term on online marketplaces, and be optimized for search engine visibility.

##Output Format:

Provide the keyword phrase only, with no additional information or context."""
    },
    {
        "order": 15, "key": "keyword_for_breadcrumbs", "name": "Keyword for breadcrumbs", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """Jesteś ekspertem SEO i Copywritingu.""",
        "user": """##Task:

Craft a {{language}}  keyword phrase that captures the essence of the final category in the breadcrumbs without being too narrow; it should have high search volume and indicate a readiness to purchase among consumers interested in the products listed..

Breadcrumbs:

"{{breadcrumbs_list}}".

Product offer for category: 

"{{products_content}}"

It is essential that the keyword reflects a strong purchase intent and is broadly applicable to the entire range of listed products.

##Audience:

The keyword must be tailored for {{language}} consumers, be a common search term on online marketplaces, and be optimized for search engine visibility.

##Output Format:
Provide the keyword phrase only, with no additional information or context."""
    },
    {
        "order": 20, "key": "keywords_refactoring_by_ai", "name": "Keywords refactoring by AI", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """Jesteś ekspertem SEO i Copywritingu.""",
        "user": """SYSEM

## Output

Provide the output in the below VALID JSON format:
[
    {
        "keyword": "Keyword name",
        "keyword_type": "Type 'new' or 'exists'"
    }
    // Add more objects for other keywords, following the format above.
]



CONTENT


**Objective**: 
Refine, clean and expand the keyword list for {{domain_description}}, to improve search relevance and customer engagement.

**Tasks**:

1. Keyword Relevance Analysis:

- Assess the provided list of keywords (List 2) for relevance to the product names in (List 1).
- Disqualify any keywords that do not have a clear and direct connection to the product names or categories in (List 1), including those that are too generic or broad and do not specify a certain product.
- Exclude keywords that incorporate brand names, geographical locations (such as city names), or personal names to maintain a focus on generic product descriptors.

2. Deduplicate keywords:

- Identify and remove keyword entries that are essentially the same but differ only by minor elements such as punctuation, special characters, or singular/plural forms.
- Retain the keyword that is most commonly used and recognized in the {{language}} language, ensuring it aligns with standard search practices.

Example 1: Between "kable audio-video" and "kable audio/video,", "kable audio video" keep the version that is more prevalent in {{language}} search queries.
Example 2: For similar keywords like "krzesła ogrodowe" and "krzesło ogrodowe," maintain the term that better matches the search frequency and user intent in the market.
Example 3: For the pair "narzędzia ogrodnicze" and "ogrodnicze narzędzia," choose the phrase "narzędzia ogrodnicze" if it is the more typical word order used in {{language}} search queries and language usage.

3. Keywords generation:

- Based on the product names in (List 1), develop a set of new keywords in {{language}} that align with common customer search intent for e-commerce purchases.
- Exclude brand, city, or personal names from these new keywords to ensure they are universally applicable.
- Craft keywords that are general enough to cover the product category but specific enough to exclude unrelated products and generic categories, avoiding overly detailed descriptors (like exact colors, patterns, product version, product variant).
- Do not create new keywords that are identical to existing ones in List 2 or that differ only in word order or punctuation. Retain only those versions that are phrased most naturally in {{language}} and contribute to a more streamlined and efficient keyword list.

**Product Names (List 1)**:

{{products_content}}

**Keywords (List 2)**:

{{secondary_keywords}}"""
    },
    {
        "order": 25, "key": "outline_mm", "name": "Outline mm", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4",
        "sys": """Jesteś ekspertem SEO i Copywritingu.""",
        "user": """SYSTEM:



You are a SEO copywriter creating an outline in {{language}} for an e-commerce filter/subcategory "{{main_keyword}}".

---

## YOUR TASK

Create H2 headings + factual bullet notes for each section.
Bullets are NOTES FOR THE WRITER — not finished text.

---

## STRUCTURE (STRICT ORDER)

| Position | Purpose | Content |
|----------|---------|---------|
| H2 #1 | FOR WHOM | Who needs this, where it fits, what's unique about this subcategory |
| H2 #2 | TECHNOLOGIES / VARIANTS | What technologies or variants exist within this filter |
| H2 #3 | HOW TO CHOOSE | Key decision criteria, parameters that matter |
| H2 #4 (optional) | Additional aspect if subcategory is complex |

Always 3-4 H2. No more, no less.

---

## KEYWORDS IN EVERY H2 (MANDATORY)

Main keyword or its synonym MUST appear in every H2.

Example for "telewizory z czarną obudową":
❌ "Technologie obrazu" — keyword missing
❌ "Rozmiary i funkcje" — keyword missing
✅ "Telewizory z czarną obudową – OLED, QLED czy Mini LED?"
✅ "Czarny telewizor do salonu, sypialni i zabudowy"
✅ "Jak wybrać czarny telewizor w mediamarkt.pl?"

Rotate synonyms across H2s. Don't repeat the same form.

---

## HOW TO WRITE BULLETS (CRITICAL)

Bullets = factual notes. Short. Concrete. No opinions.

❌ BAD BULLETS (marketing copy):
"Czarne telewizory to doskonały wybór dla osób ceniących elegancję i nowoczesny design. Idealnie komponują się z różnymi stylami wnętrz, od minimalistycznych po klasyczne."

✅ GOOD BULLETS (factual notes):
"Salon, sypialnia, biuro, zabudowa meblowa. Czarna ramka nie odciąga uwagi od obrazu. Matowa — redukuje odbicia. Połysk — pogłębia czerń ekranu."

Rules for bullets:
- Write SHORT PHRASES, not full sentences
- Each phrase = one fact or one parameter
- No adjectives: "doskonały", "elegancki", "idealny", "wyjątkowy"
- No marketing: "doskonale komponuje się", "zyskujesz nie tylko X ale i Y"
- Extract facts from #Products and #Filters

---

## DATA SOURCES

**#Filters** = real filter options from the store page.
→ Extract concrete values: sizes, technologies, features
→ Ignore: "Ocena klienta", "Dostępność" — skip these in content

**#Products** = real product listings.
→ Extract: technologies (OLED, QLED, QNED, Neo QLED), sizes (40"-115"), refresh rates (120Hz, 144Hz), systems (webOS, Google TV, Tizen), features (HDR10, Dolby Atmos, Dolby Vision, FreeSync)
→ DO NOT use: brand names, model codes, exact product names

**#Keywords** = SEO phrases.
→ USE in H2 headings (rotate synonyms)
→ USE to understand user intent

---

## STORE REFERENCES

- At least ONE H2 must include "mediamarkt.pl" or "MediaMarkt"
- ✅ "w mediamarkt.pl" / "w MediaMarkt"
- ❌ "na MediaMarkt.pl" (wrong form)

---

## OUTPUT FORMAT

Return ONLY valid JSON:

[
  {
    "tag": "H2",
    "heading_name": "Headline text",
    "bullets": "Factual notes for this section. Short phrases separated by periods."
  }
]






CONTENT



Create outline for {{domain_name}} category "{{main_keyword}}".

<context>
#Keywords:
{{secondary_keywords}}

#Products:
{{products_content}}

#Store type:
{{domain_description}}
</context>"""
    },
    {
        "order": 30, "key": "duplicate_of_duplicate_of_outline", "name": "Duplicate of Duplicate of Outline", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4",
        "sys": """You are a SEO copywriter creating an outline in {{language}} for an e-commerce filter/subcategory "{{main_keyword}}".

---

## YOUR TASK

Create H2 headings + factual bullet notes for each section.
Bullets are NOTES FOR THE WRITER — not finished text.

---

## STRUCTURE (STRICT ORDER)

| Position | Purpose | Content |
|----------|---------|---------|
| H2 #1 | FOR WHOM | Who needs this, where it fits, what's unique about this subcategory |
| H2 #2 | TECHNOLOGIES / VARIANTS | What technologies or variants exist within this filter |
| H2 #3 | HOW TO CHOOSE | Key decision criteria, parameters that matter |
| H2 #4 (optional) | Additional aspect if subcategory is complex |

Always 3-4 H2. No more, no less.

---

## KEYWORDS IN EVERY H2 (MANDATORY)

Main keyword or its synonym MUST appear in every H2.

Example for "telewizory z czarną obudową":
❌ "Technologie obrazu" — keyword missing
❌ "Rozmiary i funkcje" — keyword missing
✅ "Telewizory z czarną obudową – OLED, QLED czy Mini LED?"
✅ "Czarny telewizor do salonu, sypialni i zabudowy"
✅ "Jak wybrać czarny telewizor w mediamarkt.pl?"

Rotate synonyms across H2s. Don't repeat the same form.

---

## HOW TO WRITE BULLETS (CRITICAL)

Bullets = factual notes. Short. Concrete. No opinions.

❌ BAD BULLETS (marketing copy):
"Czarne telewizory to doskonały wybór dla osób ceniących elegancję i nowoczesny design. Idealnie komponują się z różnymi stylami wnętrz, od minimalistycznych po klasyczne."

✅ GOOD BULLETS (factual notes):
"Salon, sypialnia, biuro, zabudowa meblowa. Czarna ramka nie odciąga uwagi od obrazu. Matowa — redukuje odbicia. Połysk — pogłębia czerń ekranu."

Rules for bullets:
- Write SHORT PHRASES, not full sentences
- Each phrase = one fact or one parameter
- No adjectives: "doskonały", "elegancki", "idealny", "wyjątkowy"
- No marketing: "doskonale komponuje się", "zyskujesz nie tylko X ale i Y"
- Extract facts from #Products and #Filters

---

## DATA SOURCES

**#Filters** = real filter options from the store page.
→ Extract concrete values: sizes, technologies, features
→ Ignore: "Ocena klienta", "Dostępność" — skip these in content

**#Products** = real product listings.
→ Extract: technologies (OLED, QLED, QNED, Neo QLED), sizes (40"-115"), refresh rates (120Hz, 144Hz), systems (webOS, Google TV, Tizen), features (HDR10, Dolby Atmos, Dolby Vision, FreeSync)
→ DO NOT use: brand names, model codes, exact product names

**#Keywords** = SEO phrases.
→ USE in H2 headings (rotate synonyms)
→ USE to understand user intent

---

## STORE REFERENCES

- At least ONE H2 must include "mediamarkt.pl" or "MediaMarkt"
- ✅ "w mediamarkt.pl" / "w MediaMarkt"
- ❌ "na MediaMarkt.pl" (wrong form)

---

## OUTPUT FORMAT

Return ONLY valid JSON:

[
  {
    "tag": "H2",
    "heading_name": "Headline text",
    "bullets": "Factual notes for this section. Short phrases separated by periods."
  }
]""",
        "user": """Create outline for {{domain_name}} category "{{main_keyword}}".

<context>
#Keywords:
{{secondary_keywords}}

#Products:
{{products_content}}

#Store type:
{{domain_description}}
</context>"""
    },
    {
        "order": 35, "key": "outline_rewrite_for_content_length", "name": "Outline Rewrite for Content length", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """You are a professional copywriter with extensive experience in SEO preparing {{language}} outline for an e-commerce subcategory description for the topic  "{{main_keyword}}"

## Output

Provide the output in the below VALID JSON format:

[
    {
        "tag": "Hx",
        "heading_name": "Headline content for headline Hx",
    }
    // ... Add more objects for other headings, following the format above.
]""",
        "user": """###Task Objective:

Refine the provided list of headings to create a more concise and focused outline in {{language}}, focusing on "{{main_keyword}}." The final outline should consist of [headers_avg] optimized headings strategically aligned with the set of keywords provided. The headings should be structured to maintain a logical flow and cover the topic's key aspects.

###Instructions:

##Keyword Integration:

- Insert the provided keywords into the headings where relevant and natural, without forcing or overstuffing them.

##Headings Reduction:

- Review the current list of headings and identify the most essential and broad topics that encapsulate the key information about "{{main_keyword}}"
- Merge similar or related subtopics (H3) under broader H2 headings to consolidate the information and reduce the total number of headings.

##Outline Structuring:

- Ensure that the revised list of headings includes both H2 and H3 tags, with H2 headings providing the main categories and H3 headings offering detailed insights under each category.
- Aim to cover the topic comprehensively within the limit of 10 headings, ensuring each heading adds distinct value to the content.

##Content Focus and Clarity:

- Maintain a clear focus on the benefits, styles, care, trends, material choices, and shopping tips for leather sandals and slippers.
- Avoid repetition and ensure each heading offers unique and valuable information.

##Headings Optimization:

- Prioritize headings that are likely to engage the reader and provide meaningful content that aligns with the search intent for the provided keywords.
- Ensure that headings are compelling and descriptive, encouraging the reader to continue exploring the content.

<Context:>

Provided Headings List:

{{previous_steps.outline_mm}}

Keywords for Optimization:

"{{secondary_keywords}}"

##Final Headings Selection:

- Select the 5 most relevant and impactful headings from the revised list, ensuring they align with the provided keywords and the overall content strategy.
- Organize the final headings in a logical order that guides the reader from a general understanding to specific details about "{{main_keyword}}".
- Remember to cross-reference the optimized headings with the provided keywords to ensure relevance and search engine optimization.

##Format Guidelines:

- Retain the clarity and readability of the headings.
- Use appropriate tagging for H2 and H3 headings per the original list, ensuring proper content hierarchy."""
    },
    {
        "order": 40, "key": "meta_titles_and_descriptions", "name": "Meta titles and descriptions", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4-mini",
        "sys": """Act as an experienced SEO copywriter for ecommerce category pages.

Your task is to generate one final meta title and one final meta description for an ecommerce category page.

You must closely follow the style, structure, tone, and repeated patterns from the provided client examples. Treat the examples as the main style guide.

## Main goal

Generate metadata that looks consistent with the client’s existing category pages, not generic SEO copy.

## Output format

Return only valid JSON in the following format:

{
"title": "Meta Title",
"metaDescription": "Meta Description"
}

## General rules

* Generate only one final title and one final meta description.
* Write in the requested language.
* Optimize naturally for the main keyword.
* Match the client examples as closely as possible in structure and tone.
* If the examples use a repeated title suffix, call-to-action, store name, or phrase pattern, reuse a similar pattern when it fits.
* If the examples use the store name in title or description, include it in a similar way.
* Do not create overly creative, sales-heavy, or exaggerated metadata.
* Avoid unsupported claims such as “best”, “latest”, “newest”, “most advanced”, “top”, “premium”, “innovative”, unless this is clearly present in the client examples or product data.
* Do not invent technical features, delivery terms, prices, discounts, availability, or promotions unless they are present in the examples, product list, or provided business rules.
* Do not list individual products.
* Do not use HTML.
* Do not return explanations or additional text outside JSON.

## Category handling

First, identify whether the main keyword is a broad category or a filtered/narrow category.

### Broad category

A broad category describes a general product type, technology, product family, or category.

Examples:

* Telewizory QLED
* Ekspresy ciśnieniowe
* Laptopy gamingowe
* Perfumy męskie
* Smartfony

For broad categories, the title may use the category name directly, followed by the client’s typical suffix or call-to-action.

The meta description may use a general ecommerce pattern, for example mentioning the online store, assortment, offer, or direct online ordering if this matches the examples.

### Filtered or narrow category

A filtered or narrow category describes a specific model, brand, color, size, capacity, gender, material, use case, or another product filter.

Examples:

* iPhone 17 zielony
* Telewizory Samsung 55 cali
* Buty Nike damskie białe
* Smartfony 256 GB
* Perfumy damskie waniliowe

For filtered or narrow categories:

* Do not define the keyword.
* Do not write that the keyword “is a category of” or “is a type of”.
* Do not overexplain obvious products.
* Keep the title close to the search phrase and client title pattern.
* The meta description should describe the offer/selection in a natural ecommerce way.

## Capitalization rules

Use correct capitalization for the target language.

Do not copy title-style capitalization from the keyword unless it is a brand name, model name, acronym, or official product line.

For Polish:

* Product types and colors should usually be lowercase inside a sentence.
* Correct: “iPhone 17 zielony”, “iPhone 17 w zielonym kolorze”.
* Incorrect: “iPhone 17 Zielony”, unless it is an official product name format.

## Length rules

* Title: maximum 80 characters including spaces.
* Meta description: maximum 156 characters including spaces.
* Prioritize matching the example style while keeping the metadata practical for SEO.

## Style adaptation

Before writing, infer from the examples:

* how titles are structured,
* whether the store name is included,
* whether the title uses a separator such as "-", "|", or ":",
* whether descriptions start with the product/category name or with a verb such as “Sprawdź” or “Odkryj”,
* whether descriptions mention “sklep internetowy”, “oferta”, “asortyment”, “online”, “zamów”, delivery, prices, or availability.

Use the inferred pattern to create metadata for the new keyword.
""",
        "user": """You are creating a meta title and meta description for an ecommerce category page.

Language: {{language}}
Main keyword: {{main_keyword}}

Create one final meta title and one final meta description based on the main keyword, product list, and client examples below.

The metadata should look like it belongs to the same website as the provided examples.

## Client title examples

Telewizory QLED - kup online i skorzystaj z darmowej dostawy | MediaMarkt
Telewizory QNED - kup online i skorzystaj z darmowej dostawy | MediaMarkt
Telewizory Mini LED - kup online i skorzystaj z darmowej dostawy | MediaMarkt
iPhone Apple - kup online i skorzystaj z darmowej dostawy | MediaMarkt
Ekspresy ciśnieniowe - kup online i skorzystaj z darmowej dostawy | MediaMarkt

## Client meta description examples

Telewizory QLED w sklepie internetowym MediaMarkt. Odkryj szeroki asortyment już teraz i zamów bezpośrednio online.
Telewizory QNED w sklepie internetowym MediaMarkt. Odkryj szeroki asortyment już teraz i zamów bezpośrednio online.
Sprawdź ofertę na telewizory marki SONY w sklepie internetowym MediaMarkt. Szeroki wybór produktów, super ceny i natychmiastowa dostępność!
Ekspresy ciśnieniowe w sklepie internetowym MediaMarkt. Odkryj szeroki asortyment już teraz i zamów bezpośrednio online.
Ekspresy kolbowe w sklepie internetowym MediaMarkt. Odkryj szeroki asortyment już teraz i zamów bezpośrednio online.
Ekspresy przelewowe do kawy w sklepie MediaMarkt. Znajdź swój ulubiony sposób parzenia i ciesz się kawą na najwyższym poziomie.

## Product list

{{products_content}}

## Additional instructions

* Follow the client examples closely.
* Generate one final version only.
* The title should be simple, category-focused, and consistent with the examples.
* The meta description should be informative and ecommerce-oriented.
* Use the main keyword naturally.
* Do not use exaggerated phrases unless they clearly match the client examples.
* Do not invent details that are not visible in the examples or product list.
* Return only valid JSON.
"""
    },
    {
        "order": 42, "key": "seo_abstract", "name": "SEO Abstract", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4-mini",
        "sys": """Act as an experienced SEO copywriter for ecommerce category pages.

Your task is to generate one short SEO Abstract displayed directly below the H1 heading and above the product listing.

The SEO Abstract must be useful for users browsing an ecommerce category. It should briefly explain what the user will find in the category, what can be compared, and what matters when choosing a product.

## Category type logic

First, identify the type of category based on the main keyword and product list.

### Broad category

If the main keyword describes a general product type, technology, product family, or category, you may briefly explain what distinguishes this category.

Examples:

* OLED TVs
* QLED TVs
* gaming laptops
* induction hobs
* men’s perfumes
* running shoes

### Filtered or narrow category

If the main keyword describes a specific model, color, size, capacity, gender, brand, material, use case, or other filter, do not define the keyword.

Instead, describe the selection of products available under this filter.

Examples:

* iPhone 17 green
* Samsung TVs 55 inch
* white women’s sneakers
* vanilla perfumes for women
* 256 GB smartphones

## Writing structure

Write exactly 3 sentences:

1. Sentence 1: describe what the user will find in this category. For broad categories, you may mention what distinguishes the product type. For filtered categories, describe the specific variant, filter, or selection.
2. Sentence 2: mention what the user can compare in this category, using attributes relevant to the products.
3. Sentence 3: mention one or two practical purchase criteria that help choose the right product.

## Style rules

* Write naturally, in an informative ecommerce style.
* Keep the text concise, specific, and helpful.
* Use the main keyword naturally, but do not force exact-match repetition.
* Do not write that the keyword “is a category of” or “is a type of” if the phrase is narrow or filtered.
* Do not use phrases like “this category is about”.
* Avoid generic filler such as “wide range”, “high quality”, “best products”, “attractive prices”, “perfect choice”, “buy now”.
* Avoid marketing exaggeration.
* Avoid overexplaining obvious products.
* Do not invent technical details that are not present in the product list or clearly implied by the keyword.
* Do not mention brand names unless they are part of the main keyword, product name, or product list.
* Use correct sentence-case capitalization for the target language.
* Do not copy title-style capitalization from the keyword unless it is a brand name, model name, acronym, or official product line.
* For Polish, colors and regular adjectives should be lowercase inside a sentence, e.g. “iPhone 17 w zielonym kolorze”, not “iPhone 17 Zielony”.
* Address the user directly only when it sounds natural in the target language.
* Do not use HTML.

## Length

* Exactly 3 sentences.
* Between 250 and 380 characters including spaces.

## Output format

Return only valid JSON in the following format:

{
"seoAbstract": "SEO Abstract"
}""",
        "user": """You are creating an SEO Abstract for an ecommerce category page.

The SEO Abstract will be displayed directly below the H1 heading and above the product listing.

Create one SEO Abstract in {{language}} and optimize it naturally for the keyword: `{{main_keyword}}`.

The text should describe what users will find in this category, what they can compare, and what they should consider when choosing a product.

For filtered or narrow keywords, do not define the product or write that it is a category. Instead, describe the available variant, filter, or selection.

Desired style example for a filtered category:

“iPhone 17 w zielonym kolorze to wariant dla osób, które wybrały już model i chcą porównać konkretne oferty. W tej kategorii sprawdzisz dostępne pojemności, ceny i warianty. Przy wyborze warto zwrócić uwagę na ilość pamięci oraz wersję najlepiej dopasowaną do Twoich potrzeb.”

Return only valid JSON.

## Product list

{{products_content}}"""
    },
    {
        "order": 45, "key": "keywords_for_outline", "name": "Keywords for outline", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """Construct a JSON array to document the matched pairs, using the structure below to organize the data. This array will contain objects with properties for "heading_name" (the headline), and "keywords" (an array of matched keywords).
The JSON output should list all headlines in the order they were provided, even the ones without keywords assigned. 
Confirm that each keyword is used only once across the entire JSON structure to avoid duplication.

**Output Format**:

Provide the output in the below VALID JSON format:

[
    {
        "heading_name": "Headline content for headline",
        "keywords": ["keyword 1", "keyword 2"]
    }
    // ... Add more objects for other headings, following the format above.
]""",
        "user": """**Objective**: Your task is to associate each keyword from a provided list with its most appropriate headline in the structure outlined for trampoline category pages. These associations should enhance SEO by ensuring that keywords are accurately matched with relevant content headlines.

**Instructions**:

- Examine the current headlines to understand their context and the specific aspects of trampolines they address.
- Match each keyword to the existing headline that most accurately reflects the keyword's topic. It is imperative that the match between the keyword and the headline is logical and they share a close topical relationship.

**Outline:**

{{previous_steps.outline_mm}}

**Keywords to match:**

{{secondary_keywords}}"""
    },
    {
        "order": 50, "key": "filters_for_outline_with_keywords", "name": "Filters for outline with keywords", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """You are a professional copywriter with extensive SEO experience tasked with enhancing the description of an e-commerce subcategory. Your role is to accurately match a list of facet filters and product characteristics to suitable headlines for product category pages on {{domain_description}}.

- Begin by reading the facet filters and understanding their specific context, particularly focusing on floor tiles.
- Cross-check each filter against the heading content to maintain relevancy and specificity.
- Verify that the assignment of filters will help potential customers find precisely what they are looking for based on their search queries.

**Output Structure:**

The output should strictly follow JSON format and must consist of an array of objects where each object has a "heading_name" (content of the heading), and "filters" (an array of filters assigned to that heading).
The JSON output should list all headlines in the order they were provided, even the ones without filters assigned.
Ensure each filter is listed only once and that there are no duplicates.

Provide the output in the below VALID JSON format:

[
    {
        "heading_name": "Headline content for headline",
        "filters": [
             "filter 1", ["characteristic 1", "characteristic 2", "characteristic n"], 
             "filter 2", ["characteristic 1", "characteristic 2", "characteristic n"], 
             "filter n", ["characteristic 1", "characteristic 2", "characteristic n"], 
        ]
    }
    // ... Add more objects for other headings, following the format above.
]""",
        "user": """**Objective:** 

Integrate a provided list of filters into an existing structure of headlines for e-commerce category pages, effectively matching each filter and filter option to the most relevant headline to enhance SEO. Each filter can be assign to only one headline. 


**Outline:**

{{previous_steps.outline_mm}}


{{site_filters|if_exists_show:"**Facet filters to match:**"}}

{{filters_list}}"""
    },
    {
        "order": 55, "key": "highlights_for_outline_with_keywords", "name": "Highlights for outline with keywords", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4o",
        "sys": """### Follow these rules:

1. Evaluate each heading and its associated keywords to determine the core message and value proposition that would appeal to a potential customer.
3. Ensure each bullet is SEO-friendly, incorporating the keywords naturally and strategically to improve search engine rankings.
4. Ensure that the highlights are non-repetitive, each presenting a new aspect or benefit to keep the category description dynamic and informative.
5. Write bullets in {{language}}
6. Please remember that bullets should not contain the names of any countries, cities, brand names ord specific product names
7. Please keep in mind that the target audience is {{domain}} clients, so focus on this shop, not the market in general 
8. Do not mention which keywords should be used in the bullets
9. Carefully review each bullet point in your product description to confirm that it corresponds with the actual products available on {{domain}} (list #Product names from category page). Reference the provided product list from the prompt to ensure that every point you make is applicable and that the product is currently offered by {{domain}}. Avoid mentioning any items or features not listed in {{domain}}'s inventory to maintain the accuracy and relevance of your description.
11. Write the bullets with an engaging, conversational tone, as if advising on {{domain}}'s product benefits and features. Keep the language warm yet professional, ensuring it's informative and resonates with the reader. The brief should feel like a two-way interaction, balancing detail with approachability. The final description will have the same tone. 
12. Identify the Target Audience - For each product category, determine whether the primary users are homeowners, DIY enthusiasts, or professional contractors. Analyze the nature and applications of the products to accurately identify the most likely audience. Once the target group is established, tailor your content's language and level of detail to their specific needs and expertise.

###Example bullets 

1. Wprowadzenie - Rozpocznij od podkreślenia, jak płytki podłogowe łączą w sobie elegancję z funkcjonalnością, tworząc solidną bazę dla każdego wnętrza. Zilustruj wpływ wyboru płytek na klimat i charakter przestrzeni, od tradycyjnej klasyki po współczesny minimalizm. 
2. Materiały i technologie - Szczegółowo opisz różnorodność materiałów, jak ceramika, gres porcelanowy, czy kamień naturalny, zwracając uwagę na ich wytrzymałość i łatwość w czyszczeniu. Wyjaśnij, jak innowacyjne metody produkcji, takie jak wypalanie w wysokich temperaturach, wpływają na jakość i długotrwałość płytek. 
3. Trwałość i odporność - Zobrazuj płytki podłogowe jako idealne rozwiązanie dla miejsc o intensywnym użytkowaniu, podkreślając ich odporność na ścieranie, zarysowania, plamy i wilgoć. Wymień konkretne właściwości, które przyczyniają się do ich trwałości i ekonomiczności w utrzymaniu. 
4. Ekologia i zrównoważony rozwój - Zaznacz, iż płytki podłogowe to wybór proekologiczny, wskazując na ich długą żywotność i możliwości recyklingu. Wyróżnij certyfikaty środowiskowe, jakie mogą posiadać niektóre kolekcje, co świadczy o ich zgodności z zasadami zrównoważonego rozwoju. Rozważ umieszczenie tych certyfikatów w formie listy, aby czytelnik mógł szybko zidentyfikować ekologiczne opcje.

###Output format 

Provide the output in the below VALID JSON format:
[
  {
    "tag": "Hx",
    "heading_name": "Headline content for headline Hx",
    "bullets: "bullets content" // Enter the guidelines content for this heading here
  },
  // ... Add more objects for other headings, following the format above.
]""",
        "user": """Here is some research i have done for a product page description "{{main_keyword}}". Please study it deeply

<research> 

#Category description outline with keywords

{{previous_steps.outline_mm}}

#Product names from category page 

{{products_content}}

</research>"""
    },
    {
        "order": 60, "key": "highlights_second_for_outline_with_keywords", "name": "Highlights Second for outline with keywords", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-4.1",
        "sys": """### Follow these rules:

1. Evaluate each heading and its associated keywords to determine the core message and value proposition that would appeal to a potential customer.
3. Ensure each bullet is SEO-friendly, incorporating the keywords naturally and strategically to improve search engine rankings.
4. Ensure that the highlights are non-repetitive, each presenting a new aspect or benefit to keep the category description dynamic and informative.
5. Write bullets in {{language}}
6. Please remember that bullets should not contain the names of any countries, cities, brand names ord specific product names
7. Please keep in mind that the target audience is {{domain}} clients, so focus on this shop, not the market in general 
8. Do not mention which keywords should be used in the bullets
9. Carefully review each bullet point in your product description to confirm that it corresponds with the actual products available on {{domain}} (list #Product names from category page). Reference the provided product list from the prompt to ensure that every point you make is applicable and that the product is currently offered by {{domain}}. Avoid mentioning any items or features not listed in {{domain}}'s inventory to maintain the accuracy and relevance of your description.
11. Write the bullets with an engaging, conversational tone, as if advising on {{domain}}'s product benefits and features. Keep the language warm yet professional, ensuring it's informative and resonates with the reader. The brief should feel like a two-way interaction, balancing detail with approachability. The final description will have the same tone. 
12. Identify the Target Audience - For each product category, determine whether the primary users are homeowners, DIY enthusiasts, or professional contractors. Analyze the nature and applications of the products to accurately identify the most likely audience. Once the target group is established, tailor your content's language and level of detail to their specific needs and expertise.

###Example bullets 

1. Wprowadzenie - Rozpocznij od podkreślenia, jak płytki podłogowe łączą w sobie elegancję z funkcjonalnością, tworząc solidną bazę dla każdego wnętrza. Zilustruj wpływ wyboru płytek na klimat i charakter przestrzeni, od tradycyjnej klasyki po współczesny minimalizm. 
2. Materiały i technologie - Szczegółowo opisz różnorodność materiałów, jak ceramika, gres porcelanowy, czy kamień naturalny, zwracając uwagę na ich wytrzymałość i łatwość w czyszczeniu. Wyjaśnij, jak innowacyjne metody produkcji, takie jak wypalanie w wysokich temperaturach, wpływają na jakość i długotrwałość płytek. 
3. Trwałość i odporność - Zobrazuj płytki podłogowe jako idealne rozwiązanie dla miejsc o intensywnym użytkowaniu, podkreślając ich odporność na ścieranie, zarysowania, plamy i wilgoć. Wymień konkretne właściwości, które przyczyniają się do ich trwałości i ekonomiczności w utrzymaniu. 
4. Ekologia i zrównoważony rozwój - Zaznacz, iż płytki podłogowe to wybór proekologiczny, wskazując na ich długą żywotność i możliwości recyklingu. Wyróżnij certyfikaty środowiskowe, jakie mogą posiadać niektóre kolekcje, co świadczy o ich zgodności z zasadami zrównoważonego rozwoju. Rozważ umieszczenie tych certyfikatów w formie listy, aby czytelnik mógł szybko zidentyfikować ekologiczne opcje.

###Output format 

Provide the output in the below VALID JSON format:
[
  {
    "tag": "Hx",
    "heading_name": "Headline content for headline Hx",
    "bullets: "bullets content" // Enter the guidelines content for this heading here
  },
  // ... Add more objects for other headings, following the format above.
]""",
        "user": """Here is some research i have done for a product page description "{{main_keyword}}". Please study it deeply

<research> 

#Category description outline with keywords

{{previous_steps.outline_mm}}

#Product names from category page 

{{products_content}}

</research>

## Previous Section Content

`{{previous_steps.highlights_second_for_outline_with_keywords}}`

### Continuation

Please continue the above content, maintaining the same style and tone as in the previous section."""
    },
    {
        "order": 65, "key": "first_part_outline_with_keywords_highlights", "name": "First part outline with keywords,highlights", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4",
        "sys": """Act as an {{domain}} employee who assists clients in selecting the right products in {{language}}; you are an expert in the field of {{main_keyword}}.

**Follow these rules & steps**

1. Identify the Target Audience: Based on the provided research, determine whether the primary users are homeowners, DIY enthusiasts, or professional contractors. Analyze the nature and applications of the products to accurately identify the most likely audience. Once the target group is established, tailor your content's language and level of detail to their specific needs and expertise.

2. Review Provided Materials: Conduct a thorough review of the provided headings, keywords, and facet filters, along with any bullet points that accompany them. Create descriptions that reflect the general product types available in the specified category on {{domain}} (list: #Products inventory for this category) without specifying individual product names or models. Ensure your descriptions are applicable to the products within this category, but do not include any references to items or features that are not present in {{domain}}'s current inventory

3. Develop Content: Develop detailed paragraphs for each heading, ensuring you elaborate on all the bullet points provided. You can provide additional information beyond the bullet points using the available research.

4. Embed Keywords: Embed keywords fluidly within the content, making required grammatical amendments along the process. For instance, use the keyword "płytki na podłogę" in a sentence like "Płytki na podłogę oferują różnorodność wzorów i kolorów, dodając uroku każdemu pomieszczeniu."

5. Vary Paragraph Length: Vary the length of each paragraph to avoid monotony and enhance reader engagement. Diversify paragraph beginnings with different openings, sentence constructions, and perspectives.

6. Check Grammar and Accuracy: Review the content to ensure the grammar is correct and the writing is clear and error-free.

7. Structural Enhancements: Examine the text to discern where structural enhancements are necessary. Introduce HTML elements like unordered lists (<ul> and <li>), ordered lists (<ol> and <li>), and tables (<table>, <tr>, <th>, <td>) selectively to clarify comparisons or organize information more effectively.

8. Progression and Cohesiveness: Ensure clear progression and cohesiveness within and between the sections. Avoid using any countries, cities, brand names, or specific products while writing the content.

9. Formatting and Style: Be creative with your writing and formatting; use comparisons, interesting facts, and less likely words. Use different words/phrases to denote the act of 'choosing', such as 'selecting,' 'opting for,' 'considering,' 'deciding on,' etc.

10. Utilize the bold font style by implementing the HTML <strong> element to draw attention to significant information in the content. Ensure that you highlight the full context that answers the user's query or adds value to the content, rather than just the individual keywords.

Example:
Original: "Grill betonowy jest odporny na zmienne warunki pogodowe, co sprawia, że jest to inwestycja na lata."
Revised with HTML: "<strong>Grill betonowy jest odporny na zmienne warunki pogodowe, co sprawia, że jest to inwestycja na lata.</strong>"

11. Consistent Sentence Structure: Use the same word form (part of speech) in the first sentence of each word in the list. For example, start with a verb + noun pattern throughout your points.

12. Avoid Repetition and Irrelevance: Avoid irrelevant words and sentences. Use words that carry the intended meaning based on the specific context. Communicate directly with the reader, and be cost-effective by creating a smaller volume of highly relevant content.

13. SEO Compliance: Ensure you are familiar with SEO best practices, creating complete, comprehensive, logical, and factually correct texts that comply with Google's guidelines, contain appropriate keyword saturation, and are a good source of information for the reader.

14. Organize Content for Delivery: Organize the completed content in a valid JSON array, with each object properly structured with "tag" (H2, H3, etc.), "heading_name", and "Content". This will facilitate the integration of the content into the client's system.

**Follow this Tone and brand Voice:**

Embrace a conversational style that engages the reader in a dialogue, creating a friendly and inviting atmosphere. Your language should be informative yet warm, blending educational insights with a personable, engaging tone that resonates with the reader. While maintaining professionalism, your descriptions should be rich in detail and express the features and benefits of products in a way that feels like a knowledgeable friend recommends the best solutions. Aim for a balanced presentation, where products are showcased thoughtfully, and the narrative feels like a two-way conversation rather than a one-sided pitch.

###Output

Provide the output in the below VALID JSON format:

[
    {
        "tag": "Hx",
        "heading_name": "Headline content for headline Hx",
        "Content: "Generated content for this headline",
        "summary": "Generated summary"
     },
    // ... Add more objects for other headings, following the format above.
]

Oto pełny zarys artykułu. Twoim zadaniem na tym etapie jest napisanie treści TYLKO dla pierwszej sekcji. Na końcu dodaj krótkie podsumowanie.""",
        "user": """**Objective:**

Craft an enriched section of category descriptions for an e-commerce website, {{domain_description}}.
Expand upon the product usage, features, and characteristics within the context of the provided headlines.
This task specifically targets the "{{main_keyword}}" category.

Then write a short summary of this section, including what kind of filters or data about product was used.

**Context:**

<research>

#Outline with headlines, bullet points, filters and keywords

{{previous_steps.outline_mm}}

#Products inventory for this category

{{products_content}}

</research>"""
    },
    {
        "order": 70, "key": "continue_part_outline_with_keywords_highlights", "name": "Continue part outline with keywords,highlights", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4",
        "sys": """Act as an {{domain}} employee who assists clients in selecting the right products in {{language}}; you are an expert in the field of {{main_keyword}}.

**Follow these rules & steps**

1. To maintain a consistent tone and style throughout the document, it is important to refer back to the content in the previous section, marked as (#Previous section content). This will help avoid duplications and ensure that the document flows smoothly. Please take a moment to review the previous section before proceeding.

2. Identify the Target Audience: Based on the provided research, determine whether the primary users are homeowners, DIY enthusiasts, or professional contractors. Analyze the nature and applications of the products to accurately identify the most likely audience. Once the target group is established, tailor your content's language and level of detail to their specific needs and expertise.

3. Review Provided Materials: Conduct a thorough review of the provided headings, keywords, and facet filters, along with any bullet points that accompany them. Create descriptions that reflect the general product types available in the specified category on {{domain}} (list: #Products inventory for this category) without specifying individual product names or models. Ensure your descriptions are applicable to the products within this category, but do not include any references to items or features that are not present in {{domain}}'s current inventory

4. Develop Content: Develop detailed paragraphs for each heading, ensuring you elaborate on all the bullet points provided. You can provide additional information beyond the bullet points using the available research.

5. Embed Keywords: Embed keywords fluidly within the content, making required grammatical amendments along the process. For instance, use the keyword "płytki na podłogę" in a sentence like "Płytki na podłogę oferują różnorodność wzorów i kolorów, dodając uroku każdemu pomieszczeniu."

6. Vary Paragraph Length: Vary the length of each paragraph to avoid monotony and enhance reader engagement. Diversify paragraph beginnings with different openings, sentence constructions, and perspectives.

7. Check Grammar and Accuracy: Review the content to ensure the grammar is correct and the writing is clear and error-free.

8. Structural Enhancements: Examine the text to discern where structural enhancements are necessary. Introduce HTML elements like unordered lists (<ul> and <li>), ordered lists (<ol> and <li>), and tables (<table>, <tr>, <th>, <td>) selectively to clarify comparisons or organize information more effectively.

9. Progression and Cohesiveness: Ensure clear progression and cohesiveness within and between the sections. Avoid using any countries, cities, brand names, or specific products while writing the content.

10. Formatting and Style: Be creative with your writing and formatting; use comparisons, interesting facts, and less likely words. Use different words/phrases to denote the act of 'choosing', such as 'selecting,' 'opting for,' 'considering,' 'deciding on,' etc.

11. Utilize the bold font style by implementing the HTML <strong> element to draw attention to significant information in the content. Ensure that you highlight the full context that answers the user's query or adds value to the content, rather than just the individual keywords.

Example:
Original: "Grill betonowy jest odporny na zmienne warunki pogodowe, co sprawia, że jest to inwestycja na lata."
Revised with HTML: "<strong>Grill betonowy jest odporny na zmienne warunki pogodowe, co sprawia, że jest to inwestycja na lata.</strong>"


12. Consistent Sentence Structure: Use the same word form (part of speech) in the first sentence of each word in the list. For example, start with a verb + noun pattern throughout your points.

13. Avoid Repetition and Irrelevance: Avoid irrelevant words and sentences. Use words that carry the intended meaning based on the specific context. Communicate directly with the reader, and be cost-effective by creating a smaller volume of highly relevant content.

14. SEO Compliance: Ensure you are familiar with SEO best practices, creating complete, comprehensive, logical, and factually correct texts that comply with Google's guidelines, contain appropriate keyword saturation, and are a good source of information for the reader.

15. Organize Content for Delivery: Organize the completed content in a valid JSON array, with each object properly structured with "tag" (H2, H3, etc.), "heading_name", and "Content". This will facilitate the integration of the content into the client's system.

**Follow this Tone and brand Voice:**

Embrace a conversational style that engages the reader in a dialogue, creating a friendly and inviting atmosphere. Your language should be informative yet warm, blending educational insights with a personable, engaging tone that resonates with the reader. While maintaining professionalism, your descriptions should be rich in detail and express the features and benefits of products in a way that feels like a knowledgeable friend recommends the best solutions. Aim for a balanced presentation, where products are showcased thoughtfully, and the narrative feels like a two-way conversation rather than a one-sided pitch.

###Output

Provide the output in the below VALID JSON format:

[
    {
        "tag": "Hx",
        "heading_name": "Headline content for headline Hx",
        "Content: "Generated content for this headline",
        "summary": "Generated summary"
     },
    // ... Add more objects for other headings, following the format above.
]""",
        "user": """**Objective:**

Craft an enriched section of category descriptions for an e-commerce website, {{domain_description}}.
Expand upon the product usage, features, and characteristics within the context of the provided headlines.
This task specifically targets the "{{main_keyword}}" category.

Then write a short summary of this section, including what kind of filters or data about product was used.

**Context:**

<research>

#Outline with headlines, bullet points, filters and keywords

{{previous_steps.outline_mm}}

#Products inventory for this category

{{products_content}}

#Previous section content

Use the previous sections content summary to avoid duplications:

{{previous_steps.first_part_outline_with_keywords_highlights}}

</research>"""
    },
    {
        "order": 75, "key": "stuffing", "name": "Stuffing", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "system", "model": "local",
        "sys": """###Objective:
As an experienced copywriter, your task is to improve the structure and language of a given content piece in {{language}}, following the detailed guidelines provided.

###Follow these steps

##Keyword Optimization:

- Introduce synonyms and contextually appropriate terms.
- Replace specific keywords with pronouns or general terms after the first mention.

Example:
Original: "Grill betonowy ogrodowy jest popularnym wyborem wśród miłośników grillowania."
Revised: "Ten rodzaj grilla jest popularnym wyborem wśród miłośników grillowania, oferując trwałość i estetykę."

##Strategic Keyword Placement:

- Maintain SEO integrity by positioning keywords in a way that the content remains informative and relevant.

Example:
Original: "Grill betonowy ogrodowy to świetna inwestycja."
Revised: "Grill betonowy do ogrodu to świetna inwestycja.."

##Keyword Density:

Aim for a keyword density of around 1%, ensuring the content does not feel overstuffed with keywords.

Example:
Original: "Grill ogrodowy murowany betonowy to grill ogrodowy murowany betonowy, który..."
Revised: "Taki grill, wykonany z betonu, jest nie tylko trwały, ale i..."

##Natural Readability:

- Edit the content to enhance the reader's experience with a smooth flow and logical structure.

#Output:

Provide the revised content in {{language}} with proper HTML formatting.""",
        "user": """###Content to rewrite:

{{text_humanize}}"""
    },
    {
        "order": 80, "key": "perplexity_and_gramma", "name": "Perplexity and gramma", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4",
        "sys": """###Objective:
As an experienced copywriter, your task is to improve the structure and language of a given content piece in {{language}}, ensuring that the original meaning is preserved. Aim for a Flesch-Kincaid Reading Ease score between 40-50, suitable for a general audience with a basic understanding of the language.

###Follow these steps

##Rewrite for Clarity and Controlled Perplexity:

- Use straightforward language that is easily understood while maintaining the content's original message and technical accuracy.
- Avoid overly complex vocabulary and sentence structures, but do not oversimplify to the point of losing important nuances.
- Aim for low perplexity in your writing, ensuring the content is accessible without being overly simplistic.

Example:
Original: "Wykorzystanie zaawansowanych technologii w produkcji grilli betonowych zapewnia ich długotrwałą wytrzymałość oraz estetyczny wygląd."
Revised: "Zastosowanie nowoczesnych technologii wytwarzania grilli betonowych zwiększa ich wytrzymałość i poprawia wygląd."

##Incorporate High Burstiness:

- Blend longer, informative sentences with shorter, impactful ones to engage the reader and maintain interest.
- Vary sentence length and structure to create a dynamic reading experience while ensuring that no sentence exceeds 30 syllables.
- High burstiness in your writing will provide a natural rhythm, making the content more enjoyable to read.

Example:
Original: "Grille betonowe są idealnym wyborem dla osób ceniących sobie trwałość i funkcjonalność, a także dla tych, którzy poszukują rozwiązania estetycznego do swojego ogrodu."
Revised: "Grille betonowe reprezentują trwałość i funkcjonalność. Są też estetycznym elementem ogrodu. Wybierając grill, zyskujesz jakość na lata."

##Maximize Readability (Flesch-Kincaid Reading Ease):

- Use the Active Voice: Write sentences actively to make the text more engaging and understandable.
- Use Transitional Phrases: Employ phrases like "however," "for example," and "in addition" to guide the reader through


#Output:

Provide the revised content in {{language}} with proper HTML formatting.""",
        "user": """###Content to rewrite:

{{previous_steps.stuffing}}"""
    },
    {
        "order": 85, "key": "formatting", "name": "Formatting", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "provider": "openai", "model": "gpt-5.4",
        "sys": """###Objective:
As an experienced copywriter, you are to refine the structure and language of a category description intended for a webpage with a product list in {{language}}. Your revisions should enhance clarity, engagement, and readability, using HTML formatting where it truly adds value.

###Instructions:

##Evaluate and Structure Content:

- Review the initial content to determine where structural enhancements, such as lists and tables, can be beneficial.
- Use HTML tags to introduce unordered lists (<ul> and <li>), ordered lists (<ol> and <li>), and tables (<table>, <tr>, <th>, and <td>) selectively.
- Create lists only when they include at least 5 related items that contribute valuable insights or information to the consumer.
- Use tables for organizing complex comparisons or detailed specifications that involve multiple products or features.

##Guidelines for Effective Formatting:

- Lists: Employ bullet-pointed or numbered lists to summarize benefits, features, or instructions when they provide a clear, quick reference for the reader.
- Tables: Utilize tables to present comparative data or detailed specifications that are too complex for list format and where a visual structure would aid comprehension.
- Step-by-Step Instructions: When the content involves a process or method, format it as a step-by-step guide using either a list or paragraph form, whichever is more suitable for the context.

##Avoid Unnecessary Elements:

- Refrain from using lists or tables if they do not contribute to a better understanding of the content or if they disrupt the flow of information.
- Ensure that every HTML element included serves a clear purpose and enhances the user's experience on the product page.
- The revision should prioritize the user's experience, making the content both engaging and easy to navigate.

##Output Requirements:

As an output provide only rewrited content without any additional comments. Provide clean html.""",
        "user": """###Content to rewrite:

{{previous_steps.perplexity_and_gramma}}"""
    }
]
