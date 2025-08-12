### Import required libraries ###
from .GEE_Functions_update import *
from .Functions_update import *
import matplotlib.pyplot
import glob
from spectral_libraries.core import amuses
from datetime import timedelta, datetime
import sys
#from Report import *
import shutil
import time

# Start the timer
start_time = time.time()

def run_hydrosens(main_folder, region_name, dates_to_process, output_master, amc, p, coordinates, crs='EPSG:4326', endmember=3):
    """
    Run the Hydrosens workflow for specific dates and coordinate-based area of interest.
    
    Parameters:
        main_folder: Main working folder
        region_name: Name of the region for folder organization
        dates_to_process: List of datetime objects for specific dates to process
        output_master: Output directory
        amc: Antecedent Moisture Condition
        p: Precipitation value
        coordinates: List of [lon, lat] pairs defining the polygon boundary
        crs: Coordinate reference system (default: 'EPSG:4326')
        endmember: Number of endmembers for MESMA (2 or 3, default: 3)
                  3 = vegetation, impervious, soil
                  2 = vegetation, soil (no impervious)
    """    
    # Convert coordinates to Earth Engine geometry
    aoi = coordinates_to_ee_geometry(coordinates)
    
    print(f"Processing coordinate-based AOI with {len(coordinates)} vertices for region: {region_name}")
    print(f"Processing {len(dates_to_process)} specific dates")
    return process_specific_dates(dates_to_process, aoi, output_master, region_name, amc, p, coordinates, crs, endmember)


