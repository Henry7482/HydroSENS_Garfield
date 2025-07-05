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
from PIL import Image, ImageDraw

warnings.filterwarnings('ignore')

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

def get_satellite_image_from_gee(coordinates, output_path, image_size=2048, max_cloud_cover=20, zoom_out_factor=5):
    """
    Get high-quality satellite imagery from Google Earth Engine with proper zoom out for small regions
    """
    try:
        print("  Getting high-resolution satellite imagery from Google Earth Engine...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to EE geometry
        original_aoi = coordinates_to_ee_geometry(coordinates)
        
        # Calculate region dimensions for scale
        coords = np.array(coordinates)
        lon_range = coords[:, 0].max() - coords[:, 0].min()
        lat_range = coords[:, 1].max() - coords[:, 1].min()
        max_range = max(lon_range, lat_range)
        
        # For very small regions, increase zoom out factor significantly
        if max_range < 0.001:  # Very small region (< ~100m)
            zoom_out_factor = 6
        elif max_range < 0.01:  # Small region (< ~1km)
            zoom_out_factor = 8
        elif max_range < 0.05:  # Medium region (< ~5km)
            zoom_out_factor = 10
        
        # Create expanded region for zoom out
        center_lon = coords[:, 0].mean()
        center_lat = coords[:, 1].mean()
        
        # Calculate expanded bounds with adaptive zoom factor
        expanded_range = max_range * zoom_out_factor
        half_range = expanded_range / 2
        
        expanded_coords = [
            [center_lon - half_range, center_lat - half_range],
            [center_lon - half_range, center_lat + half_range],
            [center_lon + half_range, center_lat + half_range],
            [center_lon + half_range, center_lat - half_range],
            [center_lon - half_range, center_lat - half_range]
        ]
        
        # Use expanded area for satellite image
        expanded_aoi = coordinates_to_ee_geometry(expanded_coords)
        
        # Improved scale calculation for better resolution while showing context
        region_size_meters = expanded_range * 111000  # Rough conversion to meters
        
        # Calculate scale to ensure good resolution but show enough context
        base_scale = region_size_meters / image_size
        
        # For small regions, use SMALLER scale to show MORE DETAIL (zoom in)
        # Smaller scale = higher resolution, more detail
        if expanded_range < 0.005:  # Small regions like yours - ZOOM IN
            scale = max(base_scale, 2)   # High detail - 5m per pixel
        elif expanded_range < 0.01:  # Very small regions
            scale = max(base_scale, 4)   # Good detail
        elif expanded_range < 0.1:  # Moderately zoomed out
            scale = max(base_scale, 6)
        else:
            scale = max(base_scale, 8)  # Normal scale for larger regions
        
        print(f"    Using scale: {scale:.1f}m per pixel (zoom factor: {zoom_out_factor}x)")
        print(f"    Image size: {image_size}x{image_size} pixels")
        print(f"    Expanded region size: {expanded_range:.4f} degrees")
        
        # Try multiple satellite data sources in order of preference
        satellite_sources = [
            {
                'name': 'Sentinel-2 (10m resolution)',
                'collection': 'COPERNICUS/S2_SR_HARMONIZED',
                'bands': ['B4', 'B3', 'B2'],  # RGB
                'scale': max(scale, 10),
                'date_range': ('2020-01-01', '2024-12-31'),
                'vis_params': {'min': 0, 'max': 3000, 'gamma': 1.2}
            },
            {
                'name': 'Landsat 8-9 (30m resolution)', 
                'collection': 'LANDSAT/LC09/C02/T1_L2',
                'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # RGB
                'scale': max(scale, 30),
                'date_range': ('2020-01-01', '2024-12-31'),
                'vis_params': {'min': 0, 'max': 2000, 'gamma': 1.2}
            },
            {
                'name': 'Landsat 8 (30m resolution)',
                'collection': 'LANDSAT/LC08/C02/T1_L2', 
                'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # RGB
                'scale': max(scale, 30),
                'date_range': ('2015-01-01', '2024-12-31'),
                'vis_params': {'min': 0, 'max': 2000, 'gamma': 1.2}
            }
        ]
        
        for source in satellite_sources:
            try:
                print(f"    Trying {source['name']}...")
                
                # Get image collection
                if 'COPERNICUS' in source['collection']:
                    # Sentinel-2
                    collection = ee.ImageCollection(source['collection']) \
                        .filterBounds(expanded_aoi) \
                        .filterDate(source['date_range'][0], source['date_range'][1]) \
                        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover)) \
                        .sort('CLOUDY_PIXEL_PERCENTAGE')
                else:
                    # Landsat
                    collection = ee.ImageCollection(source['collection']) \
                        .filterBounds(expanded_aoi) \
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
                    **source['vis_params']
                }
                
                # Get the image URL for download using expanded area
                url = image.getThumbURL({
                    'region': expanded_aoi,
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
                    return True, expanded_coords, coordinates
                else:
                    print(f"      Failed to download from {source['name']}: HTTP {response.status_code}")
                    continue
                
            except Exception as e:
                print(f"      Error with {source['name']}: {str(e)[:100]}...")
                continue
        
        print("    All GEE satellite sources failed")
        return False, None, None
        
    except Exception as e:
        print(f"    GEE satellite image generation failed: {e}")
        return False, None, None

def add_overlay_to_image(image_path, original_coordinates, expanded_coordinates, 
                        edge_color='red', face_color='none', line_width=3, alpha=0.6):
    """
    Add colored overlay to the satellite image with better line quality
    """
    try:
        print("  Adding colored overlay to satellite image...")
        
        # Open the image
        img = Image.open(image_path).convert('RGBA')
        width, height = img.size
        
        # Create overlay with higher resolution for better line quality
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Convert coordinates to pixel coordinates
        expanded_coords = np.array(expanded_coordinates[:-1])  # Remove duplicate last point
        original_coords = np.array(original_coordinates[:-1] if original_coordinates[0] == original_coordinates[-1] 
                                  else original_coordinates)
        
        # Calculate bounds
        exp_lon_min, exp_lat_min = expanded_coords.min(axis=0)
        exp_lon_max, exp_lat_max = expanded_coords.max(axis=0)
        
        # Convert original coordinates to pixel coordinates
        pixel_coords = []
        for lon, lat in original_coords:
            # Normalize to 0-1
            x_norm = (lon - exp_lon_min) / (exp_lon_max - exp_lon_min)
            y_norm = 1 - (lat - exp_lat_min) / (exp_lat_max - exp_lat_min)  # Flip Y axis
            
            # Convert to pixel coordinates
            x_pixel = int(x_norm * width)
            y_pixel = int(y_norm * height)
            pixel_coords.append((x_pixel, y_pixel))
        
        # Parse colors
        def parse_color(color_str):
            if color_str == 'none':
                return None
            elif color_str == 'red':
                return (255, 0, 0, int(255 * alpha))
            elif color_str == 'blue':
                return (0, 0, 255, int(255 * alpha))
            elif color_str == 'green':
                return (0, 255, 0, int(255 * alpha))
            elif color_str == 'yellow':
                return (255, 255, 0, int(255 * alpha))
            elif color_str == 'cyan':
                return (0, 255, 255, int(255 * alpha))
            elif color_str == 'magenta':
                return (255, 0, 255, int(255 * alpha))
            elif color_str == 'orange':
                return (255, 165, 0, int(255 * alpha))
            else:
                return (255, 0, 0, int(255 * alpha))  # Default to red
        
        # Draw filled polygon if face_color is not 'none'
        if face_color != 'none':
            fill_color = parse_color(face_color)
            if fill_color:
                draw.polygon(pixel_coords, fill=fill_color)
        
        # Draw outline if edge_color is not 'none'
        if edge_color != 'none':
            outline_color = parse_color(edge_color)
            if outline_color:
                # Make outline fully opaque and thicker for better visibility
                outline_color = outline_color[:3] + (255,)
                draw.polygon(pixel_coords, outline=outline_color, width=line_width)
        
        # Composite the overlay onto the original image
        img = Image.alpha_composite(img, overlay)
        
        # Convert back to RGB and save
        img = img.convert('RGB')
        img.save(image_path, 'PNG', quality=95)
        
        print(f"    Overlay added successfully")
        return True
        
    except Exception as e:
        print(f"    Error adding overlay: {e}")
        return False

def generate_region_satellite_map_gee(coordinates, output_path="assets/images/region_screenshot.png", 
                                     figsize=(8, 6), alpha=0.6,  # Changed figsize for half A4
                                     edge_color='none', face_color='none',
                                     line_width=3, use_gee_first=True,
                                     add_padding=True, padding_factor=0.1,
                                     zoom_out_factor=5):  # Increased default zoom out factor
    """
    Generate satellite map using Google Earth Engine first, with contextily fallback
    Now optimized for better resolution and half A4 page size
    """
    
    try:
        print(f"Generating high-resolution satellite map for region...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to numpy array
        coords = np.array(coordinates)
        
        success = False
        
        # Method 1: Try Google Earth Engine first with improved settings
        if use_gee_first:
            print(f"Method 1: Trying Google Earth Engine (zoom out factor: {zoom_out_factor}x)...")
            success, expanded_coords, original_coords = get_satellite_image_from_gee(
                coordinates=coords.tolist(),
                output_path=output_path,
                image_size=2048,  # Increased resolution
                zoom_out_factor=zoom_out_factor
            )
            
            # Add overlay if GEE was successful and overlay is requested
            if success and (edge_color != 'none' or face_color != 'none'):
                overlay_success = add_overlay_to_image(
                    image_path=output_path,
                    original_coordinates=original_coords,
                    expanded_coordinates=expanded_coords,
                    edge_color=edge_color,
                    face_color=face_color,
                    line_width=line_width,
                    alpha=alpha
                )
                if not overlay_success:
                    print("  Warning: Failed to add overlay to GEE image")
        
        # Method 2: Fallback to contextily if GEE fails
        if not success:
            print("Method 2: Falling back to contextily providers...")
            
            # Add padding for very small regions if requested
            if add_padding:
                coords = add_region_padding(coords, padding_factor)
                print(f"  Added {padding_factor*100}% padding to region")
            
            success = generate_contextily_satellite_map(
                coordinates=coords,
                output_path=output_path,
                figsize=figsize,
                alpha=alpha,
                edge_color=edge_color,
                face_color=face_color,
                line_width=line_width
            )
        
        # Resize image to half A4 dimensions if successful
        if success:
            resize_image_for_half_a4(output_path)
            print(f"  Region satellite map saved to: {output_path}")
        else:
            print(f"  All satellite sources failed")
            
        return success
        
    except Exception as e:
        print(f"  Error generating satellite map: {e}")
        return False

def resize_image_for_half_a4(image_path):
    """
    Resize image to appropriate dimensions for half A4 page
    Half A4 at 300 DPI: ~1240x875 pixels
    """
    try:
        print("  Resizing image for half A4 page...")
        
        # Open the image
        img = Image.open(image_path)
        
        # Calculate dimensions for half A4 (landscape orientation)
        # A4 is 210mm x 297mm, half A4 is roughly 148mm x 105mm
        # At 300 DPI: 148mm = ~1748px, 105mm = ~1240px
        target_width = 1240
        target_height = 950
        
        # Resize maintaining aspect ratio, then crop to exact dimensions
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # Image is wider than target, fit to height
            new_height = target_height
            new_width = int(target_height * img_ratio)
        else:
            # Image is taller than target, fit to width
            new_width = target_width
            new_height = int(target_width / img_ratio)
        
        # Resize the image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact target dimensions (center crop)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        img = img.crop((left, top, right, bottom))
        
        # Save the resized image
        img.save(image_path, 'PNG', quality=95, optimize=True)
        
        print(f"    Image resized to {target_width}x{target_height} pixels for half A4")
        
    except Exception as e:
        print(f"    Error resizing image: {e}")

def generate_contextily_satellite_map(coordinates, output_path, figsize=(8, 6), 
                                     alpha=0.6, edge_color='none', face_color='none',
                                     line_width=3):
    """
    Generate satellite map using contextily with improved resolution
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
        
        # Calculate adaptive zoom with higher resolution
        zoom = calculate_adaptive_zoom(coordinates, min_zoom=12, max_zoom=20)
        
        # Create the plot with higher DPI
        fig, ax = plt.subplots(figsize=figsize, facecolor='white', dpi=300)
        
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
                
                # Add satellite basemap with higher zoom
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
        
        # Save the map with higher DPI
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='none', edgecolor='none')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"    Contextily generation failed: {e}")
        return False

def calculate_adaptive_zoom(coordinates, min_zoom=10, max_zoom=16):
    """
    Calculate appropriate zoom level based on region size - lower zoom shows more area
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
        
        # For small regions, use LOWER zoom levels to show more context
        # Lower zoom = more area visible, higher zoom = more detail but less area
        if max_dimension < 50:    # Very small region (< 50m)
            zoom = 10  # Show much more context
        elif max_dimension < 100: # Small region (< 100m)
            zoom = 11
        elif max_dimension < 500: # Medium-small region (< 500m)
            zoom = 12
        elif max_dimension < 1000: # Medium region (< 1km)
            zoom = 13
        elif max_dimension < 2000: # Large region (< 2km)
            zoom = 14
        else:
            zoom = max_zoom
        
        # Ensure zoom is within bounds
        zoom = max(min_zoom, min(max_zoom, zoom))
        
        return zoom
        
    except Exception as e:
        return 13  # Lower default to show more context

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