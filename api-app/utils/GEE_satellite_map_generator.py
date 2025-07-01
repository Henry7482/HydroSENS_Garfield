import ee
import geemap
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Polygon
import warnings
import os
import tempfile
from PIL import Image

warnings.filterwarnings('ignore')

# Initialize Earth Engine (you already have this)
service_account = 'khoabui@hydrosens-garfield.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, r"./.secret/hydrosens-garfield-f6fe24f0d188.json")
ee.Initialize(credentials)

def coordinates_to_ee_geometry(coordinates):
    """
    Convert coordinate array to Earth Engine Geometry
    """
    # Ensure the polygon is closed (first and last coordinates are the same)
    if coordinates[0] != coordinates[-1]:
        coordinates = coordinates + [coordinates[0]]
    
    return ee.Geometry.Polygon([coordinates])

def get_satellite_image_from_gee(coordinates, output_path, image_size=1024, max_cloud_cover=20, zoom_out_factor=3):
    """
    Get high-quality satellite imagery from Google Earth Engine with zoomed out view
    
    Parameters:
    -----------
    coordinates : list
        List of [longitude, latitude] coordinate pairs
    output_path : str
        Path where to save the satellite image
    image_size : int
        Output image size in pixels (1024 = high quality)
    max_cloud_cover : int
        Maximum cloud coverage percentage
    zoom_out_factor : float
        How much to zoom out (higher = more zoomed out, default=3)
        
    Returns:
    --------
    bool : True if successful, False otherwise
    """
    try:
        print("  Getting zoomed out satellite imagery from Google Earth Engine...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to EE geometry
        aoi = coordinates_to_ee_geometry(coordinates)
        
        # Calculate region dimensions for scale
        coords = np.array(coordinates)
        lon_range = coords[:, 0].max() - coords[:, 0].min()
        lat_range = coords[:, 1].max() - coords[:, 1].min()
        max_range = max(lon_range, lat_range)
        
        # Force larger scale for more zoomed out view
        # Convert degrees to approximate meters and apply zoom out factor
        region_size_meters = max_range * 111000  # Rough conversion to meters
        scale = max(30, region_size_meters / (image_size / zoom_out_factor))
        
        # Ensure minimum scale based on zoom out factor
        min_scale_by_zoom = {
            1: 10,   # Normal zoom
            2: 20,   # 2x zoomed out
            3: 30,   # 3x zoomed out  
            4: 50,   # 4x zoomed out
            5: 100   # 5x zoomed out
        }
        
        min_scale = min_scale_by_zoom.get(int(zoom_out_factor), 30)
        scale = max(scale, min_scale)
        
        print(f"    Using zoomed out scale: {scale}m per pixel (zoom factor: {zoom_out_factor}x)")
        
        # Try multiple satellite data sources in order of preference
        satellite_sources = [
            {
                'name': 'Sentinel-2 (10m resolution)',
                'collection': 'COPERNICUS/S2_SR_HARMONIZED',
                'bands': ['B4', 'B3', 'B2'],  # RGB
                'scale': max(scale, 10),
                'date_range': ('2020-01-01', '2024-12-31')
            },
            {
                'name': 'Landsat 8-9 (30m resolution)', 
                'collection': 'LANDSAT/LC09/C02/T1_L2',
                'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # RGB
                'scale': max(scale, 30),
                'date_range': ('2020-01-01', '2024-12-31')
            },
            {
                'name': 'Landsat 8 (30m resolution)',
                'collection': 'LANDSAT/LC08/C02/T1_L2', 
                'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # RGB
                'scale': max(scale, 30),
                'date_range': ('2015-01-01', '2024-12-31')
            }
        ]
        
        for source in satellite_sources:
            try:
                print(f"    Trying {source['name']}...")
                
                # Get image collection
                if 'COPERNICUS' in source['collection']:
                    # Sentinel-2
                    collection = ee.ImageCollection(source['collection']) \
                        .filterBounds(aoi) \
                        .filterDate(source['date_range'][0], source['date_range'][1]) \
                        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover)) \
                        .sort('CLOUDY_PIXEL_PERCENTAGE')
                else:
                    # Landsat
                    collection = ee.ImageCollection(source['collection']) \
                        .filterBounds(aoi) \
                        .filterDate(source['date_range'][0], source['date_range'][1]) \
                        .filter(ee.Filter.lte('CLOUD_COVER', max_cloud_cover)) \
                        .sort('CLOUD_COVER')
                
                # Check if any images are available
                count = collection.size().getInfo()
                if count == 0:
                    print(f"      No images available for {source['name']}")
                    continue
                
                print(f"      Found {count} images, using the clearest one")
                
                # Get the best (least cloudy) image
                image = collection.first().select(source['bands'])
                
                # Scale pixel values for visualization (Landsat needs scaling)
                if 'LANDSAT' in source['collection']:
                    # Scale Landsat surface reflectance values
                    image = image.multiply(0.0000275).add(-0.2) \
                        .multiply(10000).uint16()  # Convert to 0-10000 range
                
                # Create visualization parameters for RGB
                vis_params = {
                    'bands': source['bands'],
                    'min': 0,
                    'max': 3000 if 'COPERNICUS' in source['collection'] else 2000,
                    'gamma': 1.2
                }
                
                # Get the image URL for download
                url = image.getThumbURL({
                    'region': aoi,
                    'dimensions': image_size,
                    'format': 'png',
                    **vis_params
                })
                
                # Download the image
                import requests
                response = requests.get(url)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"    Successfully downloaded satellite image from {source['name']}")
                    return True
                else:
                    print(f"      Failed to download from {source['name']}: HTTP {response.status_code}")
                    continue
                
            except Exception as e:
                print(f"      Error with {source['name']}: {str(e)[:100]}...")
                continue
        
        print("    All GEE satellite sources failed")
        return False
        
    except Exception as e:
        print(f"    GEE satellite image generation failed: {e}")
        return False

