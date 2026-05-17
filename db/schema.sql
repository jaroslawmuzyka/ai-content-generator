-- Utworzenie funkcji do automatycznej aktualizacji pola updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Tabela: operators
CREATE TABLE operators (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    is_active boolean default true,
    created_at timestamptz default now()
);

-- Tabela: campaigns
CREATE TABLE campaigns (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text,
    default_content_type text,
    default_language text default 'pl',
    default_locale text default 'pl-PL',
    default_provider text default 'openai',
    default_model text,
    status text default 'active',
    created_by text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

CREATE TRIGGER update_campaigns_modtime
BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tabela: default_prompt_sets
CREATE TABLE default_prompt_sets (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    content_type text not null,
    language text,
    description text,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

CREATE TRIGGER update_default_prompt_sets_modtime
BEFORE UPDATE ON default_prompt_sets FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tabela: default_prompt_steps
CREATE TABLE default_prompt_steps (
    id uuid primary key default gen_random_uuid(),
    default_prompt_set_id uuid references default_prompt_sets(id) on delete cascade,
    step_order integer not null,
    step_key text not null,
    step_name text not null,
    system_prompt text,
    user_prompt text not null,
    default_provider text default 'openai',
    default_model text,
    temperature numeric default 0.7,
    max_tokens integer,
    output_type text default 'text',
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

CREATE TRIGGER update_default_prompt_steps_modtime
BEFORE UPDATE ON default_prompt_steps FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tabela: campaign_prompt_sets
CREATE TABLE campaign_prompt_sets (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references campaigns(id) on delete cascade,
    name text not null,
    source_default_prompt_set_id uuid references default_prompt_sets(id),
    content_type text not null,
    language text,
    version integer default 1,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

CREATE TRIGGER update_campaign_prompt_sets_modtime
BEFORE UPDATE ON campaign_prompt_sets FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tabela: campaign_prompt_steps
CREATE TABLE campaign_prompt_steps (
    id uuid primary key default gen_random_uuid(),
    campaign_prompt_set_id uuid references campaign_prompt_sets(id) on delete cascade,
    step_order integer not null,
    step_key text not null,
    step_name text not null,
    system_prompt text,
    user_prompt text not null,
    provider text default 'openai',
    model text,
    temperature numeric default 0.7,
    max_tokens integer,
    output_type text default 'text',
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

CREATE TRIGGER update_campaign_prompt_steps_modtime
BEFORE UPDATE ON campaign_prompt_steps FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tabela: content_jobs
CREATE TABLE content_jobs (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references campaigns(id) on delete cascade,
    operator_name text,
    content_type text not null,
    language text default 'pl',
    locale text default 'pl-PL',
    url text,
    is_existing_url boolean default false,
    main_keyword text not null,
    secondary_keywords text,
    target_length integer,
    current_content text,
    additional_notes text,
    provider text default 'openai',
    model text,
    status text default 'draft',
    priority integer default 0,
    current_step_key text,
    final_html text,
    meta_title text,
    meta_description text,
    faq_html text,
    faq_json jsonb,
    seo_report_json jsonb,
    error_message text,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    started_at timestamptz,
    completed_at timestamptz
);

CREATE TRIGGER update_content_jobs_modtime
BEFORE UPDATE ON content_jobs FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Tabela: content_job_steps
CREATE TABLE content_job_steps (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references content_jobs(id) on delete cascade,
    step_order integer not null,
    step_key text not null,
    step_name text not null,
    status text default 'pending',
    provider text,
    model text,
    system_prompt_used text,
    user_prompt_used text,
    input_payload_json jsonb,
    output_text text,
    output_json jsonb,
    input_tokens integer,
    output_tokens integer,
    estimated_cost numeric,
    error_message text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz default now()
);

-- Tabela: job_prompt_snapshots
CREATE TABLE job_prompt_snapshots (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references content_jobs(id) on delete cascade,
    step_order integer not null,
    step_key text not null,
    step_name text not null,
    system_prompt_snapshot text,
    user_prompt_snapshot text,
    provider text,
    model text,
    temperature numeric,
    max_tokens integer,
    is_active boolean default true,
    created_at timestamptz default now()
);

-- Tabela: exports
CREATE TABLE exports (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid references campaigns(id),
    operator_name text,
    export_type text,
    file_name text,
    filters_json jsonb,
    created_at timestamptz default now()
);

-- Indeksy dla optymalizacji wyszukiwań
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaign_prompt_sets_campaign_id ON campaign_prompt_sets(campaign_id);
CREATE INDEX idx_content_jobs_campaign_id ON content_jobs(campaign_id);
CREATE INDEX idx_content_jobs_status ON content_jobs(status);
CREATE INDEX idx_content_jobs_priority ON content_jobs(priority DESC);
CREATE INDEX idx_content_jobs_created_at ON content_jobs(created_at DESC);
CREATE INDEX idx_content_job_steps_job_id ON content_job_steps(job_id);
CREATE INDEX idx_content_job_steps_status ON content_job_steps(status);
CREATE INDEX idx_job_prompt_snapshots_job_id ON job_prompt_snapshots(job_id);
CREATE INDEX idx_exports_campaign_id ON exports(campaign_id);
CREATE INDEX idx_exports_created_at ON exports(created_at DESC);
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

