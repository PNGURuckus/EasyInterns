import { createClientComponentClient, createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

export const createClient = () => {
  return createClientComponentClient()
}

export const createServerClient = () => {
  return createServerComponentClient({ cookies })
}

export type Database = {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          full_name: string | null
          avatar_url: string | null
          preferred_fields: string[] | null
          preferred_locations: string[] | null
          preferred_modality: string | null
          skills: string[] | null
          education_level: string | null
          graduation_year: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          avatar_url?: string | null
          preferred_fields?: string[] | null
          preferred_locations?: string[] | null
          preferred_modality?: string | null
          skills?: string[] | null
          education_level?: string | null
          graduation_year?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          avatar_url?: string | null
          preferred_fields?: string[] | null
          preferred_locations?: string[] | null
          preferred_modality?: string | null
          skills?: string[] | null
          education_level?: string | null
          graduation_year?: number | null
          created_at?: string
          updated_at?: string
        }
      }
    }
  }
}
