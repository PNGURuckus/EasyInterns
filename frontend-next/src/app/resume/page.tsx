'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { 
  FileText, 
  Download, 
  Eye, 
  Edit3, 
  Trash2, 
  Plus,
  Sparkles,
  Copy
} from 'lucide-react'
import Link from 'next/link'
import { Resume } from '@/types'
import { formatDate } from '@/lib/utils'

export default function ResumePage() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [selectedTemplate, setSelectedTemplate] = useState<string>('ats_clean')

  const { data: resumesResponse, isLoading } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => apiClient.getResumes(),
    enabled: !!user,
  })

  const createResumeMutation = useMutation({
    mutationFn: (template: string) => apiClient.createResume({ template }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
    },
  })

  const deleteResumeMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
    },
  })

  const resumes = resumesResponse?.success ? resumesResponse.data : []

  const handleCreateResume = () => {
    createResumeMutation.mutate(selectedTemplate)
  }

  const handleDeleteResume = (id: string) => {
    if (confirm('Are you sure you want to delete this resume?')) {
      deleteResumeMutation.mutate(id)
    }
  }

  const handleDownloadPDF = async (id: string) => {
    try {
      const response = await apiClient.downloadResumePDF(id)
      // Handle PDF download
      const blob = new Blob([response], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `resume-${id}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download PDF:', error)
    }
  }

  const templates = [
    {
      id: 'ats_clean',
      name: 'ATS Clean',
      description: 'Simple, ATS-friendly format that passes automated screening',
      preview: '/templates/ats-clean-preview.png'
    },
    {
      id: 'modern_two_column',
      name: 'Modern Two Column',
      description: 'Professional two-column layout with visual hierarchy',
      preview: '/templates/modern-two-column-preview.png'
    },
    {
      id: 'creative_accent',
      name: 'Creative Accent',
      description: 'Creative design with color accents for design roles',
      preview: '/templates/creative-accent-preview.png'
    },
    {
      id: 'compact_student',
      name: 'Compact Student',
      description: 'Optimized for students with limited experience',
      preview: '/templates/compact-student-preview.png'
    }
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading resumes...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="text-center py-8">
            <p className="text-gray-600">Please sign in to manage your resumes.</p>
            <Button asChild className="mt-4">
              <Link href="/auth/signin">Sign In</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-6xl px-6 py-8 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Resume Builder</h1>
          <p className="text-gray-600">Create professional resumes tailored for internship applications</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Resume List */}
          <div className="lg:col-span-2">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Your Resumes</h2>
              <Button onClick={handleCreateResume} disabled={createResumeMutation.isPending}>
                <Plus className="h-4 w-4 mr-2" />
                {createResumeMutation.isPending ? 'Creating...' : 'New Resume'}
              </Button>
            </div>

            {resumes.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No resumes yet</h3>
                  <p className="text-gray-600 mb-6">
                    Create your first resume to start applying for internships.
                  </p>
                  <Button onClick={handleCreateResume} disabled={createResumeMutation.isPending}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Your First Resume
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {resumes.map((resume) => (
                  <ResumeCard
                    key={resume.id}
                    resume={resume}
                    onDelete={handleDeleteResume}
                    onDownload={handleDownloadPDF}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Template Selection */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Choose Template</h2>
            <div className="space-y-4">
              {templates.map((template) => (
                <Card
                  key={template.id}
                  className={`cursor-pointer transition-all ${
                    selectedTemplate === template.id 
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => setSelectedTemplate(template.id)}
                >
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription className="text-sm">
                      {template.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="aspect-[3/4] bg-gray-100 rounded border flex items-center justify-center">
                      <FileText className="h-8 w-8 text-gray-400" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* AI Enhancement */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-yellow-500" />
                  AI Enhancement
                </CardTitle>
                <CardDescription>
                  Let AI optimize your resume for specific internships
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Our AI can tailor your resume content, highlight relevant skills, 
                  and improve formatting for better ATS compatibility.
                </p>
                <Button variant="outline" className="w-full">
                  <Sparkles className="h-4 w-4 mr-2" />
                  Enhance with AI
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

function ResumeCard({ 
  resume, 
  onDelete, 
  onDownload 
}: { 
  resume: Resume
  onDelete: (id: string) => void
  onDownload: (id: string) => void
}) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await onDelete(resume.id)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg">{resume.title}</CardTitle>
            <CardDescription className="mt-1">
              Template: {resume.template} • Updated {formatDate(resume.updated_at)}
            </CardDescription>
          </div>
          
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/resume/${resume.id}/preview`}>
                <Eye className="h-4 w-4" />
              </Link>
            </Button>
            
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/resume/${resume.id}/edit`}>
                <Edit3 className="h-4 w-4" />
              </Link>
            </Button>
            
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => onDownload(resume.id)}
            >
              <Download className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          {resume.content && (
            <div className="text-sm text-gray-600">
              <p className="line-clamp-2">{resume.content.summary || 'No summary available'}</p>
            </div>
          )}
          
          <div className="flex justify-between items-center pt-2 border-t">
            <div className="flex gap-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                {resume.template.replace('_', ' ').toUpperCase()}
              </span>
              {resume.is_ai_enhanced && (
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  AI Enhanced
                </span>
              )}
            </div>
            
            <div className="flex gap-2">
              <Button size="sm" variant="outline" asChild>
                <Link href={`/resume/${resume.id}/duplicate`}>
                  <Copy className="h-4 w-4 mr-1" />
                  Duplicate
                </Link>
              </Button>
              
              <Button size="sm" asChild>
                <Link href={`/resume/${resume.id}/edit`}>
                  Edit Resume
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
