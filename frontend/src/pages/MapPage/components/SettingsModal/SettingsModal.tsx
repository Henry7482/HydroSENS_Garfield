"use client";

import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/redux/store";
import {
    setSelectedMetrics,
    setEndmemberType,
    toggleSettingsModal,
    AVAILABLE_METRICS,
    ENDMEMBER_TYPES,
    type MetricKey,
    type EndmemberType,
} from "@/redux/settingsActions";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { X, Info, Trash2, Loader2 } from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
    TooltipProvider,
} from "@/components/ui/tooltip";

import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import {
    checkRegionCache,
    deleteAllCache,
    deleteRegionCache,
} from "@/api/cache";

function SettingsModal() {
    const dispatch = useDispatch();
    const { selectedMetrics, endmemberType, isSettingsModalOpen } = useSelector(
        (state: RootState) => state.settings
    );
    const { regions } = useSelector((state: RootState) => state.regionState);

    // Local state for temporary changes before applying
    const [tempSelectedMetrics, setTempSelectedMetrics] =
        useState<MetricKey[]>(selectedMetrics);
    const [tempEndmemberType, setTempEndmemberType] =
        useState<EndmemberType>(endmemberType);

    // Cache management state
    const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
    const [regionToDelete, setRegionToDelete] = useState<string | null>(null);
    const [cacheStatus, setCacheStatus] = useState<Record<string, boolean>>({});
    const [isLoadingCache, setIsLoadingCache] = useState(false);
    const [isDeletingAll, setIsDeletingAll] = useState(false);
    const [isDeletingRegion, setIsDeletingRegion] = useState<string | null>(
        null
    );

    // Update local state when modal opens
    useEffect(() => {
        if (isSettingsModalOpen) {
            setTempSelectedMetrics(selectedMetrics);
            setTempEndmemberType(endmemberType);
        }
    }, [isSettingsModalOpen, selectedMetrics, endmemberType]);

    // Load cache status when modal opens
    useEffect(() => {
        if (isSettingsModalOpen && regions.length > 0) {
            loadCacheStatus();
        }
    }, [isSettingsModalOpen, regions]);

    const loadCacheStatus = async () => {
        if (regions.length === 0) return;

        setIsLoadingCache(true);
        try {
            const regionNames = regions.map((region) => region.name);
            const response = await checkRegionCache(regionNames);
            setCacheStatus(response.hasCache);
        } catch (error) {
            console.error("Failed to load cache status:", error);
            // Set all regions as having no cache on error
            const noCacheStatus: Record<string, boolean> = {};
            regions.forEach((region) => {
                noCacheStatus[region.name] = false;
            });
            setCacheStatus(noCacheStatus);
        } finally {
            setIsLoadingCache(false);
        }
    };

    const handleClose = () => {
        dispatch(toggleSettingsModal(false));
    };

    const handleCancel = () => {
        // Reset temporary state to current saved state
        setTempSelectedMetrics(selectedMetrics);
        setTempEndmemberType(endmemberType);
        handleClose();
    };

    const handleApply = () => {
        // Apply temporary changes to Redux state
        dispatch(setSelectedMetrics(tempSelectedMetrics));
        dispatch(setEndmemberType(tempEndmemberType));

        // Console log the selected metrics
        console.log("Applied Settings:");
        console.log("Selected Metrics:", tempSelectedMetrics);
        console.log("Endmember Type:", tempEndmemberType);

        handleClose();
    };

    const handleMetricToggle = (metricKey: MetricKey, checked: boolean) => {
        if (checked) {
            setTempSelectedMetrics([...tempSelectedMetrics, metricKey]);
        } else {
            setTempSelectedMetrics(
                tempSelectedMetrics.filter((key) => key !== metricKey)
            );
        }
    };

    const handleEndmemberChange = (value: EndmemberType) => {
        setTempEndmemberType(value);
    };

    // Cache management handlers
    const handleDeleteAllCache = async () => {
        setIsDeletingAll(true);
        try {
            await deleteAllCache();
            console.log("Successfully deleted all cache");
            // Refresh cache status
            await loadCacheStatus();
        } catch (error) {
            console.error("Failed to delete all cache:", error);
        } finally {
            setIsDeletingAll(false);
            setShowDeleteAllConfirm(false);
        }
    };

    const handleDeleteRegionCache = async (regionName: string) => {
        setIsDeletingRegion(regionName);
        try {
            await deleteRegionCache(regionName);
            console.log(`Successfully deleted cache for region: ${regionName}`);
            // Update cache status for this region
            setCacheStatus((prev) => ({
                ...prev,
                [regionName]: false,
            }));
        } catch (error) {
            console.error(
                `Failed to delete cache for region ${regionName}:`,
                error
            );
        } finally {
            setIsDeletingRegion(null);
            setRegionToDelete(null);
        }
    };

    if (!isSettingsModalOpen) return null;

    return (
        <TooltipProvider>
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1000]">
                <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] flex flex-col relative z-[1001]">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b">
                        <h2 className="text-xl font-semibold">Settings</h2>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleClose}
                            className="h-8 w-8 p-0"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>

                    {/* Content */}
                    <div className="p-6 space-y-6 overflow-y-auto flex-1 min-h-0">
                        {/* Output Statistics Section */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <h3 className="text-lg font-medium">
                                    Output Statistics
                                </h3>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-4 w-4 text-gray-400" />
                                    </TooltipTrigger>
                                    <TooltipContent className="z-[9999]">
                                        <p>
                                            Select which metrics to include in
                                            the analysis
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>

                            <div className="space-y-3">
                                {AVAILABLE_METRICS.map((metric) => (
                                    <div
                                        key={metric.key}
                                        className="flex items-center space-x-3"
                                    >
                                        <Checkbox
                                            id={metric.key}
                                            checked={tempSelectedMetrics.includes(
                                                metric.key
                                            )}
                                            onCheckedChange={(checked) =>
                                                handleMetricToggle(
                                                    metric.key,
                                                    checked as boolean
                                                )
                                            }
                                        />
                                        <label
                                            htmlFor={metric.key}
                                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                                        >
                                            {metric.label}
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Optimized For Section */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <h3 className="text-lg font-medium">
                                    Optimized For
                                </h3>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-4 w-4 text-gray-400" />
                                    </TooltipTrigger>
                                    <TooltipContent className="z-[9999]">
                                        <p>
                                            Choose the endmember type for
                                            analysis optimization
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>

                            {/* Custom Select Implementation */}
                            <div className="relative">
                                <select
                                    value={tempEndmemberType}
                                    onChange={(e) =>
                                        handleEndmemberChange(
                                            e.target.value as EndmemberType
                                        )
                                    }
                                    className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring appearance-none"
                                >
                                    {ENDMEMBER_TYPES.map((type) => (
                                        <option
                                            key={type.value}
                                            value={type.value}
                                        >
                                            {type.label}
                                        </option>
                                    ))}
                                </select>
                                <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                                    <svg
                                        className="h-4 w-4 opacity-50"
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 20 20"
                                        fill="currentColor"
                                        aria-hidden="true"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Cache Management Section */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <h3 className="text-lg font-medium">
                                    Cache Management
                                </h3>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <Info className="h-4 w-4 text-gray-400" />
                                    </TooltipTrigger>
                                    <TooltipContent className="z-[9999]">
                                        <p>
                                            Manage cached data for areas and
                                            analysis results
                                        </p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>

                            {/* Delete All Cache Button */}
                            <Button
                                variant="outline"
                                onClick={() => setShowDeleteAllConfirm(true)}
                                disabled={isDeletingAll}
                                className="w-full flex items-center gap-2 text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                            >
                                {isDeletingAll ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Trash2 className="h-4 w-4" />
                                )}
                                {isDeletingAll
                                    ? "Deleting..."
                                    : "Delete All Cache"}
                            </Button>

                            {/* Regions Cache List */}
                            <Accordion
                                type="single"
                                collapsible
                                className="w-full"
                            >
                                <AccordionItem
                                    value="regions-cache"
                                    className="border rounded-md"
                                >
                                    <AccordionTrigger className="px-4 py-3 text-sm font-medium">
                                        Area Cache (
                                        {isLoadingCache
                                            ? "..."
                                            : Object.values(cacheStatus).filter(
                                                  Boolean
                                              ).length}{" "}
                                        areas)
                                    </AccordionTrigger>
                                    <AccordionContent className="px-4 pb-3">
                                        <div className="space-y-2">
                                            {isLoadingCache ? (
                                                <div className="flex items-center justify-center py-4">
                                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                                    <span className="text-sm text-gray-500">
                                                        Loading cache status...
                                                    </span>
                                                </div>
                                            ) : regions.length === 0 ? (
                                                <p className="text-sm text-gray-500 italic">
                                                    No areas found
                                                </p>
                                            ) : (
                                                regions
                                                    .filter(
                                                        (region) =>
                                                            cacheStatus[
                                                                region.name
                                                            ]
                                                    )
                                                    .map((region) => (
                                                        <div
                                                            key={region.name}
                                                            className="flex items-center justify-between p-2 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors"
                                                        >
                                                            <span className="text-sm font-medium">
                                                                {region.name}
                                                            </span>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() =>
                                                                    setRegionToDelete(
                                                                        region.name
                                                                    )
                                                                }
                                                                disabled={
                                                                    isDeletingRegion ===
                                                                    region.name
                                                                }
                                                                className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                                                            >
                                                                {isDeletingRegion ===
                                                                region.name ? (
                                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                                ) : (
                                                                    <Trash2 className="h-4 w-4" />
                                                                )}
                                                            </Button>
                                                        </div>
                                                    ))
                                            )}
                                        </div>
                                    </AccordionContent>
                                </AccordionItem>
                            </Accordion>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex gap-3 p-6 border-t bg-gray-50">
                        <Button
                            variant="outline"
                            onClick={handleCancel}
                            className="flex-1"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleApply}
                            className="flex-1"
                            disabled={tempSelectedMetrics.length === 0}
                        >
                            Apply
                        </Button>
                    </div>
                </div>

                {/* Delete All Cache Confirmation Modal */}
                {showDeleteAllConfirm && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1002]">
                        <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
                            <div className="space-y-2">
                                <h3 className="text-lg font-semibold">
                                    Delete All Cache
                                </h3>
                                <p className="text-sm text-gray-600">
                                    This will permanently delete all cached data
                                    for all areas. This might slow down the
                                    analysis.
                                </p>
                            </div>
                            <div className="flex gap-3 justify-end">
                                <Button
                                    variant="outline"
                                    onClick={() =>
                                        setShowDeleteAllConfirm(false)
                                    }
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleDeleteAllCache}
                                    disabled={isDeletingAll}
                                    className="bg-red-600 hover:bg-red-700 text-white"
                                >
                                    {isDeletingAll ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                            Deleting...
                                        </>
                                    ) : (
                                        "Delete All"
                                    )}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Delete Region Cache Confirmation Modal */}
                {regionToDelete && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1002]">
                        <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
                            <div className="space-y-2">
                                <h3 className="text-lg font-semibold">
                                    Delete Area Cache
                                </h3>
                                <p className="text-sm text-gray-600">
                                    This will permanently delete all cached data
                                    for the area "{regionToDelete}". This might
                                    slow down the analysis.
                                </p>
                            </div>
                            <div className="flex gap-3 justify-end">
                                <Button
                                    variant="outline"
                                    onClick={() => setRegionToDelete(null)}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={() =>
                                        regionToDelete &&
                                        handleDeleteRegionCache(regionToDelete)
                                    }
                                    disabled={
                                        isDeletingRegion === regionToDelete
                                    }
                                    className="bg-red-600 hover:bg-red-700 text-white"
                                >
                                    {isDeletingRegion === regionToDelete ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                            Deleting...
                                        </>
                                    ) : (
                                        "Delete"
                                    )}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </TooltipProvider>
    );
}

export default SettingsModal;
