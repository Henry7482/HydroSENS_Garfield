export function regionToGeoJSON(coords: number[][]) {
  // Leaflet:  [lat, lng]
  // GeoJSON:  [lng, lat]
  const ring = coords.map(([lat, lng]) => [lng, lat]);

  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "Polygon", coordinates: [ring] },
        properties: {},
      },
    ],
  };
}