def process_specific_dates(dates_to_process, aoi, output_master, region_name, amc, p, coordinates, crs, endmember=3):
    """Process Sentinel-2 images for specific dates if imagery exists."""

    all_weather_data = get_daily_weather(dates_to_process, aoi)

    HSG250m = os.getenv("HSG250m")
    sli = os.getenv("SLI")
    dates_with_images = []
    vegetation_values = []
    impervious_values = []
    soil_values = []
    curve_number = []
    ndvi_values = []
    avg_temp = []
    avg_p = []

    for date in dates_to_process:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
            
        print(f"Processing for date: {date.strftime('%Y-%m-%d')} in region: {region_name}")
        # extract S-2 data
        StartDate = date
        EndDate = StartDate + timedelta(days=1, seconds=-1)

        filtered_col, num_images = load_Sentinel2(aoi, StartDate, EndDate)

        if num_images == 0:
            print(f"No images found for {StartDate.strftime('%Y-%m-%d')}. Skipping to next date.")
            continue

        dates_with_images.append(date)
        
        output = create_output_folder(output_master, region_name, date)
        print("Output: ", output)

        print(f"Image found for {date}, creating output folder.")

        print(f"Processing image from {date}")

        # Use the provided CRS instead of reading from shapefile
        crs_string = crs
        resample_img = resampling(filtered_col, crs_string)
        DEM = getDEM(aoi)
        Bandsexport(resample_img, crs_string, output, aoi)
        DEMexport(DEM, crs_string, output, aoi)

        weather_day = all_weather_data.get(date.strftime('%Y-%m-%d'))
        if weather_day:
            temperature = weather_day['temperature']
            precipitation = weather_day['precipitation']
            avg_temp.append(temperature)
            avg_p.append(precipitation)
        else:
            # Handle cases where weather data might be missing for a day
            print("[temp] NO TEMP DATA FOUND")
            avg_temp.append(0)
            avg_p.append(0)

        bands = gdal.Open(output + r"/Bands.tif")
        band_array = bands.ReadAsArray()
        arr2 = bands.GetRasterBand(1).ReadAsArray().astype('float64') 
        arr3 = bands.GetRasterBand(2).ReadAsArray().astype('float64')
        arr4 = bands.GetRasterBand(3).ReadAsArray().astype('float64')
        arr8A = bands.GetRasterBand(6).ReadAsArray().astype('float64')
        arr11 = bands.GetRasterBand(7).ReadAsArray().astype('float64')

        # True Color Image 
        np.seterr(invalid='ignore') 
        writeTCI(arr4, arr3, arr2, bands, "TCI", output) 

        # NDVI
        np.seterr(invalid='ignore')
        NDVI = (np.divide((arr8A - arr4), (arr8A + arr4), out=np.zeros_like(arr8A), where=(arr8A + arr4) != 0))
        ndvi_values.append(np.nanmean(NDVI))
        CreateFloat(NDVI, bands, "NDVI", output)

        # MNDWI
        np.seterr(invalid='ignore')
        MNDWI = (np.divide((arr3 - arr11), (arr3 + arr11), out=np.zeros_like(arr3), where=(arr3 + arr11) != 0))

        ### Water Mask ###
        # Default MNDWI threshold is 0

        reclassified_MNDWI = np.where(MNDWI > 0, 1, 0)
        CreateFloat(reclassified_MNDWI, bands, "null_MNDWI", output)
        del MNDWI

        # Sieve sparse, unconnected pixels in MNDWI to maintain contiguous water bodies
        null = gdal.Open(output + r"/null_MNDWI.tif", 1)
        Band = null.GetRasterBand(1)
        gdal.SieveFilter(srcBand=Band, maskBand=None, dstBand=Band, threshold=16, connectedness=8)
        del null, Band

        # Mask out water
        mask = gdal.Open(output + r"/null_MNDWI.tif")
        mask_array = mask.ReadAsArray()

        # Mask and save all bands of band_array
        driver = gdal.GetDriverByName('GTiff')
        output_raster_path = output + r"/bands_masked.tif"
        if os.path.exists(output_raster_path):
            os.remove(output_raster_path)
        output_raster = driver.Create(output + r"/bands_masked.tif", bands.RasterXSize, bands.RasterYSize,
                                      band_array.shape[0],
                                      gdal.GDT_Float64)
        output_raster.SetProjection(bands.GetProjection())
        output_raster.SetGeoTransform(bands.GetGeoTransform())

        for band_index in range(band_array.shape[0]):
            masked_band = np.where(mask_array == 0, band_array[band_index], 0)
            output_raster.GetRasterBand(band_index + 1).WriteArray(masked_band)

        output_raster.FlushCache()
        output_raster = None

        ### MESMA ###

        # Prepare image and spectral library for MESMA
        input_img = r"/Bands.tif"
        image = gdal.Open(output + input_img)
        image_array = image.ReadAsArray()
        image_array[np.isnan(image_array)] = -9999
        image_array[np.isinf(image_array)] = -9999
        image_array[image_array == 0] = -9999
        img = prepare_S2image(output + r"/bands_masked.tif")
        class_list_init_, initial_lib = prepare_sli(sli, num_bands=8)

        # Always run AMUSES on the full original library
        A = amuses.Amuses()
        em_spectra_dict = A.execute(image_array, initial_lib, 0.9, 0.95, 15, (0.0002, 0.02))
        em_spectra_list = list(em_spectra_dict.values())
        indices_array = em_spectra_dict['amuses_indices']

        # Get the trimmed library from the original spectral library using AMUSES indices
        class_list_init, em_spectra_trim = trimmed_library(sli, num_bands=8, row_numbers=indices_array)

        output_file = output + r"/trimmed_library.csv"
        wavelengths = [490, 560, 665, 783, 842, 865, 1610, 2190]

        # Create dataframe with all AMUSES-selected endmembers
        data = {
            "MaterialClass": class_list_init,
            **{str(wavelengths[i]): em_spectra_trim[i] for i in range(len(wavelengths))}
        }
        df = pd.DataFrame(data)

        # Filter based on endmember parameter AFTER getting AMUSES results
        if endmember == 2:
            # For 2 endmembers, we need to work around MESMA library limitations
            # Keep vegetation and soil, but also include minimal impervious to avoid indexing errors
            material_order = ['vegetation', 'soil']
            df_filtered = df[df['MaterialClass'].isin(material_order)].copy()
            
            # If we don't have enough endmembers, we need to create a dummy impervious entry
            # to prevent MESMA from failing with indexing errors
            if len(df_filtered) > 0:
                # Add one minimal impervious endmember to satisfy MESMA's internal requirements
                impervious_rows = df[df['MaterialClass'] == 'impervious']
                if len(impervious_rows) > 0:
                    # Take just one impervious endmember to complete the set
                    dummy_impervious = impervious_rows.iloc[:1].copy()
                    df_filtered = pd.concat([df_filtered, dummy_impervious])
                    material_order = ['vegetation', 'impervious', 'soil']  # Standard order for MESMA
                    print(f"Using 2 endmembers: vegetation and soil (with dummy impervious for MESMA compatibility)")
                else:
                    print("Warning: No impervious endmembers available for MESMA compatibility")
                    material_order = ['vegetation', 'soil']
            
            print(f"Original AMUSES selection had {len(df)} endmembers, filtered to {len(df_filtered)}")
        else:
            # Use all 3 endmembers
            material_order = ['vegetation', 'impervious', 'soil']
            df_filtered = df[df['MaterialClass'].isin(material_order)].copy()
            print("Using 3 endmembers: vegetation, impervious, and soil")

        # Ensure we have endmembers for the analysis
        if len(df_filtered) == 0:
            print("Warning: No endmembers of desired types found after filtering. Using original AMUSES selection.")
            df_filtered = df.copy()
            material_order = list(df['MaterialClass'].unique())

        # For balanced selection, limit the number per class
        unique_classes = df_filtered['MaterialClass'].unique()
        if len(unique_classes) >= 2:
            # Balance the selection but ensure we have all required classes
            max_per_class = max(3, min(10, len(df_filtered) // len(unique_classes)))
            balanced_df = []
            for cls in unique_classes:
                cls_rows = df_filtered[df_filtered['MaterialClass'] == cls].head(max_per_class)
                balanced_df.append(cls_rows)
            df_filtered = pd.concat(balanced_df).copy()
            
            class_counts = df_filtered['MaterialClass'].value_counts().to_dict()
            print(f"Balanced selection: {class_counts}")

        print(f"Final endmember selection: {list(df_filtered['MaterialClass'].unique())}")

        # Sort by material class
        df_filtered['MaterialClass'] = pd.Categorical(df_filtered['MaterialClass'], categories=material_order, ordered=True)
        df_filtered = df_filtered.sort_values('MaterialClass')
        df_filtered = df_filtered.reset_index(drop=True)

        output_csv = output + r"/trimmed_library.csv"
        print("output_csv", output_csv)
        df_filtered.to_csv(output_csv, index=False)

        class_list, trim_lib = prepare_sli(output + r"/trimmed_library.csv", num_bands=8)

        # Run MESMA algorithm using trimmed spectral library
        out_fractions = doMESMA(class_list, img, trim_lib)
        final = np.flip(out_fractions, axis=1)
        final = np.rot90(final, k=3, axes=(1, 2))
        
        # Handle different endmember configurations
        if endmember == 2:
            # For 2 endmembers: We included a dummy impervious for MESMA compatibility
            # Now we need to extract only vegetation and soil, and set impervious to zero
            unique_classes = list(df_filtered['MaterialClass'].unique())
            print(f"MESMA output shape: {final.shape}, Classes: {unique_classes}")
            
            # Find indices for vegetation and soil in the final output
            class_indices = {cls: i for i, cls in enumerate(sorted(unique_classes))}
            
            if 'vegetation' in class_indices and 'soil' in class_indices:
                vegetation = final[class_indices['vegetation']]
                soil = final[class_indices['soil']]
                print(f"Extracted vegetation (index {class_indices['vegetation']}) and soil (index {class_indices['soil']})")
            else:
                # Fallback: assume first two bands are what we want
                vegetation = final[0] if len(final) > 0 else np.zeros_like(mask_array)
                soil = final[1] if len(final) > 1 else np.zeros_like(mask_array)
                print("Fallback: using first two MESMA output bands")
            
            # Set impervious to zero array for 2-endmember case
            impervious = np.zeros_like(soil)
            print("2-endmember MESMA: vegetation and soil fractions calculated, impervious set to zero")
        else:
            # For 3 endmembers: Standard processing
            unique_classes = list(df_filtered['MaterialClass'].unique())
            print(f"MESMA output shape: {final.shape}, Classes: {unique_classes}")
            
            if len(unique_classes) >= 3:
                # Standard 3-endmember case - order depends on alphabetical sorting
                class_indices = {cls: i for i, cls in enumerate(sorted(unique_classes))}
                vegetation = final[class_indices.get('vegetation', 0)]
                impervious = final[class_indices.get('impervious', 1)]
                soil = final[class_indices.get('soil', 2)]
                print(f"Extracted vegetation (index {class_indices.get('vegetation', 0)}), "
                      f"impervious (index {class_indices.get('impervious', 1)}), "
                      f"soil (index {class_indices.get('soil', 2)})")
            else:
                # Fallback for cases with fewer than 3 endmembers
                vegetation = final[0] if len(final) > 0 else np.zeros_like(mask_array)
                impervious = final[1] if len(final) > 1 else np.zeros_like(mask_array)
                soil = final[2] if len(final) > 2 else np.zeros_like(mask_array)
                print("Fallback: using first three MESMA output bands")
            print("3-endmember MESMA: vegetation, impervious, and soil fractions calculated")
        
        vegetation_values.append(np.nanmean(vegetation))
        impervious_values.append(np.nanmean(impervious))
        soil_values.append(np.nanmean(soil))

        del img
        os.remove(output + r"/trimmed_library.csv")
        CreateFloat(soil, image, "soil", output)
        CreateFloat(impervious, image, "impervious", output)
        CreateFloat(vegetation, image, "vegetation", output)

        ### Global Soil Dataset Processing ###

        # Create buffered coordinates for soil dataset extraction
        try:
            buffered_coords, buffered_crs = Create_buffer(coordinates, crs)
            print(f"Created buffer with {len(buffered_coords)} coordinates")
        except Exception as e:
            print(f"Error creating buffer: {e}")
            raise

        # Matching global dataset projection to buffered coordinates for extraction
        try:
            HSG250m_open = gdal.Open(HSG250m)
            if HSG250m_open is None:
                raise ValueError(f"Could not open HSG dataset: {HSG250m}")
            soil_crs = HSG250m_open.GetProjection()
            print(f"HSG dataset CRS: {soil_crs}")
        except Exception as e:
            print(f"Error accessing HSG dataset: {e}")
            raise

        # Extract study area from global dataset using buffered coordinates
        try:
            print(f"Extracting from HSG dataset using buffered coordinates...")
            Extract(HSG250m, buffered_coords, buffered_crs, output + r"/extracted.tif", nodata_value=255)
            print("HSG extraction completed successfully")
        except Exception as e:
            print(f"Error in HSG extraction: {e}")
            # Try with original coordinates if buffered extraction fails
            try:
                print("Retrying with original coordinates...")
                Extract(HSG250m, coordinates, crs, output + r"/extracted.tif", nodata_value=255)
                print("HSG extraction with original coordinates completed")
            except Exception as e2:
                print(f"Error in HSG extraction retry: {e2}")
                raise

        # Reproject extracted raster to match MNDWI
        MNDWI = gdal.Open(output + r"/null_MNDWI.tif")
        print(output + r"/null_MNDWI.tif")
        setcrs = MNDWI.GetProjection()
        
        print("MNDWI CRS", setcrs)
        inputfile = output + r"/extracted.tif"
        output_raster = output + r"/HSG_match.tif"

        # Extract the resolution information from the MNDWI raster
        MNDWI_geotransform = MNDWI.GetGeoTransform()
        MNDWI_res = (MNDWI_geotransform[1], MNDWI_geotransform[5])
        warp = gdal.Warp(output_raster, inputfile, dstSRS=setcrs, xRes=MNDWI_res[0],
                         yRes=MNDWI_res[1], outputType=gdal.GDT_Int16)

        del inputfile, output_raster, MNDWI, warp

        # Fill NoData holes in the extracted data
        reference = gdal.Open(output + r"/HSG_match.tif")
        data = matplotlib.pyplot.imread(output + r"/HSG_match.tif")
        filled = Fill(data)
        CreateInt(filled, reference, "filled", output)
        matplotlib.pyplot.close()
        reference = None
        del data, filled, reference

        # Reclassify to HSG value
        soilraster = gdal.Open(output + r"/filled.tif")
        reclass = soilraster.ReadAsArray()

        reclass[np.where((1 <= reclass) & (reclass <= 3))] = 4
        reclass[np.where((3 <= reclass) & (reclass <= 8))] = 3
        reclass[reclass == 10] = 3
        reclass[reclass == 11] = 2
        reclass[reclass == 9] = 2
        reclass[reclass == 12] = 1

        CreateInt(reclass, soilraster, "HSG_reclass", output)
        del soilraster

        extract_raster(output + r"/HSG_reclass.tif", output + r"/null_MNDWI.tif", output + r"/HSG_final.tif")

        ### Initial CN classification for vegetation and soil ###

        # Reclassify NDVI
        NDVI = gdal.Open(output + r"/NDVI.tif")
        newNDVI = NDVI.ReadAsArray()
        newNDVI[newNDVI >= 0.62] = 10
        newNDVI[np.where((0.55 <= newNDVI) & (newNDVI < 0.62))] = 20
        newNDVI[(0.31 < newNDVI) & (newNDVI < 0.55)] = 30
        newNDVI[newNDVI <= 0.31] = 40

        # Reclassify Vegetation Fraction
        new_veg = vegetation.copy()
        new_veg[new_veg >= 0.75] = 3
        new_veg[(0.5 < new_veg) & (new_veg < 0.75)] = 2
        new_veg[new_veg <= 0.5] = 1

        # Combine
        array1 = new_veg + newNDVI
        array1[array1 == 42] = 41
        array1[array1 == 43] = 41
        array1[np.isnan(array1)] = 0
        array1[np.isinf(array1)] = 0

        CreateInt(array1, NDVI, "veghealth", output)
        
        # Extract using coordinates instead of shapefile
        try:
            Extract(output + r"/veghealth.tif", coordinates, crs, output + r"/Vegetation_Health.tif", nodata_value=255)
            print("Vegetation health extraction completed")
        except Exception as e:
            print(f"Error in vegetation health extraction: {e}")
            raise

        # Get files
        file2 = gdal.Open(output + r"/HSG_final.tif")
        array2 = file2.ReadAsArray()
        CN_table = r"./data/CN_lookup.csv"

        # Vegetation CN Reclassification
        veg_reclass = classification(CN_table, array1, array2)

        # Soil CN Reclassification
        array3 = array1 * 0
        soil_reclass = classification(CN_table, array3, array2)

        file2 = None

        # CCN calculation - adjust based on endmember parameter
        imp_CN = 98
        if endmember == 2:
            # For 2 endmembers: only use soil and vegetation (impervious is zero)
            CCNarr = (soil_reclass * soil) + (veg_reclass * vegetation)
            print("CCN calculation using 2 endmembers (soil and vegetation only)")
        else:
            # For 3 endmembers: use soil, vegetation, and impervious
            CCNarr = (soil_reclass * soil) + (veg_reclass * vegetation) + (imp_CN * impervious)
            print("CCN calculation using 3 endmembers (soil, vegetation, and impervious)")

        ### Slope Correction ###

        # Create slope map isolating pixels >5%
        DEMfile = gdal.Open(output + r"/DEM.tif")
        DEM = DEMfile.ReadAsArray()
        cellsize = 10

        px, py = np.gradient(DEM, cellsize)
        slope_init = np.sqrt(px ** 2 + py ** 2)
        slope = np.degrees(np.arctan(slope_init))

        slope[slope < 5] = 0
        slope[slope == 90] = 0

        # Sharpley-Williams Method for slope correction

        AMC_III = AMCIII(CCNarr)
        CN_slope_SW = (1 / 3) * (AMC_III - CCNarr) * (1 - ((2 * 2.718281) ** (-13.86 * slope))) + CCNarr

        ### Conversion to different AMC if required ###

        while amc > 0:
            choice = amc
            if choice == 1:
                CCN_arr = AMCI(CN_slope_SW)
            elif choice == 3:
                CCN_arr = AMCIII(CN_slope_SW)
            else:
                CCN_arr = CN_slope_SW
            break

        # One last extraction to clean up edges of CCN map
        CCN_arr_final = np.where(mask_array == 0, CCN_arr, 0)

        CCN_arr_final[np.isnan(CCN_arr_final)] = 100
        CCN_arr_final[np.isinf(CCN_arr_final)] = 100
        CCN_arr_final[CCN_arr_final > 100] = 100
        CCN_arr_final[CCN_arr_final == 0] = 100
        curve_number.append(np.nanmean(CCN_arr_final))
        CreateInt(CCN_arr_final, DEMfile, "CCN_masked", output)
        
        # Extract using coordinates instead of shapefile
        try:
            Extract(output + r"/CCN_masked.tif", coordinates, crs, output + f"/CCN_final.tif", nodata_value=255)
            print("CCN final extraction completed")
        except Exception as e:
            print(f"Error in CCN final extraction: {e}")
            raise

        del mask, DEMfile

        ### Runoff Calculation ###

        """US Department of Agriculture (USDA) Natural Resources Conservation Service (NRCS) 
        CN method for determining the Runoff Coefficient
                Storage = 254 * (1-CN/100)
                Initial Abstraction = 0.2*S
                Runoff  = (P-Ia)^2/(P-Ia+S)
        """

        # Storage
        CCN = gdal.Open(output + r"/CCN_final.tif")
        CCN_array = CCN.ReadAsArray()

        storage = 254 * (1 - (CCN_array / 100.0))

        # Initial Abstraction
        Ia = 0.2 * storage

        # Runoff Coefficient
        # precipitation in mm

        runoff_c = (p - Ia) ** 2 / (p - Ia + storage)
        runoff_c[runoff_c < 0] = np.nan

        CreateFloat(runoff_c, CCN, "Runoff", output)

        # Clean up output folder - keep only essential files
        cleanup_output_folder(output)

        # Post-processing: Clip all important TIF files to polygon shape
        # This ensures that instead of having bounding box rasters, we get precise polygon-clipped rasters
        # that match the exact area of interest defined by the coordinates
        clipping_results = clip_tif_files_to_polygon(output, coordinates, crs)
        
        # Store clipping results for potential debugging or reporting
        if clipping_results['failure_count'] > 0:
            print(f"Warning: {clipping_results['failure_count']} files failed to clip properly")

    # Create results dictionary for only the dates that were successfully processed
    formatted_data = {}
    
    for i in range(len(dates_with_images)):
        date = dates_with_images[i].strftime('%Y-%m-%d')
        formatted_data[date] = {
            "ndvi": nan_to_zero(ndvi_values[i]),
            "soil-fraction": nan_to_zero(soil_values[i]),
            "vegetation-fraction": nan_to_zero(vegetation_values[i]),
            "precipitation": nan_to_zero(avg_p[i]),
            "temperature": nan_to_zero(avg_temp[i]),
            "curve-number": nan_to_zero(curve_number[i])
        }

    print(f"Successfully processed {len(dates_with_images)} out of {len(dates_to_process)} requested dates")
    return formatted_data


def create_output_folder(base_output, region_name, date):
    """Create a subfolder for the specific region and date."""
    # Convert date to string format YYYY-MM-DD
    date_str = date.strftime('%Y-%m-%d')
    # Create folder path: base_output/region_name/date
    folder_path = os.path.join(base_output, region_name, date_str)
    # Check if folder exists, if not, create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


def cleanup_output_folder(output_folder):
    """
    Clean up output folder to keep only essential files based on LAYER_RANGES.
    
    Essential files to keep:
    - vegetation.tif
    - impervious.tif
    - CCN_final.tif
    - Runoff.tif
    - NDVI.tif
    - Vegetation_Health.tif
    - soil.tif
    """
    import os
    import glob
    
    # Define essential files to keep (based on LAYER_RANGES keys)
    essential_files = {
        'vegetation.tif',
        'impervious.tif', 
        'CCN_final.tif',
        'Runoff.tif',
        'NDVI.tif',
        'Vegetation_Health.tif',
        'soil.tif',
        'TCI.tif'
    }
    
    # Get all files in the output folder
    all_files = glob.glob(os.path.join(output_folder, '*'))
    
    # Remove non-essential files
    for file_path in all_files:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            if filename not in essential_files:
                try:
                    os.remove(file_path)
                    print(f"Removed unnecessary file: {filename}")
                except Exception as e:
                    print(f"Warning: Could not remove {filename}: {e}")
    
    print(f"Output folder cleanup completed. Kept {len(essential_files)} essential files.")


# Updated convenience function for the coordinate-based approach
def run_hydrosens_with_coordinates(region_name, coordinates, dates_to_process, output_dir=None, amc=2, precipitation=10.0, crs='EPSG:4326', endmember=3):
    """
    Convenience function to run Hydrosens analysis with coordinate array
    
    Parameters:
        region_name: Name of the region for folder organization
        coordinates: List of [lon, lat] pairs defining the polygon boundary
                    Example: [[-120.5, 35.2], [-120.3, 35.2], [-120.3, 35.4], [-120.5, 35.4]]
        dates_to_process: List of datetime objects for specific dates to process (preferred)
        start_date: Start date as string 'YYYY-MM-DD' (fallback for backward compatibility)
        end_date: End date as string 'YYYY-MM-DD' (fallback for backward compatibility)
        output_dir: Output directory path
        amc: Antecedent Moisture Condition (1, 2, or 3)
        precipitation: Precipitation value in mm
        crs: Coordinate reference system (default: 'EPSG:4326')
        endmember: Number of endmembers for MESMA (2 or 3, default: 3)
                  3 = vegetation, impervious, soil
                  2 = vegetation, soil (no impervious)
    
    Returns:
        Dictionary with analysis results
    """
    
    # Validate coordinates
    if not coordinates or len(coordinates) < 3:
        raise ValueError("Need at least 3 coordinate pairs to define a polygon")
    
    # Validate each coordinate pair
    for i, coord in enumerate(coordinates):
        if len(coord) != 2:
            raise ValueError(f"Coordinate {i} must have exactly 2 values [lon, lat]")
        if not (-180 <= coord[0] <= 180):
            raise ValueError(f"Longitude {coord[0]} at position {i} is out of valid range [-180, 180]")
        if not (-90 <= coord[1] <= 90):
            raise ValueError(f"Latitude {coord[1]} at position {i} is out of valid range [-90, 90]")
    
    process_dates = dates_to_process
    print(f"Processing {len(process_dates)} specific dates")
    
    # Validate endmember parameter - default to 3 if not 2
    if endmember != 2:
        endmember = 3
    
    print(f"Running Hydrosens analysis for region '{region_name}' with polygon of {len(coordinates)} vertices")
    print(f"Processing {len(process_dates)} dates")
    print(f"AMC: {amc}, Precipitation: {precipitation}mm")
    
    return run_hydrosens(
        main_folder=".",  # Current directory as main folder
        region_name=region_name,
        dates_to_process=process_dates,
        output_master=output_dir,
        amc=amc,
        p=precipitation,
        coordinates=coordinates,
        crs=crs,
        endmember=endmember
    )