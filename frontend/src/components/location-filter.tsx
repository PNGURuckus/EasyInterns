"use client"

import { useMemo, useState } from "react"
import dynamic from "next/dynamic"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LocationOption, LocationScope, REGION_FILTERS, TOP_LOCATIONS } from "@/data/locations"

const LocationMap = dynamic(() => import("./location-map"), { ssr: false })

export type LocationFilterProps = {
  selectedLocations: LocationOption[]
  scope: LocationScope
  onScopeChange: (scope: LocationScope) => void
  onLocationsChange: (locations: LocationOption[]) => void
}

export function LocationFilter({
  selectedLocations,
  scope,
  onScopeChange,
  onLocationsChange,
}: LocationFilterProps) {
  const [search, setSearch] = useState("")

  const filteredOptions = useMemo(() => {
    if (!search) return TOP_LOCATIONS
    const needle = search.toLowerCase()
    return TOP_LOCATIONS.filter(
      (option) =>
        option.label.toLowerCase().includes(needle) ||
        option.city.toLowerCase().includes(needle) ||
        option.region.toLowerCase().includes(needle)
    )
  }, [search])

  const selectedIds = useMemo(() => new Set(selectedLocations.map((loc) => loc.id)), [selectedLocations])

  const handleToggleLocation = (option: LocationOption) => {
    if (selectedIds.has(option.id)) {
      onLocationsChange(selectedLocations.filter((loc) => loc.id !== option.id))
    } else {
      onLocationsChange([...selectedLocations, option])
    }
  }

  const handleQuickFilter = (filterId: string) => {
    const filter = REGION_FILTERS.find((item) => item.id === filterId)
    if (!filter) return

    if (filter.scope === "remote") {
      onScopeChange("remote")
      onLocationsChange([])
      return
    }

    onScopeChange(filter.scope)

    if (filter.locations) {
      const next = TOP_LOCATIONS.filter((loc) => filter.locations?.includes(loc.id))
      onLocationsChange(next)
    } else {
      onLocationsChange([])
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        {REGION_FILTERS.map((quick) => (
          <Button
            key={quick.id}
            size="sm"
            variant={scope === quick.scope ? "default" : "outline"}
            onClick={() => handleQuickFilter(quick.id)}
          >
            {quick.label}
          </Button>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-[2fr_3fr]">
        <div className="space-y-4">
          <Tabs value={scope} onValueChange={(value) => onScopeChange(value as LocationScope)}>
            <TabsList className="grid grid-cols-4">
              <TabsTrigger value="city">City</TabsTrigger>
              <TabsTrigger value="region">Province</TabsTrigger>
              <TabsTrigger value="country">Country</TabsTrigger>
              <TabsTrigger value="remote">Remote</TabsTrigger>
            </TabsList>
          </Tabs>

          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search locations"
          />

          <div className="h-48 overflow-y-auto rounded-md border border-border">
            <div className="grid gap-2 p-3">
              {filteredOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => handleToggleLocation(option)}
                  className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-sm transition ${
                    selectedIds.has(option.id)
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border hover:bg-muted"
                  }`}
                >
                  <span>
                    {option.label}
                    <span className="block text-xs text-muted-foreground">{option.region}</span>
                  </span>
                  {selectedIds.has(option.id) && <Badge variant="outline">Selected</Badge>}
                </button>
              ))}
            </div>
          </div>

          {selectedLocations.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedLocations.map((loc) => (
                <Badge key={loc.id} variant="secondary" className="gap-2">
                  {loc.label}
                  <button
                    onClick={() => handleToggleLocation(loc)}
                    className="text-xs text-destructive"
                    aria-label={`Remove ${loc.label}`}
                  >
                    ✕
                  </button>
                </Badge>
              ))}
              <Button size="sm" variant="outline" onClick={() => onLocationsChange([])}>
                Clear
              </Button>
            </div>
          )}
        </div>

        <div className="overflow-hidden rounded-xl border border-border">
          <LocationMap locations={filteredOptions} selectedIds={selectedIds} onSelect={handleToggleLocation} />
        </div>
      </div>
    </div>
  )
}
