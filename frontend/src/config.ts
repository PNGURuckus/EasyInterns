// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';

// Authentication
export const AUTH_TOKEN_KEY = 'easyinterns_auth_token';

// Default pagination
const DEFAULT_PAGE_SIZE = 10;

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS: [DEFAULT_PAGE_SIZE, 20, 50],
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  AUTH: 'easyinterns_auth',
  THEME: 'theme',
  RECENT_SEARCHES: 'recent_searches',
} as const;
