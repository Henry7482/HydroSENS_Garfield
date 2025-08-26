import React from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
// Using native JavaScript date formatting instead of date-fns
import { Calendar, TrendingUp } from "lucide-react";

interface DateRangeConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    startDate: number;
    endDate: number;
    regionName: string;
    isLoading?: boolean;
}

export function DateRangeConfirmationModal({
    isOpen,
    onClose,
    onConfirm,
    startDate,
    endDate,
    regionName,
    isLoading = false,
}: DateRangeConfirmationModalProps) {
    const formatDate = (timestamp: number) => {
        return new Date(timestamp).toLocaleDateString("en-US", {
            month: "short",
            day: "2-digit",
            year: "numeric",
        });
    };

    const calculateDays = () => {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffTime = Math.abs(end.getTime() - start.getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        return diffDays;
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-blue-600" />
                        Analyze Area
                    </DialogTitle>
                    <DialogDescription>
                        Confirm your analysis parameters for the selected area.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="bg-slate-50 rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-700">
                                Area:
                            </span>
                            <span className="text-sm text-slate-900 font-semibold">
                                {regionName}
                            </span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-700">
                                Date Range:
                            </span>
                            <div className="flex items-center gap-2 text-sm text-slate-900">
                                <Calendar className="h-4 w-4 text-slate-500" />
                                <span>
                                    {formatDate(startDate)} -{" "}
                                    {formatDate(endDate)}
                                </span>
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-700">
                                Duration:
                            </span>
                            <span className="text-sm text-slate-900">
                                {calculateDays()}{" "}
                                {calculateDays() === 1 ? "day" : "days"}
                            </span>
                        </div>
                    </div>
                </div>

                <DialogFooter className="flex gap-2 sm:gap-2">
                    <Button
                        variant="outline"
                        onClick={onClose}
                        disabled={isLoading}
                        className="flex-1"
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={onConfirm}
                        disabled={isLoading}
                        className="flex-1"
                    >
                        {isLoading ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                Analyzing...
                            </>
                        ) : (
                            "Start Analysis"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
