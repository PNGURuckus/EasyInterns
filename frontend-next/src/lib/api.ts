import { ApiResponse, SearchResponse, SearchFilters, Internship, User, Resume, ScrapeJob } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  setToken(token: string | null) {
    this.token = token
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || data.message || 'An error occurred',
        }
      }

      return {
        success: true,
        data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      }
    }
  }

  // Internships API
  async searchInternships(filters: SearchFilters = {}, page = 1, perPage = 20): Promise<ApiResponse<SearchResponse>> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    })

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v.toString()))
        } else {
          params.set(key, value.toString())
        }
      }
    })

    return this.request<SearchResponse>(`/api/internships?${params}`)
  }

  async getInternship(id: string): Promise<ApiResponse<Internship>> {
    return this.request<Internship>(`/api/internships/${id}`)
  }

  async logInternshipView(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/internships/${id}/view`, {
      method: 'POST',
    })
  }

  async logInternshipApply(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/internships/${id}/apply`, {
      method: 'POST',
    })
  }

  async logEmailCopy(id: string, email: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/internships/${id}/email-copy`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  }

  // User API
  async getProfile(): Promise<ApiResponse<User>> {
    return this.request<User>('/api/users/profile')
  }

  async updateProfile(data: Partial<User>): Promise<ApiResponse<User>> {
    return this.request<User>('/api/users/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getBookmarks(): Promise<ApiResponse<Internship[]>> {
    return this.request<Internship[]>('/api/users/bookmarks')
  }

  async addBookmark(internshipId: string): Promise<ApiResponse<void>> {
    return this.request<void>('/api/users/bookmarks', {
      method: 'POST',
      body: JSON.stringify({ internship_id: internshipId }),
    })
  }

  async removeBookmark(internshipId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/users/bookmarks/${internshipId}`, {
      method: 'DELETE',
    })
  }

  async getUserStats(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/users/stats')
  }

  // Resume API
  async getResumes(): Promise<ApiResponse<Resume[]>> {
    return this.request<Resume[]>('/api/resumes')
  }

  async getResume(id: string): Promise<ApiResponse<Resume>> {
    return this.request<Resume>(`/api/resumes/${id}`)
  }

  async createResume(data: Partial<Resume>): Promise<ApiResponse<Resume>> {
    return this.request<Resume>('/api/resumes', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateResume(id: string, data: Partial<Resume>): Promise<ApiResponse<Resume>> {
    return this.request<Resume>(`/api/resumes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteResume(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/resumes/${id}`, {
      method: 'DELETE',
    })
  }

  async exportResumePDF(id: string): Promise<ApiResponse<{ pdf_url: string }>> {
    return this.request<{ pdf_url: string }>(`/api/resumes/${id}/export`)
  }

  async enhanceResumeWithAI(id: string, internshipId?: string): Promise<ApiResponse<Resume>> {
    const body = internshipId ? JSON.stringify({ internship_id: internshipId }) : undefined
    return this.request<Resume>(`/api/resumes/${id}/enhance`, {
      method: 'POST',
      body,
    })
  }

  async getResumeTemplates(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/api/resumes/templates')
  }

  // Scraping API (Admin only)
  async startScrapeJob(sources: string[]): Promise<ApiResponse<ScrapeJob>> {
    return this.request<ScrapeJob>('/api/scrape/start', {
      method: 'POST',
      body: JSON.stringify({ sources }),
    })
  }

  async getScrapeJob(id: string): Promise<ApiResponse<ScrapeJob>> {
    return this.request<ScrapeJob>(`/api/scrape/jobs/${id}`)
  }

  async getScrapeJobs(): Promise<ApiResponse<ScrapeJob[]>> {
    return this.request<ScrapeJob[]>('/api/scrape/jobs')
  }

  async cancelScrapeJob(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/scrape/jobs/${id}/cancel`, {
      method: 'POST',
    })
  }

  async getScrapeStats(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/scrape/stats')
  }
}

export const apiClient = new ApiClient()
export default apiClient
