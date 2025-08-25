import { MAX_REGION_AREA_KMSQ } from "@/constants";
import { useMemo } from "react";

export const useRegionSizeLimit = (currentArea: number) => {
    const shouldShowAreaLimit = useMemo(() => {
        return Math.floor(currentArea) > 0;
    }, [currentArea]);

    const areaSizePercent = useMemo(() => {
        const percent = (currentArea / MAX_REGION_AREA_KMSQ) * 100;
        return `${Math.min(100, percent)}%`;
    }, [currentArea]);

    const areaSizeText = useMemo(() => {
        const flooredArea = Math.floor(currentArea);
        const text = `${flooredArea}/${MAX_REGION_AREA_KMSQ} km²`;
        return text;
    }, [currentArea]);

    const isOverAreaSizeLimit = useMemo(() => {
        return currentArea > MAX_REGION_AREA_KMSQ;
    }, [currentArea]);

    return {
        shouldShowAreaLimit,
        areaSizePercent,
        areaSizeText,
        isOverAreaSizeLimit,
    };
};
