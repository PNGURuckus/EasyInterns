'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSearchStore } from '@/lib/store'
import { apiClient } from '@/lib/api'
import { SearchFilters, Internship } from '@/types'
import { 
  Search, 
  Filter, 
  MapPin, 
  Building, 
  Clock, 
  DollarSign,
  Bookmark,
  ExternalLink
} from 'lucide-react'
import Link from 'next/link'
import { formatSalary, formatRelativeTime, getFieldTagLabel, getModalityLabel, getModalityColor } from '@/lib/utils'

export default function BrowsePage() {
  const { filters, query, setFilters, setQuery } = useSearchStore()
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)

  const { data: searchResults, isLoading, error } = useQuery({
    queryKey: ['internships', filters, query, page],
    queryFn: () => apiClient.searchInternships({ ...filters, query }, page, 20),
    enabled: true,
  })

  const handleSearch = (searchQuery: string) => {
    setQuery(searchQuery)
    setPage(1)
  }

  const handleFilterChange = (newFilters: Partial<SearchFilters>) => {
    setFilters(newFilters)
    setPage(1)
  }

  const handleBookmark = async (internshipId: string) => {
    try {
      await apiClient.addBookmark(internshipId)
      // Refresh the search results
    } catch (error) {
      console.error('Failed to bookmark internship:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-8">
        {/* Search Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Find Your Perfect Internship</h1>
          
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search internships, companies, or skills..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>
            
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              Filters
            </Button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Filter Internships</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Field
                  </label>
                  <select
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={filters.field_tags?.[0] || ''}
                    onChange={(e) => handleFilterChange({ 
                      field_tags: e.target.value ? [e.target.value] : undefined 
                    })}
                  >
                    <option value="">All Fields</option>
                    <option value="software_engineering">Software Engineering</option>
                    <option value="data_science">Data Science</option>
                    <option value="product_management">Product Management</option>
                    <option value="design">Design</option>
                    <option value="marketing">Marketing</option>
                    <option value="finance">Finance</option>
                    <option value="consulting">Consulting</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Work Mode
                  </label>
                  <select
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={filters.modality?.[0] || ''}
                    onChange={(e) => handleFilterChange({ 
                      modality: e.target.value ? [e.target.value] : undefined 
                    })}
                  >
                    <option value="">All Modes</option>
                    <option value="remote">Remote</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="onsite">On-site</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    placeholder="City, Province"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={filters.locations?.[0] || ''}
                    onChange={(e) => handleFilterChange({ 
                      locations: e.target.value ? [e.target.value] : undefined 
                    })}
                  />
                </div>
              </div>
              
              <div className="mt-4 flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setFilters({})
                    setQuery('')
                  }}
                >
                  Clear All
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Facets Sidebar */}
          <div className="lg:col-span-1">
            {searchResults?.success && searchResults.data?.facets && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Refine Results</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Field Tags */}
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-2">Field</h4>
                    <div className="space-y-1">
                      {searchResults.data.facets.field_tags.slice(0, 5).map((facet) => (
                        <button
                          key={facet.value}
                          className="flex justify-between w-full text-left text-sm hover:bg-gray-50 p-1 rounded"
                          onClick={() => handleFilterChange({ field_tags: [facet.value] })}
                        >
                          <span>{getFieldTagLabel(facet.value)}</span>
                          <span className="text-gray-500">{facet.count}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Modality */}
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-2">Work Mode</h4>
                    <div className="space-y-1">
                      {searchResults.data.facets.modality.map((facet) => (
                        <button
                          key={facet.value}
                          className="flex justify-between w-full text-left text-sm hover:bg-gray-50 p-1 rounded"
                          onClick={() => handleFilterChange({ modality: [facet.value] })}
                        >
                          <span>{getModalityLabel(facet.value)}</span>
                          <span className="text-gray-500">{facet.count}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Internship List */}
          <div className="lg:col-span-3">
            {isLoading && (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading internships...</p>
              </div>
            )}

            {error && (
              <Card>
                <CardContent className="text-center py-8">
                  <p className="text-red-600">Failed to load internships. Please try again.</p>
                </CardContent>
              </Card>
            )}

            {searchResults?.success && searchResults.data && (
              <>
                <div className="mb-4 flex justify-between items-center">
                  <p className="text-gray-600">
                    {searchResults.data.total} internships found
                  </p>
                </div>

                <div className="space-y-4">
                  {searchResults.data.internships.map((internship) => (
                    <InternshipCard 
                      key={internship.id} 
                      internship={internship}
                      onBookmark={handleBookmark}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {searchResults.data.total > 20 && (
                  <div className="mt-8 flex justify-center gap-2">
                    <Button
                      variant="outline"
                      disabled={page === 1}
                      onClick={() => setPage(page - 1)}
                    >
                      Previous
                    </Button>
                    <span className="flex items-center px-4">
                      Page {page} of {Math.ceil(searchResults.data.total / 20)}
                    </span>
                    <Button
                      variant="outline"
                      disabled={page >= Math.ceil(searchResults.data.total / 20)}
                      onClick={() => setPage(page + 1)}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function InternshipCard({ 
  internship, 
  onBookmark 
}: { 
  internship: Internship
  onBookmark: (id: string) => void 
}) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg">
              <Link 
                href={`/internships/${internship.id}`}
                className="hover:text-blue-600"
              >
                {internship.title}
              </Link>
            </CardTitle>
            <CardDescription className="flex items-center gap-2 mt-1">
              <Building className="h-4 w-4" />
              {internship.company?.name}
            </CardDescription>
          </div>
          
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onBookmark(internship.id)}
            >
              <Bookmark className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <Link href={internship.apply_url} target="_blank">
                <ExternalLink className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getModalityColor(internship.modality)}`}>
              {getModalityLabel(internship.modality)}
            </span>
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {getFieldTagLabel(internship.field_tag)}
            </span>
            {internship.is_government && (
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Government
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-600">
            {internship.location && (
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {internship.location}
              </div>
            )}
            
            {(internship.salary_min || internship.salary_max) && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-4 w-4" />
                {formatSalary(internship.salary_min, internship.salary_max)}
              </div>
            )}
            
            {internship.posting_date && (
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatRelativeTime(internship.posting_date)}
              </div>
            )}
          </div>
          
          {internship.description && (
            <p className="text-sm text-gray-700 line-clamp-2">
              {internship.description}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
