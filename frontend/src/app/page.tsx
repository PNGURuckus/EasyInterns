"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Search } from "lucide-react"
import { internshipApi } from "@/services/api"
import { useQuery } from "@tanstack/react-query"

type Internship = {
  id: string
  title: string
  company: string
  company_id?: string
  location: string
  is_remote: boolean
  posted_date: string
  application_deadline: string
  salary_range?: string
  type: string
  description?: string
  city?: string
  region?: string
  apply_url?: string
  created_at?: string
  updated_at?: string
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("")
  const [locationQuery, setLocationQuery] = useState("")
  const [isRemote, setIsRemote] = useState(false)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['internships', { searchQuery, locationQuery, isRemote }],
    queryFn: () => 
      internshipApi.getInternships({
        query: searchQuery || undefined,
        location: locationQuery || undefined,
        is_remote: isRemote || undefined,
        limit: 50,
      }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const internships = data?.items || []
  const loading = isLoading
  const errorMessage = isError ? (error instanceof Error ? error.message : 'Failed to load internships') : null

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const filteredInternships = internships.filter(internship => 
    internship.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    internship.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
    internship.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return (
      <div className="container py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold tracking-tight mb-4">Find Your Dream Internship</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Discover the best internship opportunities across Canada
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="h-full flex flex-col">
              <CardHeader>
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent className="flex-1 space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
              </CardContent>
              <CardFooter className="flex justify-between">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-9 w-24" />
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (errorMessage) {
    return (
      <div className="container py-12 text-center">
        <div className="bg-destructive/10 text-destructive p-6 rounded-lg inline-block">
          <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="mb-4">{errorMessage}</p>
          <Button variant="outline" onClick={() => refetch()}>
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight mb-4">Find Your Dream Internship</h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
          Discover the best internship opportunities across Canada
        </p>
        
        <div className="max-w-4xl mx-auto grid gap-4 grid-cols-1 md:grid-cols-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by title, company, or keyword"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pl-10 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="relative">
            <input
              type="text"
              placeholder="Location"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                checked={isRemote}
                onChange={(e) => setIsRemote(e.target.checked)}
              />
              Remote Only
            </label>
            <Button onClick={() => refetch()} className="w-full md:w-auto">
              Search
            </Button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">Latest Opportunities</h2>
        <div className="text-sm text-muted-foreground">
          {filteredInternships.length} {filteredInternships.length === 1 ? 'internship' : 'internships'} available
        </div>
      </div>

      {filteredInternships.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No internships found matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredInternships.map((internship) => (
            <Card key={internship.id} className="h-full flex flex-col hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="secondary" className="text-xs">
                    {internship.type}
                  </Badge>
                  {internship.is_remote && (
                    <Badge variant="outline" className="text-xs">
                      Remote
                    </Badge>
                  )}
                </div>
                <CardTitle className="text-xl">{internship.title}</CardTitle>
                <p className="text-sm text-muted-foreground">{internship.company}</p>
              </CardHeader>
              <CardContent className="flex-1 space-y-2">
                <div className="flex items-center text-sm">
                  <span className="text-muted-foreground">Location:</span>
                  <span className="ml-2">
                    {internship.city && internship.region 
                      ? `${internship.city}, ${internship.region}` 
                      : internship.location}
                  </span>
                </div>
                {internship.salary_range && (
                  <div className="flex items-center text-sm">
                    <span className="text-muted-foreground">Salary:</span>
                    <span className="ml-2 font-medium">{internship.salary_range}</span>
                  </div>
                )}
                <div className="flex items-center text-sm">
                  <span className="text-muted-foreground">Posted:</span>
                  <span className="ml-2">{formatDate(internship.posted_date)}</span>
                </div>
                {internship.application_deadline && (
                  <div className="flex items-center text-sm">
                    <span className="text-muted-foreground">Deadline:</span>
                    <span className="ml-2">{formatDate(internship.application_deadline)}</span>
                  </div>
                )}
                {internship.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2 mt-2">
                    {internship.description}
                  </p>
                )}
              </CardContent>
              <CardFooter className="mt-auto">
                <div className="w-full flex gap-2">
                  {internship.apply_url && (
                    <Button asChild variant="outline" className="flex-1">
                      <a href={internship.apply_url} target="_blank" rel="noopener noreferrer">
                        Apply Now
                      </a>
                    </Button>
                  )}
                  <Button asChild className="flex-1">
                    <Link href={`/internships/${internship.id}`}>
                      View Details
                    </Link>
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
