export interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  preferred_fields?: string[]
  preferred_locations?: string[]
  preferred_modality?: 'remote' | 'hybrid' | 'onsite'
  skills?: string[]
  education_level?: string
  graduation_year?: number
  created_at: string
  updated_at: string
}

export interface Company {
  id: string
  name: string
  domain?: string
  logo_url?: string
  description?: string
  size?: string
  industry?: string
  created_at: string
  updated_at: string
}

export interface Internship {
  id: string
  title: string
  description?: string
  location?: string
  modality: 'remote' | 'hybrid' | 'onsite'
  field_tag: string
  apply_url: string
  external_id?: string
  salary_min?: number
  salary_max?: number
  posting_date?: string
  deadline?: string
  requirements?: string
  benefits?: string
  is_government: boolean
  relevance_score?: number
  company_id: string
  source_id: string
  created_at: string
  updated_at: string
  company?: Company
  contact_emails?: ContactEmail[]
  is_bookmarked?: boolean
}

export interface ContactEmail {
  id: string
  internship_id: string
  email: string
  confidence: number
  source_type: string
  verified: boolean
  created_at: string
}

export interface Resume {
  id: string
  user_id: string
  title: string
  template: string
  content: Record<string, any>
  pdf_url?: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface SearchFilters {
  query?: string
  field_tags?: string[]
  modality?: string[]
  locations?: string[]
  salary_min?: number
  salary_max?: number
  is_government?: boolean
  posted_after?: string
  company_ids?: string[]
  source_ids?: string[]
}

export interface SearchFacets {
  field_tags: Array<{ value: string; count: number }>
  modality: Array<{ value: string; count: number }>
  locations: Array<{ value: string; count: number }>
  companies: Array<{ value: string; count: number; company_name: string }>
  sources: Array<{ value: string; count: number; source_name: string }>
  salary_ranges: Array<{ min: number; max: number; count: number }>
}

export interface SearchResponse {
  internships: Internship[]
  total: number
  page: number
  per_page: number
  facets: SearchFacets
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface CandidateProfile {
  skills: string[]
  experience_level: string
  preferred_fields: string[]
  preferred_locations: string[]
  preferred_modality: string
  education_level: string
  graduation_year?: number
}

export interface ScrapeJob {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  sources: string[]
  progress: {
    current_source?: string
    completed_sources: number
    total_sources: number
    total_internships: number
    new_internships: number
    errors: string[]
  }
  result?: {
    total_sources: number
    total_internships: number
    new_internships: number
    completed_at: string
  }
  error?: string
  created_at: string
  updated_at: string
}
