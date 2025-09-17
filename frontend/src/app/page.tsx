"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { LocationFilter } from "@/components/location-filter"
import { LocationOption, LocationScope } from "@/data/locations"
import { internshipApi } from "@/services/api"

const normalize = (value?: string) =>
  value ? value.toLowerCase().replace(/\s+/g, " ").trim() : ""

type Internship = {
  id: string
  title: string
  company: string
  company_id?: string
  location: string
  city?: string
  region?: string
  country?: string
  location_type?: string
  work_location?: string
  is_remote?: boolean
  posted_date: string
  application_deadline: string
  salary_range?: string
  type: string
  description?: string
  apply_url?: string
  created_at?: string
  updated_at?: string
}

const detectRemote = (internship: Internship) => {
  if (typeof internship.is_remote === "boolean") return internship.is_remote
  const locationType = internship.location_type ?? internship.work_location
  if (locationType && normalize(locationType).includes("remote")) return true
  const locationText = internship.location ?? ""
  return /remote|work from home|telecommute/i.test(locationText)
}

const extractLocationParts = (internship: Internship) => {
  const fallback = internship.location ? internship.location.split(",").map((part) => part.trim()) : []
  return {
    city: internship.city ?? fallback[0] ?? "",
    region: internship.region ?? fallback[1] ?? "",
    country: internship.country ?? fallback[fallback.length - 1] ?? "Canada",
  }
}

const matchesLocation = (
  internship: Internship,
  scope: LocationScope,
  selections: LocationOption[]
) => {
  if (scope === "remote") {
    return detectRemote(internship)
  }

  if (selections.length === 0) {
    return true
  }

  const { city, region, country } = extractLocationParts(internship)
  return selections.some((selection) => {
    switch (scope) {
      case "city":
        return (
          normalize(city) === normalize(selection.city) ||
          normalize(`${city}, ${region}`) === normalize(selection.label)
        )
      case "region":
        return normalize(region) === normalize(selection.region)
      case "country":
        return normalize(country) === normalize(selection.country)
      default:
        return true
    }
  })
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedLocations, setSelectedLocations] = useState<LocationOption[]>([])
  const [locationScope, setLocationScope] = useState<LocationScope>("city")

  const queryParams = useMemo(() => {
    const params: Record<string, string | number | boolean | string[] | undefined> = {
      limit: 100,
    }

    if (locationScope === "remote") {
      params.is_remote = true
    } else if (locationScope === "city" && selectedLocations.length > 0) {
      params.locations = selectedLocations.map((loc) => loc.label)
    }

    return params
  }, [locationScope, selectedLocations])

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["internships", queryParams],
    queryFn: () => internshipApi.getInternships(queryParams),
    staleTime: 5 * 60 * 1000,
  })

  const internships = data?.items || []
  const normalizedSearch = searchQuery.toLowerCase().trim()

  const filteredInternships = useMemo(() => {
    const locationFiltered = internships.filter((internship) =>
      matchesLocation(internship, locationScope, selectedLocations)
    )

    if (!normalizedSearch) {
      return locationFiltered
    }

    return locationFiltered.filter((internship) =>
      internship.title.toLowerCase().includes(normalizedSearch) ||
      internship.company.toLowerCase().includes(normalizedSearch) ||
      internship.description?.toLowerCase().includes(normalizedSearch)
    )
  }, [internships, locationScope, selectedLocations, normalizedSearch])

  const errorMessage = isError
    ? error instanceof Error
      ? error.message
      : "Failed to load internships"
    : null

  if (isLoading) {
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
    <div className="container py-12 space-y-10">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-4">Find Your Dream Internship</h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-6">
          Discover curated internships across Canada and tailor results by location, modality, and focus areas.
        </p>

        <div className="max-w-3xl mx-auto grid gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by title, company, or keyword"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pl-10 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
            />
          </div>
          <Button onClick={() => refetch()} className="justify-self-center md:w-auto">
            Refresh Results
          </Button>
        </div>
      </div>

      <LocationFilter
        selectedLocations={selectedLocations}
        scope={locationScope}
        onScopeChange={(scope) => {
          setLocationScope(scope)
          if (scope === "remote") {
            setSelectedLocations([])
          }
        }}
        onLocationsChange={setSelectedLocations}
      />

      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Latest Opportunities</h2>
        <div className="text-sm text-muted-foreground">
          {filteredInternships.length} {filteredInternships.length === 1 ? "internship" : "internships"} available
        </div>
      </div>

      {filteredInternships.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No internships found matching your filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredInternships.map((internship) => {
            const { city, region } = extractLocationParts(internship)
            const displayLocation = city
              ? region
                ? `${city}, ${region}`
                : city
              : internship.location

            return (
              <Card key={internship.id} className="h-full flex flex-col hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="secondary" className="text-xs">
                      {internship.type}
                    </Badge>
                    {detectRemote(internship) && (
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
                    <span className="ml-2">{displayLocation}</span>
                  </div>
                  {internship.salary_range && (
                    <div className="flex items-center text-sm">
                      <span className="text-muted-foreground">Salary:</span>
                      <span className="ml-2 font-medium">{internship.salary_range}</span>
                    </div>
                  )}
                  {internship.description && (
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {internship.description}
                    </p>
                  )}
                </CardContent>
                <CardFooter className="flex items-center justify-between text-sm">
                  <div className="text-muted-foreground">
                    Posted {new Date(internship.posted_date).toLocaleDateString()}
                  </div>
                  {internship.apply_url ? (
                    <Button asChild size="sm">
                      <Link href={internship.apply_url} target="_blank" rel="noopener noreferrer">
                        View Role
                      </Link>
                    </Button>
                  ) : (
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/internships/${internship.id}`}>Details</Link>
                    </Button>
                  )}
                </CardFooter>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