def generate_region_satellite_map_gee(coordinates, output_path="assets/images/region_screenshot.png", 
                                     figsize=(12, 10), alpha=0.6, 
                                     edge_color='none', face_color='none',
                                     line_width=3, use_gee_first=True,
                                     add_padding=True, padding_factor=0.2,
                                     zoom_out_factor=3):
    """
    Generate satellite map using Google Earth Engine first, with contextily fallback
    
    Parameters:
    -----------
    coordinates : list or array
        List of [longitude, latitude] coordinate pairs
    output_path : str
        Path where to save the generated map image
    figsize : tuple
        Figure size (width, height) in inches
    alpha : float
        Transparency of the region overlay (0-1)
    edge_color : str
        Color of the region border
    face_color : str
        Fill color of the region
    line_width : int
        Width of the region border
    use_gee_first : bool
        Whether to try Google Earth Engine first
    add_padding : bool
        Whether to add padding around small regions
    padding_factor : float
        How much padding to add (0.2 = 20% of region size)
    zoom_out_factor : float
        How much to zoom out for more context (higher = more zoomed out)
    
    Returns:
    --------
    bool : True if successful, False otherwise
    """
    
    try:
        print(f"Generating zoomed out satellite map for region...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to numpy array
        coords = np.array(coordinates)
        
        # Add padding for very small regions if requested
        if add_padding:
            original_coords = coords.copy()
            coords = add_region_padding(coords, padding_factor)
            print(f"  Added {padding_factor*100}% padding to region")
        
        success = False
        
        # Method 1: Try Google Earth Engine first with zoom out factor
        if use_gee_first:
            print(f"Method 1: Trying Google Earth Engine (zoom out factor: {zoom_out_factor}x)...")
            success = get_satellite_image_from_gee(
                coordinates=coords.tolist(),
                output_path=output_path,
                image_size=1024,
                zoom_out_factor=zoom_out_factor
            )
        
        # Method 2: Fallback to contextily if GEE fails
        if not success:
            print("Method 2: Falling back to contextily providers...")
            success = generate_contextily_satellite_map(
                coordinates=coords,
                output_path=output_path,
                figsize=figsize,
                alpha=alpha,
                edge_color=edge_color,
                face_color=face_color,
                line_width=line_width
            )
        
        if success:
            print(f"  Region satellite map saved to: {output_path}")
        else:
            print(f"  All satellite sources failed")
            
        return success
        
    except Exception as e:
        print(f"  Error generating satellite map: {e}")
        return False

def generate_contextily_satellite_map(coordinates, output_path, figsize=(12, 10), 
                                     alpha=0.6, edge_color='none', face_color='none',
                                     line_width=3):
    """
    Generate satellite map using contextily (your existing method)
    """
    try:
        # Ensure polygon is closed
        coords = np.array(coordinates)
        if not np.array_equal(coords[0], coords[-1]):
            coords = np.vstack([coords, coords[0]])
        
        # Create a polygon from coordinates
        polygon = Polygon(coords)
        
        # Create GeoDataFrame with WGS84 coordinates
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        
        # Reproject to Web Mercator (EPSG:3857) for contextily compatibility
        gdf_mercator = gdf.to_crs(epsg=3857)
        
        # Calculate adaptive zoom
        zoom = calculate_adaptive_zoom(coordinates)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Define satellite imagery providers
        providers_to_try = [
            ("ESRI World Imagery", ctx.providers.Esri.WorldImagery),
            ("CartoDB Voyager", ctx.providers.CartoDB.Voyager),
            ("OpenStreetMap", ctx.providers.OpenStreetMap.Mapnik)
        ]
        
        # Try each provider
        for i, (provider_name, tile_provider) in enumerate(providers_to_try):
            try:
                print(f"    Trying {provider_name}...")
                
                # Plot the polygon if not 'none'
                if face_color != 'none' or edge_color != 'none':
                    gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
                                    edgecolor=edge_color, linewidth=line_width)
                
                # Add satellite basemap
                ctx.add_basemap(ax, crs=gdf_mercator.crs, source=tile_provider, 
                              zoom=zoom, attribution_size=0)
                
                print(f"    Success with {provider_name}")
                break
                
            except Exception as e:
                print(f"    {provider_name} failed: {str(e)[:50]}...")
                ax.clear()
                continue
        
        # Customize the plot
        ax.set_axis_off()
        plt.tight_layout()
        
        # Save the map
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='none', edgecolor='none')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"    Contextily generation failed: {e}")
        return False

