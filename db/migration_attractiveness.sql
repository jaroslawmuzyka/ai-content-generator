-- Migration for Attractiveness Module

-- 1. Create campaign_content_strategy table
CREATE TABLE campaign_content_strategy (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references campaigns(id) on delete cascade,
    brand_description text,
    target_audience text,
    persona text,
    consumer_insight text,
    customer_language text,
    main_pain_points text,
    main_desires text,
    decision_triggers text,
    brand_tone text,
    brand_archetype text,
    forbidden_phrases text,
    required_phrases text,
    value_proposition text,
    proof_points text,
    call_to_action text,
    content_goal text,
    marketing_frameworks jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    UNIQUE(campaign_id)
);

CREATE TRIGGER update_campaign_content_strategy_modtime
BEFORE UPDATE ON campaign_content_strategy FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- 2. Add stage_group to prompt tables
ALTER TABLE default_prompt_steps ADD COLUMN stage_group text default 'seo';
ALTER TABLE campaign_prompt_steps ADD COLUMN stage_group text default 'seo';
ALTER TABLE job_prompt_snapshots ADD COLUMN stage_group text default 'seo';

-- 3. Add new columns to content_jobs
ALTER TABLE content_jobs ADD COLUMN generation_mode text default 'seo_and_attractiveness';
ALTER TABLE content_jobs ADD COLUMN content_goal text;
ALTER TABLE content_jobs ADD COLUMN call_to_action text;
ALTER TABLE content_jobs ADD COLUMN target_audience_override text;
ALTER TABLE content_jobs ADD COLUMN persona_override text;
ALTER TABLE content_jobs ADD COLUMN tone_override text;
ALTER TABLE content_jobs ADD COLUMN attractiveness_report_json jsonb;
ALTER TABLE content_jobs ADD COLUMN attractiveness_score numeric;
