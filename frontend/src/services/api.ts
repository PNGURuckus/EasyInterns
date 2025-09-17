import { API_BASE_URL, API_PREFIX } from '@/config';

type PrimitiveParam = string | number | boolean

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  headers?: Record<string, string>;
  params?: Record<string, PrimitiveParam | PrimitiveParam[] | undefined>;
  authToken?: string | null;
};

class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<{ data: T; status: number }> {
  const {
    method = 'GET',
    body,
    headers = {},
    params = {},
    authToken,
  } = options;

  // Construct URL with query parameters
  const url = new URL(`${API_BASE_URL}${API_PREFIX}${endpoint}`);
  
  // Add query parameters
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return
    }

    if (Array.isArray(value)) {
      value.forEach((item) => url.searchParams.append(key, String(item)))
    } else {
      url.searchParams.append(key, String(value))
    }
  })

  // Set up headers
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (authToken) {
    defaultHeaders['Authorization'] = `Bearer ${authToken}`;
  }

  // Make the request
  const response = await fetch(url.toString(), {
    method,
    headers: { ...defaultHeaders, ...headers },
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });

  // Handle response
  let responseData;
  const contentType = response.headers.get('content-type');
  
  if (contentType && contentType.includes('application/json')) {
    responseData = await response.json();
  } else if (contentType && contentType.includes('text/')) {
    responseData = await response.text();
  } else if (response.status !== 204) { // 204 is No Content
    responseData = await response.blob();
  }

  if (!response.ok) {
    const errorMessage =
      responseData?.detail ||
      responseData?.message ||
      response.statusText ||
      `Request failed with status ${response.status}`;
    
    throw new ApiError(errorMessage, response.status, responseData);
  }

  return { data: responseData, status: response.status };
}

// Internship API methods
export const internshipApi = {
  async getInternships(params: {
    skip?: number;
    limit?: number;
    query?: string;
    location?: string;
    locations?: string[];
    is_remote?: boolean;
    min_salary?: number;
    max_salary?: number;
    company_id?: string;
    posted_within_days?: number;
  } = {}) {
    const { data } = await apiRequest<{ items: any[]; total: number }>(
      '/internships/search',
      { params }
    );
    return data;
  },

  async getInternship(id: string) {
    const { data } = await apiRequest<{ item: any }>(`/internships/${id}`);
    return data.item;
  },

  async getInternshipStats(companyId?: string) {
    const { data } = await apiRequest<{ stats: any }>(
      '/internships/stats',
      { params: companyId ? { company_id: companyId } : {} }
    );
    return data.stats;
  },

  async getCompanyInternships(companyId: string, params: { skip?: number; limit?: number } = {}) {
    const { data } = await apiRequest<{ items: any[]; total: number }>(
      `/internships/company/${companyId}`,
      { params }
    );
    return data;
  },
};
