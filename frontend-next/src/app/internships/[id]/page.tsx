'use client'

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
  Mail,
  Copy,
  Calendar,
  Users,
  Award
} from 'lucide-react'
import Link from 'next/link'
import { formatSalary, formatDate, getFieldTagLabel, getModalityLabel, getModalityColor, generateCompanyLogoUrl } from '@/lib/utils'
import { useState } from 'react'
import Image from 'next/image'

export default function InternshipDetailPage({ params }: { params: { id: string } }) {
  const [bookmarked, setBookmarked] = useState(false)
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null)

  const { data: internshipResponse, isLoading, error } = useQuery({
    queryKey: ['internship', params.id],
    queryFn: () => apiClient.getInternship(params.id),
    enabled: !!params.id,
  })

  const internship = internshipResponse?.success ? internshipResponse.data : null

  const handleBookmark = async () => {
    if (!internship) return
    
    try {
      if (bookmarked) {
        await apiClient.removeBookmark(internship.id)
      } else {
        await apiClient.addBookmark(internship.id)
      }
      setBookmarked(!bookmarked)
    } catch (error) {
      console.error('Failed to toggle bookmark:', error)
    }
  }

  const handleApply = async () => {
    if (!internship) return
    
    try {
      await apiClient.logInternshipApply(internship.id)
      window.open(internship.apply_url, '_blank')
    } catch (error) {
      console.error('Failed to log application:', error)
    }
  }

  const handleCopyEmail = async (email: string) => {
    try {
      await navigator.clipboard.writeText(email)
      await apiClient.logEmailCopy(internship!.id, email)
      setCopiedEmail(email)
      setTimeout(() => setCopiedEmail(null), 2000)
    } catch (error) {
      console.error('Failed to copy email:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading internship details...</p>
        </div>
      </div>
    )
  }

  if (error || !internship) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="text-center py-8">
            <p className="text-red-600">Failed to load internship details.</p>
            <Button asChild className="mt-4">
              <Link href="/browse">Back to Browse</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-6 py-8 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {internship.title}
              </h1>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  {internship.company?.domain && (
                    <Image
                      src={generateCompanyLogoUrl(internship.company.domain)}
                      alt={`${internship.company.name} logo`}
                      width={24}
                      height={24}
                      className="rounded"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                  )}
                  <Building className="h-5 w-5 text-gray-400" />
                  <span className="text-lg font-medium text-gray-700">
                    {internship.company?.name}
                  </span>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getModalityColor(internship.modality)}`}>
                  {getModalityLabel(internship.modality)}
                </span>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {getFieldTagLabel(internship.field_tag)}
                </span>
                {internship.is_government && (
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                    Government Position
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={handleBookmark}
                className={bookmarked ? 'bg-blue-50 text-blue-600' : ''}
              >
                <Bookmark className="h-4 w-4 mr-2" />
                {bookmarked ? 'Saved' : 'Save'}
              </Button>
              
              <Button onClick={handleApply} className="px-6">
                <ExternalLink className="h-4 w-4 mr-2" />
                Apply Now
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Job Details */}
            <Card>
              <CardHeader>
                <CardTitle>Job Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {internship.location && (
                    <div className="flex items-center gap-2">
                      <MapPin className="h-5 w-5 text-gray-400" />
                      <span>{internship.location}</span>
                    </div>
                  )}
                  
                  {(internship.salary_min || internship.salary_max) && (
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-gray-400" />
                      <span>{formatSalary(internship.salary_min, internship.salary_max)}</span>
                    </div>
                  )}
                  
                  {internship.posting_date && (
                    <div className="flex items-center gap-2">
                      <Clock className="h-5 w-5 text-gray-400" />
                      <span>Posted {formatDate(internship.posting_date)}</span>
                    </div>
                  )}
                  
                  {internship.deadline && (
                    <div className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-gray-400" />
                      <span>Deadline {formatDate(internship.deadline)}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            {internship.description && (
              <Card>
                <CardHeader>
                  <CardTitle>Job Description</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap">{internship.description}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Requirements */}
            {internship.requirements && (
              <Card>
                <CardHeader>
                  <CardTitle>Requirements</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap">{internship.requirements}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Benefits */}
            {internship.benefits && (
              <Card>
                <CardHeader>
                  <CardTitle>Benefits</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap">{internship.benefits}</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Apply */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Apply</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={handleApply} className="w-full">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Apply on Company Site
                </Button>
                
                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    or build a tailored resume
                  </p>
                  <Button variant="outline" className="w-full mt-2" asChild>
                    <Link href={`/resume?internship=${internship.id}`}>
                      <Award className="h-4 w-4 mr-2" />
                      Build Resume
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Contact Information */}
            {internship.contact_emails && internship.contact_emails.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Contact Information</CardTitle>
                  <CardDescription>
                    Reach out directly to hiring managers
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {internship.contact_emails.map((contact, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-gray-400" />
                        <span className="text-sm">{contact.email}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyEmail(contact.email)}
                      >
                        {copiedEmail === contact.email ? (
                          <span className="text-green-600 text-xs">Copied!</span>
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Company Info */}
            {internship.company && (
              <Card>
                <CardHeader>
                  <CardTitle>About {internship.company.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  {internship.company.description ? (
                    <p className="text-sm text-gray-600">{internship.company.description}</p>
                  ) : (
                    <p className="text-sm text-gray-500 italic">
                      Company information not available
                    </p>
                  )}
                  
                  {internship.company.domain && (
                    <div className="mt-4">
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`https://${internship.company.domain}`} target="_blank">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Visit Website
                        </Link>
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Similar Jobs */}
            <Card>
              <CardHeader>
                <CardTitle>Similar Opportunities</CardTitle>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full" asChild>
                  <Link href={`/browse?field_tags=${internship.field_tag}`}>
                    <Users className="h-4 w-4 mr-2" />
                    View Similar Jobs
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
