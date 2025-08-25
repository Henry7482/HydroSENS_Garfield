import { api } from "./client";

export interface CacheCheckRequest {
    regionNames: string[];
}

export interface CacheCheckResponse {
    hasCache: Record<string, boolean>;
}

export async function checkRegionCache(
    regionNames: string[]
): Promise<CacheCheckResponse> {
    const { data } = await api.post<CacheCheckResponse>("/cache", {
        regionNames,
    });
    return data;
}

export async function deleteAllCache(): Promise<void> {
    await api.delete("/cache");
}

export async function deleteRegionCache(regionName: string): Promise<void> {
    await api.delete(`/cache/${encodeURIComponent(regionName)}`);
} 