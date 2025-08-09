import React from "react";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { deleteRegion } from "@/redux/regionActions";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/redux/store";
import { deleteRegionCache } from "@/api/cache";

interface DeleteRegionButtonProps {
    index: number;
}
function DeleteRegionButton({ index }: DeleteRegionButtonProps) {
    const dispatch = useDispatch();
    const { regions } = useSelector((state: RootState) => state.regionState);

    const handleDeleteRegionClick = async (index: number) => {
        try {
            // Get the region name before deleting the region
            const regionToDelete = regions[index];
            if (regionToDelete) {
                // Delete the cache for this region
                await deleteRegionCache(regionToDelete.name);
                console.log(
                    `Successfully deleted cache for region: ${regionToDelete.name}`
                );
            }
        } catch (error) {
            console.error("Failed to delete region cache:", error);
            // Continue with region deletion even if cache deletion fails
        }

        // Delete the region from Redux state
        dispatch(deleteRegion(index));
    };

    return (
        <AlertDialog>
            <AlertDialogTrigger className="text-gray-500 hover:text-red-500 ml-2 text-2xl">
                &times;
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Delete this region?</AlertDialogTitle>
                    <AlertDialogDescription>
                        Are you sure you want to delete this region?
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogAction
                        className="bg-red-500"
                        onClick={() => handleDeleteRegionClick(index)}
                    >
                        Delete
                    </AlertDialogAction>
                    <AlertDialogCancel className="bg-primary text-white">
                        Cancel
                    </AlertDialogCancel>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}

export default DeleteRegionButton;
