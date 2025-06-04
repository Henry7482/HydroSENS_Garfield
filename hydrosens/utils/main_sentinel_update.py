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

def run_hydrosens(main_folder, start_date, end_date, output_master, amc, p, coordinates, crs='EPSG:4326'):
    """
    Run the Hydrosens workflow for a given date range and coordinate-based area of interest.
    
    Parameters:
        main_folder: Main working folder
        start_date: Start date for analysis
        end_date: End date for analysis  
        output_master: Output directory
        amc: Antecedent Moisture Condition
        p: Precipitation value
        coordinates: List of [lon, lat] pairs defining the polygon boundary
        crs: Coordinate reference system (default: 'EPSG:4326')
    """
    # Clear all contents of the output_master directory
    if os.path.exists(output_master):
        for filename in os.listdir(output_master):
            file_path = os.path.join(output_master, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # remove file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # remove directory
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    
    # Convert coordinates to Earth Engine geometry
    aoi = coordinates_to_ee_geometry(coordinates)
    
    print(f"Processing coordinate-based AOI with {len(coordinates)} vertices")
    return process_dates(start_date, end_date, aoi, output_master, amc, p, coordinates, crs)


def process_dates(start_date, end_date, aoi, output_master, amc, p, coordinates, crs):
    """Process Sentinel-2 images within a date range if imagery exists."""

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

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    date = start_date

    while date <= end_date:
        print(f"Processing for date: {date.strftime('%Y-%m-%d')}")
        # extract S-2 data
        StartDate = date
        EndDate = StartDate + timedelta(days=1, seconds=-1)

        filtered_col, num_images = load_Sentinel2(aoi, StartDate, EndDate)

        if num_images == 0:
            print(f"No images found for {StartDate.strftime('%Y-%m-%d')}. Skipping to next date.")
            date += timedelta(days=1)
            continue

        dates_with_images.append(date)
        
        output = create_output_folder(output_master, date)
        print("Output: ", output)

        print(f"Image found for {date}, creating output folder.")

        print(f"Processing image from {date}")

        # Use the provided CRS instead of reading from shapefile
        crs_string = crs
        resample_img = resampling(filtered_col, crs_string)
        DEM = getDEM(aoi)
        Bandsexport(resample_img, crs_string, output, aoi)
        DEMexport(DEM, crs_string, output, aoi)

        target = CDS_temp(date, output)
        df = extract_data(target)
        print("Using coordinate-based AOI")
        avg_temp = get_temp(coordinates, df)

        target = CDS_precip(date, output)
        df = extract_p_data(target)
        avg_p = get_p(coordinates, df)

        bands = gdal.Open(output + r"/Bands.tif")
        band_array = bands.ReadAsArray()
        arr3 = bands.GetRasterBand(2).ReadAsArray().astype('float64')
        arr4 = bands.GetRasterBand(3).ReadAsArray().astype('float64')
        arr8A = bands.GetRasterBand(6).ReadAsArray().astype('float64')
        arr11 = bands.GetRasterBand(7).ReadAsArray().astype('float64')

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
        A = amuses.Amuses()
        em_spectra_dict = A.execute(image_array, initial_lib, 0.9, 0.95, 15, (0.0002, 0.02))
        em_spectra_list = list(em_spectra_dict.values())
        indices_array = em_spectra_dict['amuses_indices']
        class_list_init, em_spectra_trim = trimmed_library(sli,
                                                           num_bands=8, row_numbers=indices_array)

        output_file = output + r"/trimmed_library.csv"
        wavelengths = [490, 560, 665, 783, 842, 865, 1610, 2190]

        data = {
            "MaterialClass": class_list_init,
            **{str(wavelengths[i]): em_spectra_trim[i] for i in range(len(wavelengths))}
        }
        df = pd.DataFrame(data)
        material_order = ['vegetation', 'impervious', 'soil']
        df['MaterialClass'] = pd.Categorical(df['MaterialClass'], categories=material_order, ordered=True)
        df = df.sort_values('MaterialClass')
        output_csv = output + r"/trimmed_library.csv"
        print("output_csv", output_csv)
        df.to_csv(output_csv, index=False)
        class_list, trim_lib = prepare_sli(output + r"/trimmed_library.csv", num_bands=8)

        # Run MESMA algorithm using trimmed spectral library
        out_fractions = doMESMA(class_list, img, trim_lib)
        final = np.flip(out_fractions, axis=1)
        final = np.rot90(final, k=3, axes=(1, 2))
        soil = final[0]
        impervious = final[1]
        vegetation = final[2]
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

        # CCN calculation
        imp_CN = 98
        CCNarr = (soil_reclass * soil) + (veg_reclass * vegetation) + (imp_CN * impervious)

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
        date += timedelta(days=1)

    data = {
        'date': [d.strftime('%Y-%m-%d') for d in dates_with_images],
        'veg_mean': vegetation_values,
        'soil_mean': soil_values,
        'curve_number': curve_number,
        'ndvi': ndvi_values,
        'temperature': avg_temp,
        'precipitation': avg_p
    }
    
    formatted_data = {}

    for i in range(len(data['date'])):
        date = data['date'][i]
        formatted_data[date] = {
            "ndvi": nan_to_zero(data['ndvi'][i]),
            "soil-fraction": nan_to_zero(data['soil_mean'][i]),
            "vegetation-fraction": nan_to_zero(data['veg_mean'][i]),
            "precipitation": nan_to_zero(data['precipitation']),
            "temperature": nan_to_zero(data['temperature']),
            "curve-number": nan_to_zero(data['curve_number'][i])
        }

    df = pd.DataFrame(data)
    df = df[
    (df[['veg_mean', 'soil_mean', 'curve_number', 'ndvi', 'temperature']] != 0).all(axis=1)
    ]
    
    # Create a filename based on coordinates (using first coordinate as identifier)
    coord_id = f"coords_{coordinates[0][0]:.3f}_{coordinates[0][1]:.3f}"
    print("Output master: ", output_master)
    output_csv = os.path.join(output_master, coord_id + '.csv')

    df.to_csv(output_csv, index=False)

    print(f"Data saved to {output_csv}")

    return formatted_data


def create_output_folder(base_output, date):
    """Create a subfolder for the specific date."""
    # Convert date to string format YYYY-MM-DD
    date_str = date.strftime('%Y-%m-%d')
    # Create folder path
    folder_path = os.path.join(base_output, date_str)
    # Check if folder exists, if not, create it
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


# Example usage function for the coordinate-based approach
def run_hydrosens_with_coordinates(coordinates, start_date, end_date, output_dir, amc=2, precipitation=10.0, crs='EPSG:4326'):
    """
    Convenience function to run Hydrosens analysis with coordinate array
    
    Parameters:
        coordinates: List of [lon, lat] pairs defining the polygon boundary
                    Example: [[-120.5, 35.2], [-120.3, 35.2], [-120.3, 35.4], [-120.5, 35.4]]
        start_date: Start date as string 'YYYY-MM-DD'
        end_date: End date as string 'YYYY-MM-DD' 
        output_dir: Output directory path
        amc: Antecedent Moisture Condition (1, 2, or 3)
        precipitation: Precipitation value in mm
        crs: Coordinate reference system (default: 'EPSG:4326')
    
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
    
    print(f"Running Hydrosens analysis for polygon with {len(coordinates)} vertices")
    print(f"Date range: {start_date} to {end_date}")
    print(f"AMC: {amc}, Precipitation: {precipitation}mm")
    
    return run_hydrosens(
        main_folder=".",  # Current directory as main folder
        start_date=start_date,
        end_date=end_date, 
        output_master=output_dir,
        amc=amc,
        p=precipitation,
        coordinates=coordinates,
        crs=crs
    )