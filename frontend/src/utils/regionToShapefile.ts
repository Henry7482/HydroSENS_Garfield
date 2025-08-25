import * as shpwrite from "@mapbox/shp-write";
import proj4 from "proj4";
import {
  Feature,
  FeatureCollection,
  GeoJsonProperties,
  Polygon,
} from "geojson";

/**
 * Calculate the signed area of a polygon ring to determine orientation
 * Positive area = clockwise, Negative area = counter-clockwise
 */
function getSignedArea(ring: [number, number][]): number {
  let area = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[i + 1];
    area += (x2 - x1) * (y2 + y1);
  }
  return area / 2;
}

/**
 * Ensure ring has clockwise orientation (for exterior rings in shapefiles)
 */
function ensureClockwise(ring: [number, number][]): [number, number][] {
  const signedArea = getSignedArea(ring);
  // If area is negative, ring is counter-clockwise, so reverse it
  if (signedArea < 0) {
    return [...ring].reverse();
  }
  return ring;
}

/**
 * Given an array of [lat, lng] pairs describing a closed ring,
 * produce a zipped shapefile as a Blob.
 *
 * @param latLngCoords  An array of [latitude, longitude] pairs (must form a closed ring).
 * @returns Promise<Blob> - A zip file containing .shp, .shx, .dbf, .prj files
 */
export async function regionToShapefileZip(
  latLngCoords: [number, number][]
): Promise<Blob> {
  if (!Array.isArray(latLngCoords) || latLngCoords.length < 4) {
    throw new Error(
      "Coordinates must be an array of ≥4 [lat, lng] pairs (closed ring)."
    );
  }

  // 1) Reproject each [lat, lng] from EPSG:4326 → EPSG:32631 (x, y)
  console.log('🗺️ Starting coordinate conversion from EPSG:4326 to EPSG:32631');
  const ring: [number, number][] = latLngCoords.map(([lat, lng], index) => {
    const [x, y] = proj4("EPSG:4326", "EPSG:32631", [lng, lat]);
    console.log(`  Point ${index + 1}: [${lat}, ${lng}] → [${x.toFixed(2)}, ${y.toFixed(2)}]`);
    return [x, y];
  });
  console.log(`✅ Converted ${ring.length} coordinate pairs`);

  // 2) Ensure the ring is closed (first === last)
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    ring.push([first[0], first[1]]);
  }

  // 3) Ensure clockwise orientation for exterior ring
  const clockwiseRing = ensureClockwise(ring);

  // 4) Build a GeoJSON FeatureCollection
  const geoJSON: FeatureCollection<Polygon, GeoJsonProperties> = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "Polygon",
          coordinates: [clockwiseRing], // single exterior ring with correct orientation
        },
        properties: {
          name: "Region",
          id: 1,
        },
      },
    ],
  };

  // 5) Options to match Mapbox example, with EPSG:32631 WKT in .prj
  const utm31nWKT = `PROJCS["WGS 84 / UTM zone 31N",
  GEOGCS["WGS 84",
    DATUM["WGS_1984",
      SPHEROID["WGS 84",6378137,298.257223563,
        AUTHORITY["EPSG","7030"]],
      AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]],
  PROJECTION["Transverse_Mercator"],
  PARAMETER["latitude_of_origin",0],
  PARAMETER["central_meridian",3],
  PARAMETER["scale_factor",0.9996],
  PARAMETER["false_easting",500000],
  PARAMETER["false_northing",0],
  UNIT["metre",1,AUTHORITY["EPSG","9001"]],
  AUTHORITY["EPSG","32631"]]`;

  const options = {
    folder: "regions_folder",
    filename: "region_shapes",
    outputType: "blob",
    compression: "DEFLATE",
    types: { polygon: "region_polygons" },
    prj: utm31nWKT,
  };

  // 6) Use shpwrite.zip() with options → returns a Blob
  try {
    const zipBlob = await shpwrite.zip(geoJSON, options);
    return zipBlob;
  } catch (error) {
    throw new Error(`Failed to generate shapefile: ${error}`);
  }
}