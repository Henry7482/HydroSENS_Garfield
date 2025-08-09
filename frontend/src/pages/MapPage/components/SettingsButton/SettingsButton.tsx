"use client";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { toggleSettingsModal } from "@/redux/settingsActions";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { TooltipProvider } from "@/components/ui/tooltip";
import { RootState } from "@/redux/store";
import { ViewMode } from "@/types/viewMode";

function SettingsButton() {
    const { selectedRegionIndex } = useSelector(
        (state: RootState) => state.regionState
    );
    const dispatch = useDispatch();

    const handleClick = () => {
        dispatch(toggleSettingsModal(true));
    };

    return (
        <div
            className="absolute top-4 z-[100]"
            style={{
                right:
                    selectedRegionIndex === null ? "16px" : "calc(50% + 16px)",
            }}
        >
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button
                            size="icon"
                            onClick={handleClick}
                            className="h-10 w-10 bg-primary shadow-md hover:shadow-lg"
                        >
                            <Settings className="h-4 w-4" color="white" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Open Settings</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    );
}

export default SettingsButton;
