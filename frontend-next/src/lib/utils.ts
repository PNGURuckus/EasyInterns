import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatSalary(min?: number, max?: number): string {
  if (!min && !max) return 'Salary not specified'
  
  const formatter = new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })
  
  if (min && max && min !== max) {
    return `${formatter.format(min)} - ${formatter.format(max)}`
  }
  
  return formatter.format(min || max || 0)
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(d)
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffInMs = now.getTime() - d.getTime()
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))
  
  if (diffInDays === 0) return 'Today'
  if (diffInDays === 1) return 'Yesterday'
  if (diffInDays < 7) return `${diffInDays} days ago`
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`
  
  return `${Math.floor(diffInDays / 365)} years ago`
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length).trim() + '...'
}

export function getFieldTagLabel(fieldTag: string): string {
  const labels: Record<string, string> = {
    'software_engineering': 'Software Engineering',
    'data_science': 'Data Science',
    'product_management': 'Product Management',
    'design': 'Design',
    'marketing': 'Marketing',
    'sales': 'Sales',
    'finance': 'Finance',
    'consulting': 'Consulting',
    'research': 'Research',
    'operations': 'Operations',
    'other': 'Other'
  }
  
  return labels[fieldTag] || fieldTag
}

export function getModalityLabel(modality: string): string {
  const labels: Record<string, string> = {
    'remote': 'Remote',
    'hybrid': 'Hybrid',
    'onsite': 'On-site'
  }
  
  return labels[modality] || modality
}

export function getModalityColor(modality: string): string {
  const colors: Record<string, string> = {
    'remote': 'bg-green-100 text-green-800',
    'hybrid': 'bg-blue-100 text-blue-800',
    'onsite': 'bg-gray-100 text-gray-800'
  }
  
  return colors[modality] || 'bg-gray-100 text-gray-800'
}

export function extractDomain(url: string): string {
  try {
    const domain = new URL(url).hostname
    return domain.replace('www.', '')
  } catch {
    return ''
  }
}

export function generateCompanyLogoUrl(domain: string): string {
  if (!domain) return '/placeholder-company.png'
  return `https://logo.clearbit.com/${domain}?size=64&fallback=404`
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}
