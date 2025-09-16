-- EasyInterns Database Initialization Script
-- Run this in your Supabase SQL editor or PostgreSQL database

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    location TEXT,
    school TEXT,
    degree TEXT,
    graduation_year INTEGER,
    gpa DECIMAL(3,2),
    skills TEXT[],
    interests TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create companies table
CREATE TABLE IF NOT EXISTS public.companies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    description TEXT,
    industry TEXT,
    size TEXT,
    headquarters TEXT,
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, domain)
);

-- Create sources table
CREATE TABLE IF NOT EXISTS public.sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    base_url TEXT,
    is_active BOOLEAN DEFAULT true,
    rate_limit INTEGER DEFAULT 100,
    last_scraped TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create internships table
CREATE TABLE IF NOT EXISTS public.internships (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE,
    location TEXT,
    description TEXT,
    requirements TEXT,
    benefits TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    modality TEXT CHECK (modality IN ('remote', 'hybrid', 'onsite')),
    field_tag TEXT NOT NULL,
    apply_url TEXT NOT NULL,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    posting_date DATE,
    deadline DATE,
    is_government BOOLEAN DEFAULT false,
    relevance_score DECIMAL(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, external_id)
);

-- Create contact_emails table
CREATE TABLE IF NOT EXISTS public.contact_emails (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    internship_id UUID REFERENCES public.internships(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    title TEXT,
    confidence_score DECIMAL(3,2),
    extraction_method TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(internship_id, email)
);

-- Create resumes table
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    template TEXT NOT NULL,
    content JSONB,
    is_ai_enhanced BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create bookmarks table
CREATE TABLE IF NOT EXISTS public.bookmarks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    internship_id UUID REFERENCES public.internships(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, internship_id)
);

-- Create click_logs table
CREATE TABLE IF NOT EXISTS public.click_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    internship_id UUID REFERENCES public.internships(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_internships_field_tag ON public.internships(field_tag);
CREATE INDEX IF NOT EXISTS idx_internships_modality ON public.internships(modality);
CREATE INDEX IF NOT EXISTS idx_internships_location ON public.internships(location);
CREATE INDEX IF NOT EXISTS idx_internships_posting_date ON public.internships(posting_date DESC);
CREATE INDEX IF NOT EXISTS idx_internships_company_id ON public.internships(company_id);
CREATE INDEX IF NOT EXISTS idx_internships_source ON public.internships(source);
CREATE INDEX IF NOT EXISTS idx_internships_relevance_score ON public.internships(relevance_score DESC);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_internships_title_search ON public.internships USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_internships_description_search ON public.internships USING gin(to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_companies_name_search ON public.companies USING gin(to_tsvector('english', name));

-- Trigram indexes for fuzzy search
CREATE INDEX IF NOT EXISTS idx_internships_title_trgm ON public.internships USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON public.companies USING gin(name gin_trgm_ops);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_internships_field_modality ON public.internships(field_tag, modality);
CREATE INDEX IF NOT EXISTS idx_internships_location_field ON public.internships(location, field_tag);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.click_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for resumes table
CREATE POLICY "Users can view own resumes" ON public.resumes
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own resumes" ON public.resumes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own resumes" ON public.resumes
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own resumes" ON public.resumes
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for bookmarks table
CREATE POLICY "Users can view own bookmarks" ON public.bookmarks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own bookmarks" ON public.bookmarks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own bookmarks" ON public.bookmarks
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for click_logs table
CREATE POLICY "Users can create own click logs" ON public.click_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Public read access for companies, internships, contact_emails, sources
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.internships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contact_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view companies" ON public.companies FOR SELECT USING (true);
CREATE POLICY "Anyone can view internships" ON public.internships FOR SELECT USING (true);
CREATE POLICY "Anyone can view contact emails" ON public.contact_emails FOR SELECT USING (true);
CREATE POLICY "Anyone can view sources" ON public.sources FOR SELECT USING (true);

-- Insert initial sources
INSERT INTO public.sources (name, display_name, base_url, is_active) VALUES
    ('indeed', 'Indeed', 'https://indeed.com', true),
    ('talent', 'Talent.com', 'https://talent.com', true),
    ('job_bank', 'Job Bank Canada', 'https://jobbank.gc.ca', true),
    ('ops', 'Ontario Public Service', 'https://gojobs.gov.on.ca', true),
    ('bcps', 'BC Public Service', 'https://careers.gov.bc.ca', true),
    ('linkedin', 'LinkedIn', 'https://linkedin.com', false),
    ('glassdoor', 'Glassdoor', 'https://glassdoor.com', false)
ON CONFLICT (name) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON public.companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_internships_updated_at BEFORE UPDATE ON public.internships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON public.resumes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
