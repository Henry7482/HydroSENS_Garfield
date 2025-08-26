import { api } from "./client";

export interface LayerFile {
    name: string; // e.g., "vegetation.tif", "NVDI.tif"
    blob: Blob;
    url: string; // Object URL for the blob
}

export interface DateLayers {
    date: string; // e.g., "2025-05-12"
    layers: LayerFile[];
}

// Define allowed TIF file names (without .tif extension)
const ALLOWED_LAYER_NAMES = [
    "vegetation",
    "impervious",
    "CCN_final",
    "Runoff",
    "NDVI",
    "Vegetation_Health",
    "soil",
    "TCI",
];

export interface FetchLayerTifsPayload {
    region_name: string;
    start_date: string;
    end_date: string;
}

export async function fetchLayerTifs(
    payload: FetchLayerTifsPayload
): Promise<DateLayers[]> {
    try {
        console.log("Before sending: ", payload);

        const response = await api.post("/analyze/export-tifs", payload, {
            responseType: "blob",
            headers: {
                "Content-Type": "application/json",
            },
            data: payload,
        });

        // We'll need a library to extract ZIP files in the browser
        // For now, let's assume we have JSZip available
        const JSZip = (await import("jszip")).default;
        const zip = await JSZip.loadAsync(response.data);

        const dateLayers: DateLayers[] = [];
        const dateMap = new Map<string, LayerFile[]>();

        // Process each file in the ZIP
        for (const [path, file] of Object.entries(zip.files)) {
            if (file.dir) continue; // Skip directories

            // Extract date and filename from path (e.g., "2025-05-12/vegetation.tif")
            const pathParts = path.split("/");
            if (pathParts.length !== 2) continue;

            const [date, filename] = pathParts;
            if (!filename.endsWith(".tif")) continue;

            // Extract the base name without .tif extension
            const baseName = filename.replace(".tif", "");

            // Filter: only process files with allowed names
            if (!ALLOWED_LAYER_NAMES.includes(baseName)) {
                console.log(`Skipping filtered out layer: ${filename}`);
                continue;
            }

            // Get the file blob
            const blob = await file.async("blob");
            const url = URL.createObjectURL(blob);

            const layerFile: LayerFile = {
                name: filename,
                blob,
                url,
            };

            if (!dateMap.has(date)) {
                dateMap.set(date, []);
            }
            dateMap.get(date)!.push(layerFile);
        }

        // Convert map to array and sort by date
        for (const [date, layers] of dateMap.entries()) {
            dateLayers.push({ date, layers });
        }

        dateLayers.sort((a, b) => a.date.localeCompare(b.date));

        console.log(
            `Processed ${dateLayers.length} date groups with filtered layers`
        );

        return dateLayers;
    } catch (error) {
        console.error("Failed to fetch layer TIFs:", error);
        throw error;
    }
}
