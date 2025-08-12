import * as React from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { DateRange } from "react-day-picker";
import { Button } from "@/components/ui/button";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/redux/store";
import { setEndDate, setStartDate } from "@/redux/dateActions";
import Calendar from "./Calendar";
import { DateRangeConfirmationModal } from "./DateRangeConfirmationModal";

export function DateRangePicker() {
    const dispatch = useDispatch<AppDispatch>();

    // Track which date we're currently selecting (start or end)
    const [selectingStart, setSelectingStart] = React.useState(true);

    // Modal state
    const [showConfirmationModal, setShowConfirmationModal] =
        React.useState(false);
    const [pendingDateRange, setPendingDateRange] = React.useState<{
        startDate: number;
        endDate: number;
    } | null>(null);

    // Track the original date range before user started making changes
    const [originalDateRange, setOriginalDateRange] = React.useState<{
        startDate: number;
        endDate: number;
    } | null>(null);

    // Track temporary start date during selection (not in Redux yet)
    const [tempStartDate, setTempStartDate] = React.useState<number | null>(
        null
    );

    // Get dates from Redux state
    const { startDate, endDate } = useSelector(
        (state: RootState) => state.dateState
    );
    const { selectedRegionIndex, regions } = useSelector(
        (state: RootState) => state.regionState
    );
    const { loading } = useSelector((state: RootState) => state.dashboard);

    // Calculate the maximum allowed date (5 days before today)
    const maxAllowedDate = React.useMemo(() => {
        const today = new Date();
        const fiveDaysAgo = new Date(today);
        fiveDaysAgo.setDate(today.getDate() - 5);
        return fiveDaysAgo;
    }, []);

    // Convert Redux dates to DateRange format for the ShadCN component
    const dateRange: DateRange | undefined = React.useMemo(() => {
        // If we have a temporary start date, use it for display
        const displayStartDate = tempStartDate || startDate;

        if (!displayStartDate && !endDate) return undefined;

        return {
            from: displayStartDate ? new Date(displayStartDate) : undefined,
            to: endDate ? new Date(endDate) : undefined,
        };
    }, [startDate, endDate, tempStartDate]);

    // Check if we have a valid date range (both start and end dates)
    const hasValidDateRange = (start: number, end: number) => {
        return start && end && start !== end;
    };

    // Handle single date clicks for sequential selection
    const handleDateClick = (date: Date) => {
        const clickedTimestamp = date.getTime();

        if (selectingStart) {
            // First click - store original date range before making changes
            if (startDate && endDate) {
                setOriginalDateRange({
                    startDate: startDate,
                    endDate: endDate,
                });
            }

            // Set temporary start date (not in Redux yet) and prepare for end date selection
            setTempStartDate(clickedTimestamp);
            setSelectingStart(false);
        } else {
            // Second click - determine final date range
            const currentStartDate = new Date(tempStartDate || startDate!);
            let finalStartDate: number;
            let finalEndDate: number;

            if (clickedTimestamp >= currentStartDate.getTime()) {
                // If clicked date is after or equal to start date, it becomes end date
                finalStartDate = currentStartDate.getTime();
                finalEndDate = clickedTimestamp;
            } else {
                // If clicked date is before start date, it becomes new start date
                finalStartDate = clickedTimestamp;
                finalEndDate = currentStartDate.getTime();
            }

            // Check if we have a valid range (different dates) and region is selected
            if (
                hasValidDateRange(finalStartDate, finalEndDate) &&
                selectedRegionIndex !== null
            ) {
                // Show confirmation modal instead of directly updating Redux
                setPendingDateRange({
                    startDate: finalStartDate,
                    endDate: finalEndDate,
                });
                setShowConfirmationModal(true);
                // Don't update Redux state yet - wait for confirmation
            } else {
                // If same date or no region selected, just update Redux normally
                dispatch(setStartDate(finalStartDate));
                dispatch(setEndDate(finalEndDate));
                setSelectingStart(true);
                setTempStartDate(null); // Clear temporary start date
                // Clear original range since we're not showing modal
                setOriginalDateRange(null);
            }
        }
    };

    // Handle confirmation modal confirm
    const handleConfirmAnalysis = () => {
        if (pendingDateRange) {
            // Update Redux with the confirmed date range
            dispatch(setStartDate(pendingDateRange.startDate));
            dispatch(setEndDate(pendingDateRange.endDate));

            // Close modal and reset states
            setShowConfirmationModal(false);
            setPendingDateRange(null);
            setOriginalDateRange(null); // Clear original range since change was confirmed
            setTempStartDate(null); // Clear temporary start date

            // IMPORTANT: Reset selection state so user can select new ranges
            setSelectingStart(true);

            // Trigger the API call
            // Note: We'll trigger this after Redux state is updated via useEffect in RegionDashboard
        }
    };

    // Handle confirmation modal cancel - RESTORE ORIGINAL DATE RANGE
    const handleCancelAnalysis = () => {
        setShowConfirmationModal(false);
        setPendingDateRange(null);

        // Restore the original date range before any changes were made
        if (originalDateRange) {
            dispatch(setStartDate(originalDateRange.startDate));
            dispatch(setEndDate(originalDateRange.endDate));
            setOriginalDateRange(null);
        }

        // Clear temporary start date and reset the selection state to start over
        setTempStartDate(null);
        setSelectingStart(true);
    };

    // Get current region name for modal
    const currentRegionName = React.useMemo(() => {
        if (
            selectedRegionIndex !== null &&
            regions &&
            regions[selectedRegionIndex]
        ) {
            return regions[selectedRegionIndex].name;
        }
        return "Unknown Region";
    }, [selectedRegionIndex, regions]);

    // Handle range selection - we'll intercept and use our custom logic
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const handleRangeSelect = (range: DateRange | undefined) => {
        // We don't use the default range selection, instead we handle clicks manually
        // This function will be called but we'll ignore it in favor of our custom logic
    };

    return (
        <>
            <div className={"flex justify-center items-center w-full"}>
                <Popover>
                    <PopoverTrigger asChild>
                        <Button
                            id="date"
                            variant={"outline"}
                            className="font-normal py-6.5 rounded-3xl"
                        >
                            <div className="bg-primary p-2 rounded-sm mr-0.5">
                                <CalendarIcon
                                    className=" h-4 w-4"
                                    color="white"
                                />
                            </div>
                            {dateRange?.from ? (
                                dateRange.to &&
                                dateRange.from.getTime() !==
                                    dateRange.to.getTime() ? (
                                    <>
                                        {format(dateRange.from, "LLL dd, y")} -{" "}
                                        {format(dateRange.to, "LLL dd, y")}
                                    </>
                                ) : (
                                    format(dateRange.from, "LLL dd, y")
                                )
                            ) : (
                                <span>Pick a date</span>
                            )}
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                            autoFocus
                            mode="range"
                            defaultMonth={maxAllowedDate}
                            selected={dateRange}
                            onSelect={handleRangeSelect}
                            onDayClick={(date) => {
                                // Only handle clicks on enabled dates
                                if (date <= maxAllowedDate) {
                                    handleDateClick(date);
                                }
                            }}
                            numberOfMonths={2}
                            toDate={maxAllowedDate}
                            disabled={(date) => date > maxAllowedDate}
                        />
                        <div className="p-3 text-sm text-muted-foreground border-t">
                            {selectingStart
                                ? "Select start date"
                                : "Select end date"}
                        </div>
                    </PopoverContent>
                </Popover>
            </div>

            {/* Confirmation Modal */}
            {pendingDateRange && (
                <DateRangeConfirmationModal
                    isOpen={showConfirmationModal}
                    onClose={handleCancelAnalysis}
                    onConfirm={handleConfirmAnalysis}
                    startDate={pendingDateRange.startDate}
                    endDate={pendingDateRange.endDate}
                    regionName={currentRegionName}
                    isLoading={loading}
                />
            )}
        </>
    );
}

export default DateRangePicker;