def calculate_adaptive_zoom(coordinates, min_zoom=10, max_zoom=18):
    """
    Calculate appropriate zoom level based on region size
    """
    try:
        coords = np.array(coordinates)
        
        # Calculate bounding box dimensions
        lon_min, lon_max = coords[:, 0].min(), coords[:, 0].max()
        lat_min, lat_max = coords[:, 1].min(), coords[:, 1].max()
        
        # Calculate width and height in degrees
        width_deg = lon_max - lon_min
        height_deg = lat_max - lat_min
        
        # Calculate approximate dimensions in meters
        avg_lat = (lat_min + lat_max) / 2
        width_meters = width_deg * 111320 * np.cos(np.radians(avg_lat))
        height_meters = height_deg * 110540
        
        # Use the larger dimension for zoom calculation
        max_dimension = max(width_meters, height_meters)
        
        # Adaptive zoom based on region size
        if max_dimension < 200:
            zoom = max_zoom
        elif max_dimension < 500:
            zoom = 17
        elif max_dimension < 1000:
            zoom = 16
        elif max_dimension < 2000:
            zoom = 15
        elif max_dimension < 5000:
            zoom = 14
        else:
            zoom = min_zoom
        
        # Ensure zoom is within bounds
        zoom = max(min_zoom, min(max_zoom, zoom))
        
        return zoom
        
    except Exception as e:
        return 15  # Safe default

def add_region_padding(coordinates, padding_factor=0.2):
    """
    Add padding around small regions
    """
    try:
        coords = np.array(coordinates)
        
        # Calculate current bounds
        lon_min, lon_max = coords[:, 0].min(), coords[:, 0].max()
        lat_min, lat_max = coords[:, 1].min(), coords[:, 1].max()
        
        # Calculate current dimensions
        width = lon_max - lon_min
        height = lat_max - lat_min
        
        # Add padding
        lon_padding = width * padding_factor
        lat_padding = height * padding_factor
        
        # Create new bounds with padding
        new_lon_min = lon_min - lon_padding
        new_lon_max = lon_max + lon_padding
        new_lat_min = lat_min - lat_padding
        new_lat_max = lat_max + lat_padding
        
        # Return padded rectangle coordinates
        padded_coords = np.array([
            [new_lon_min, new_lat_min],  # Southwest
            [new_lon_min, new_lat_max],  # Northwest
            [new_lon_max, new_lat_max],  # Northeast
            [new_lon_max, new_lat_min],  # Southeast
        ])
        
        return padded_coords
        
    except Exception as e:
        print(f"Error adding padding: {e}")
        return coordinates

def extract_coordinates_from_metrics(metrics_data):
    """
    Extract coordinates from your metrics_data object
    """
    try:
        # Your existing coordinate extraction logic
        if hasattr(metrics_data, 'coordinates'):
            return metrics_data.coordinates
        
        if hasattr(metrics_data, 'region') and hasattr(metrics_data.region, 'coordinates'):
            return metrics_data.region.coordinates
        
        if isinstance(metrics_data, dict):
            if 'coordinates' in metrics_data:
                return metrics_data['coordinates']
            elif 'region' in metrics_data and 'coordinates' in metrics_data['region']:
                return metrics_data['region']['coordinates']
        
        # Default coordinates
        print("  No coordinates found in metrics_data, using default region")
        return [
            [-74.0059, 40.7128],
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
            [-74.0059, 40.7128]
        ]
        
    except Exception as e:
        print(f"  Error extracting coordinates: {e}")
        return [
            [-74.0059, 40.7128],
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
            [-74.0059, 40.7128]
        ]
