'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { 
  MapPin, 
  Building, 
  Clock, 
  DollarSign,
  Bookmark,
  ExternalLink,
  Trash2,
  Search
} from 'lucide-react'
import Link from 'next/link'
import { formatSalary, formatRelativeTime, getFieldTagLabel, getModalityLabel, getModalityColor } from '@/lib/utils'
import { Internship } from '@/types'

export default function SavedPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const { data: bookmarksResponse, isLoading, error, refetch } = useQuery({
    queryKey: ['bookmarks'],
    queryFn: () => apiClient.getBookmarks(),
  })

  const bookmarks = bookmarksResponse?.success ? bookmarksResponse.data : []

  const handleRemoveBookmark = async (internshipId: string) => {
    try {
      await apiClient.removeBookmark(internshipId)
      refetch()
    } catch (error) {
      console.error('Failed to remove bookmark:', error)
    }
  }

  const filteredBookmarks = bookmarks.filter(bookmark =>
    bookmark.internship.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    bookmark.internship.company?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    bookmark.internship.location?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading saved internships...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-6xl px-6 py-8 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Saved Internships</h1>
          <p className="text-gray-600">Keep track of opportunities you're interested in</p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search saved internships..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Content */}
        {error && (
          <Card>
            <CardContent className="text-center py-8">
              <p className="text-red-600">Failed to load saved internships. Please try again.</p>
              <Button onClick={() => refetch()} className="mt-4">
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {bookmarks.length === 0 && !isLoading && (
          <Card>
            <CardContent className="text-center py-12">
              <Bookmark className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No saved internships yet</h3>
              <p className="text-gray-600 mb-6">
                Start browsing and save internships you're interested in to keep track of them here.
              </p>
              <Button asChild>
                <Link href="/browse">
                  Browse Internships
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {filteredBookmarks.length > 0 && (
          <>
            <div className="mb-4">
              <p className="text-gray-600">
                {filteredBookmarks.length} saved internship{filteredBookmarks.length !== 1 ? 's' : ''}
                {searchQuery && ` matching "${searchQuery}"`}
              </p>
            </div>

            <div className="space-y-4">
              {filteredBookmarks.map((bookmark) => (
                <SavedInternshipCard
                  key={bookmark.id}
                  bookmark={bookmark}
                  onRemove={handleRemoveBookmark}
                />
              ))}
            </div>
          </>
        )}

        {searchQuery && filteredBookmarks.length === 0 && bookmarks.length > 0 && (
          <Card>
            <CardContent className="text-center py-8">
              <p className="text-gray-600">No saved internships match your search.</p>
              <Button
                variant="outline"
                onClick={() => setSearchQuery('')}
                className="mt-4"
              >
                Clear search
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function SavedInternshipCard({ 
  bookmark, 
  onRemove 
}: { 
  bookmark: { id: string; internship: Internship; created_at: string }
  onRemove: (id: string) => void 
}) {
  const { internship } = bookmark

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
              onClick={() => onRemove(internship.id)}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
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

          <div className="flex justify-between items-center pt-2 border-t">
            <p className="text-xs text-gray-500">
              Saved {formatRelativeTime(bookmark.created_at)}
            </p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" asChild>
                <Link href={`/resume?internship=${internship.id}`}>
                  Build Resume
                </Link>
              </Button>
              <Button size="sm" asChild>
                <Link href={`/internships/${internship.id}`}>
                  View Details
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
