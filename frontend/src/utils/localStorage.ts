import initialRegions from "@/data/initialRegions";
import { Region } from "@/types/region";

const REGIONS_STORAGE_KEY = "saved_regions";
const STORAGE_VERSION = "1.0"; // For future migrations if needed

interface StoredRegionsData {
    version: string;
    regions: Region[];
    lastUpdated: string;
}

/**
 * Save regions to localStorage
 */
export const saveRegionsToStorage = (regions: Region[]): void => {
    try {
        const dataToStore: StoredRegionsData = {
            version: STORAGE_VERSION,
            regions,
            lastUpdated: new Date().toISOString(),
        };

        localStorage.setItem(REGIONS_STORAGE_KEY, JSON.stringify(dataToStore));
        console.log(`Saved ${regions.length} regions to localStorage`);
    } catch (error) {
        console.error("Failed to save regions to localStorage:", error);
        // Could show user notification here
    }
};

/**
 * Load regions from localStorage
 */
export const loadRegionsFromStorage = (): Region[] => {
    try {
        const storedData = localStorage.getItem(REGIONS_STORAGE_KEY);

        if (!storedData) {
            console.log("No saved regions found in localStorage.");
            return [];
        }

        const parsedData: StoredRegionsData = JSON.parse(storedData);

        // Validate the data structure
        if (!parsedData.regions || !Array.isArray(parsedData.regions)) {
            console.warn("Invalid regions data in localStorage");
            return [];
        }

        // Validate each region object
        const validRegions = parsedData.regions.filter(
            (region) =>
                region &&
                typeof region.name === "string" &&
                typeof region.area === "number" &&
                typeof region.color === "string" &&
                Array.isArray(region.coordinates) &&
                region.coordinates.length > 0
        );

        if (validRegions.length !== parsedData.regions.length) {
            console.warn(
                `Filtered out ${
                    parsedData.regions.length - validRegions.length
                } invalid regions`
            );
        }

        console.log(`Loaded ${validRegions.length} regions from localStorage`);
        return validRegions;
    } catch (error) {
        console.error("Failed to load regions from localStorage:", error);
        return [];
    }
};

/**
 * Clear all saved regions from localStorage
 */
export const clearRegionsFromStorage = (): void => {
    try {
        localStorage.removeItem(REGIONS_STORAGE_KEY);
        console.log("Cleared all regions from localStorage");
    } catch (error) {
        console.error("Failed to clear regions from localStorage:", error);
    }
};

/**
 * Get storage info (for debugging/UI purposes)
 */
export const getStorageInfo = (): {
    hasData: boolean;
    count: number;
    lastUpdated: string | null;
} => {
    try {
        const storedData = localStorage.getItem(REGIONS_STORAGE_KEY);

        if (!storedData) {
            return { hasData: false, count: 0, lastUpdated: null };
        }

        const parsedData: StoredRegionsData = JSON.parse(storedData);

        return {
            hasData: true,
            count: parsedData.regions?.length || 0,
            lastUpdated: parsedData.lastUpdated || null,
        };
    } catch (error) {
        console.error("Failed to get storage info:", error);
        return { hasData: false, count: 0, lastUpdated: null };
    }
};
