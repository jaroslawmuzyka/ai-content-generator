import os
import re

prompty_dir = "prompty"
output_file = "services/prompt_templates_mm.py"

files = os.listdir(prompty_dir)
files.sort(key=lambda x: int(re.search(r'^(\d+)', x).group(1)) if re.search(r'^(\d+)', x) else 999)

steps = []
order = 10

var_mapping = {
    "[[language_name]]": "{{language}}",
    "[[site_keyword]]": "{{main_keyword}}",
    "[[keyword]]": "{{main_keyword}}",
    "[[site_products_or_subcategories|new_line]]": "{{products_content}}",
    "[[domain_name_from_projects_url]]": "{{domain}}",
    "[[domain_description]]": "{{domain_description}}",
    "[[site_breadcrumbs|bullet_breadcrumbs_list]]": "{{breadcrumbs_list}}",
    "[[site_filters|bullet_filter_list]]": "{{filters_list}}",
    "[[outline_sections_json|first_section]]": "{{previous_steps.outline_mm}}",
    "[[outline_sections_json|sections_no]]": "{{previous_steps.outline_mm}}",
    "[[openai_outline_json|new_line_section_only_name]]": "{{previous_steps.outline_mm}}",
    "[[openai_outline_json|to_string]]": "{{previous_steps.outline_mm}}",
    "[[summary]]": "{{previous_steps.first_part_outline_with_keywords_highlights}}",
    "[[text_humanize]]": "{{text_humanize}}",
    "[[openai_highlights_before]]": "{{previous_steps.highlights_second_for_outline_with_keywords}}",
    "[[keywords|new_line]]": "{{secondary_keywords}}",
    "[[headers_avg]]": "5"
}

for f_name in files:
    if not f_name.endswith('.txt'):
        continue
    
    with open(os.path.join(prompty_dir, f_name), 'r', encoding='utf-8') as f:
        content = f.read()
        
    for k, v in var_mapping.items():
        content = content.replace(k, v)
        
    content = re.sub(r'\[\[(.*?)\]\]', r'{{\1}}', content)
        
    if "CONTENT:" in content:
        parts = content.split("CONTENT:")
        if "SYSTEM:" in parts[0]:
            sys_prompt = parts[0].replace("SYSTEM:", "").strip()
        else:
            sys_prompt = parts[0].strip()
        user_prompt = parts[1].strip()
    else:
        sys_prompt = "Jesteś ekspertem SEO i Copywritingu."
        user_prompt = content.strip()
        
    if "12-First part outline" in f_name:
        sys_prompt += "\n\nOto pełny zarys artykułu. Twoim zadaniem na tym etapie jest napisanie treści TYLKO dla pierwszej sekcji. Na końcu dodaj krótkie podsumowanie."
    if "13-Continue part outline" in f_name:
        sys_prompt += "\n\nOto pełny zarys artykułu, a poniżej masz treść, którą już napisałeś w poprzednim kroku. Twoim zadaniem jest napisanie treści dla POZOSTAŁYCH sekcji (pomiń pierwszą)."
        
    # Kaskada dla kroków końcowych
    if "15-Perplexity and gramma" in f_name:
        user_prompt = user_prompt.replace("{{text_humanize}}", "{{previous_steps.stuffing}}")
    if "16-Formatting" in f_name:
        user_prompt = user_prompt.replace("{{text_humanize}}", "{{previous_steps.perplexity_and_gramma}}")
        
    step_key = f_name.replace('.txt', '').lower()
    step_key = re.sub(r'^\d+-', '', step_key)
    step_key = re.sub(r'[^a-z0-9]', '_', step_key).strip('_')
    step_key = re.sub(r'_+', '_', step_key)
    
    step_name = f_name.replace('.txt', '')
    step_name = re.sub(r'^\d+-', '', step_name).strip()
    
    step = f"""    {{
        "order": {order}, "key": "{step_key}", "name": "{step_name}", "stage_group": "seo", "output_type": "text", "max_tokens": 4000,
        "sys": \"\"\"{sys_prompt}\"\"\",
        "user": \"\"\"{user_prompt}\"\"\"
    }}"""
    
    steps.append(step)
    order += 5

out_content = 'PROMPTS_MM = [\n' + ',\n'.join(steps) + '\n]\n'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(out_content)

print(f"Zapisano {len(steps)} promptów do {output_file}")
