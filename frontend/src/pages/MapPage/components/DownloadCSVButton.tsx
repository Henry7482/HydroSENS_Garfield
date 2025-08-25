import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
import React, { useState } from "react";
import axios from "axios";
import { useSelector } from "react-redux";
import { RootState } from "@/redux/store";
import { format } from "date-fns";

function DownloadCSVButton() {
    const [isLoading, setIsLoading] = useState(false);

    // Get data from Redux store
    const { regions, selectedRegionIndex } = useSelector(
        (state: RootState) => state.regionState
    );
    const { startDate, endDate } = useSelector(
        (state: RootState) => state.dateState
    );

    // Generate filename based on selected region and date range
    const generateFilename = (suffix: string) => {
        const selectedRegion =
            selectedRegionIndex !== null ? regions[selectedRegionIndex] : null;
        const regionName = selectedRegion?.name || "Export";

        // Format dates as DD-MM-YYYY
        const formattedStartDate = format(new Date(startDate), "dd-MM-yyyy");
        const formattedEndDate = format(new Date(endDate), "dd-MM-yyyy");

        // Clean region name (remove special characters that might cause issues in filenames)
        const cleanRegionName = regionName.replace(/[^a-zA-Z0-9]/g, "_");

        return `${cleanRegionName}_${formattedStartDate}_${formattedEndDate}_${suffix}.csv`;
    };

    // Function to parse CSV and separate into two files
    const parseAndSeparateCSV = (csvData: string) => {
        const lines = csvData.trim().split("\n");
        const headers = lines[0].split(",");

        // Define which columns go to which file
        const weatherColumns = ["temperature", "precipitation"];
        const otherColumns = headers.filter(
            (col) => !weatherColumns.includes(col)
        );

        // Create weather CSV (temperature and precipitation only)
        const weatherHeaders = ["date", ...weatherColumns];
        const weatherRows = lines.slice(1).map((line) => {
            const values = line.split(",");
            const date = values[0];
            const temp = values[headers.indexOf("temperature")];
            const precip = values[headers.indexOf("precipitation")];
            return `${date},${temp},${precip}`;
        });
        const weatherCSV = [weatherHeaders.join(","), ...weatherRows].join(
            "\n"
        );

        // Create other data CSV (remaining columns)
        const otherRows = lines.slice(1).map((line) => {
            const values = line.split(",");
            return otherColumns
                .map((col) => values[headers.indexOf(col)])
                .join(",");
        });
        const otherCSV = [otherColumns.join(","), ...otherRows].join("\n");

        return { weatherCSV, otherCSV };
    };

    // Function to download a CSV file
    const downloadCSV = (csvContent: string, filename: string) => {
        const blob = new Blob([csvContent], {
            type: "text/csv;charset=utf-8;",
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    };

    const handleDownload = async () => {
        const formatLocal = (d: Date) => {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, "0");
            const day = String(d.getDate()).padStart(2, "0");
            return `${year}-${month}-${day}`;
        };

        try {
            setIsLoading(true);

            const response = await axios.post(
                "http://localhost:5050/analyze/export-csv",
                {
                    region_name: regions[selectedRegionIndex || 0].name,
                    start_date: formatLocal(new Date(startDate)),
                    end_date: formatLocal(new Date(endDate)),
                },
                {
                    responseType: "text", // Changed to text to parse CSV
                    headers: {
                        Accept: "text/csv",
                    },
                }
            );

            // Parse the CSV data and separate into two files
            const { weatherCSV, otherCSV } = parseAndSeparateCSV(response.data);

            // Download the remaining columns file first (as requested)
            const otherFilename = generateFilename("main_data");
            downloadCSV(otherCSV, otherFilename);

            // Then download the weather data file
            const weatherFilename = generateFilename("weather_data");
            downloadCSV(weatherCSV, weatherFilename);
        } catch (error) {
            console.error("Error downloading CSV:", error);
            // You might want to show a toast notification or error message here
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Button
            variant="outline"
            className="flex-1 h-12 gap-2"
            onClick={handleDownload}
            disabled={isLoading}
        >
            {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
                <Download className="w-4 h-4" />
            )}
            {isLoading ? "Downloading..." : "Download Data"}
        </Button>
    );
}

export default DownloadCSVButton;
