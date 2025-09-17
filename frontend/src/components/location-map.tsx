"use client"

import { memo } from "react"
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet"
import L from "leaflet"

import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, LocationOption } from "@/data/locations"

const markerIcon = L.icon({
  iconUrl:
    "data:image/svg+xml;base64," +
    btoa(
      `<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%23ff4f67' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 22s8-4.5 8-11A8 8 0 0 0 4 11c0 6.5 8 11 8 11'/><circle cx='12' cy='11' r='3'/></svg>`
    ),
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -28],
})

export type LocationMapProps = {
  locations: LocationOption[]
  selectedIds: Set<string>
  onSelect: (location: LocationOption) => void
}

function LocationMap({ locations, selectedIds, onSelect }: LocationMapProps) {
  return (
    <MapContainer
      center={DEFAULT_MAP_CENTER}
      zoom={DEFAULT_MAP_ZOOM}
      scrollWheelZoom={false}
      className="h-72 w-full rounded-xl border border-border"
      attributionControl={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {locations.map((loc) => (
        <Marker
          key={loc.id}
          position={[loc.latitude, loc.longitude]}
          icon={markerIcon}
          eventHandlers={{
            click: () => onSelect(loc),
          }}
        >
          <Popup>
            <div className="space-y-2">
              <div className="font-semibold">{loc.label}</div>
              <button
                onClick={() => onSelect(loc)}
                className="rounded-md bg-primary px-3 py-1 text-xs font-medium text-primary-foreground"
              >
                {selectedIds.has(loc.id) ? "Selected" : "Select"}
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}

export default memo(LocationMap)
