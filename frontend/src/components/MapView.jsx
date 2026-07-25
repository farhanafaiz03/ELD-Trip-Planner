import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useEffect } from 'react';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Leaflet's default marker icon relies on image files that bundlers
// like Vite don't resolve correctly out of the box - broken/missing
// marker icons are the single most common react-leaflet gotcha. We
// sidestep it entirely by drawing our own small colored dots instead
// of using Leaflet's default icon at all.
function createDotIcon(color) {
  return L.divIcon({
    className: 'map-dot-icon',
    html: `<span style="background:${color}"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

// Same color language the log sheets (Module 7) will use, pulled
// straight from index.css via var() - one place decides what each
// status looks like, everywhere in the app agrees with it.
const ICONS = {
  pickup: createDotIcon('var(--color-primary)'),
  dropoff: createDotIcon('var(--color-dropoff)'),
  on_duty_not_driving: createDotIcon('var(--status-on-duty)'),
  off_duty: createDotIcon('var(--status-off-duty)'),
};

/**
 * FitBoundsToRoute
 *
 * Leaflet doesn't automatically re-frame the view when new data shows
 * up after the map has already mounted - without this, every trip
 * would render at whatever arbitrary default center/zoom we started
 * with. This runs once real route geometry arrives and pans/zooms to
 * fit the whole trip on screen.
 */
function FitBoundsToRoute({ geometry }) {
  const map = useMap();

  useEffect(() => {
    if (geometry && geometry.length > 0) {
      map.fitBounds(geometry, { padding: [40, 40] });
    }
  }, [geometry, map]);

  return null;
}

/**
 * MapView
 *
 * Purely a renderer - it doesn't fetch anything or make decisions
 * about the trip. It just draws whatever route and stops the backend
 * already computed. All the actual logic lives in the HOS engine and
 * the view, not here.
 */
export default function MapView({ route, stops }) {
  if (!route) return null;

  return (
    <div className="map-view">
      <MapContainer center={route.geometry[0]} zoom={7} scrollWheelZoom={true}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Polyline positions={route.geometry} pathOptions={{ color: '#1e3a5f', weight: 4 }} />

        {stops.map((stop, index) => (
          <Marker
            key={index}
            position={[stop.lat, stop.lng]}
            icon={ICONS[stop.type] || ICONS.off_duty}
          >
            <Popup>{stop.label}</Popup>
          </Marker>
        ))}

        <FitBoundsToRoute geometry={route.geometry} />
      </MapContainer>

      <div className="map-legend">
        <LegendItem colorVar="--color-primary" label="Pickup" />
        <LegendItem colorVar="--color-dropoff" label="Dropoff" />
        <LegendItem colorVar="--status-on-duty" label="Fuel stop" />
        <LegendItem colorVar="--status-off-duty" label="Rest / break" />
        

      </div>

      <div className="map-summary">
        <span>{route.distance_miles} miles</span>
        <span>{route.duration_hours} hrs driving</span>
      </div>
    </div>
  );
}

function LegendItem({ colorVar, label }) {
  return (
    <span className="map-legend-item">
      <span className="map-legend-dot" style={{ background: `var(${colorVar})` }} />
      {label}
    </span>
  );
}