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
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import requests

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

def add_professional_watermark(image_path, data_source="Google Earth Engine", 
                             image_date=None, position="top-left", 
                             font_size=16, margin=15):
    """
    Add professional data source watermark similar to Google Earth style
    
    Args:
        image_path: Path to the image file
        data_source: Data source text (e.g., "Sentinel-2 via Google Earth Engine")
        image_date: Date string or datetime object for the image
        position: Where to place the watermark ("top-left", "top-right", "bottom-left", "bottom-right")
        font_size: Size of the text
        margin: Margin from the edge in pixels
    """
    try:
        print(f"  Adding professional watermark: {data_source}")
        
        # Open the image
        img = Image.open(image_path).convert('RGBA')
        width, height = img.size
        
        # Format the date
        if image_date is None:
            image_date = datetime.now()
        elif isinstance(image_date, str):
            try:
                # Try to parse the date string
                image_date = datetime.strptime(image_date, '%Y-%m-%d')
            except:
                image_date = datetime.now()
        
        date_str = image_date.strftime("%B %d, %Y")
        
        # Prepare watermark text
        source_text = f"Image Source: {data_source}"
        date_text = f"Image Date: {date_str}"
        
        # Try to load a system font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        
        # Create overlay for watermark
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get text dimensions
        source_bbox = draw.textbbox((0, 0), source_text, font=font)
        date_bbox = draw.textbbox((0, 0), date_text, font=font)
        
        source_width = source_bbox[2] - source_bbox[0]
        source_height = source_bbox[3] - source_bbox[1]
        date_width = date_bbox[2] - date_bbox[0]
        date_height = date_bbox[3] - date_bbox[1]
        
        # Calculate total dimensions
        max_width = max(source_width, date_width)
        total_height = source_height + date_height + 5  # 5px gap between lines
        
        # Calculate position
        if position == "top-left":
            x = margin
            y = margin
        elif position == "top-right":
            x = width - max_width - margin
            y = margin
        elif position == "bottom-left":
            x = margin
            y = height - total_height - margin
        elif position == "bottom-right":
            x = width - max_width - margin
            y = height - total_height - margin
        else:
            # Default to top-left
            x = margin
            y = margin
        
        # Add semi-transparent background
        padding = 8
        bg_x1 = x - padding
        bg_y1 = y - padding
        bg_x2 = x + max_width + padding
        bg_y2 = y + total_height + padding
        
        # Draw background rectangle with rounded corners effect
        background_color = (255, 255, 255, 200)  # Semi-transparent white
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=background_color)
        
        # Add subtle border
        border_color = (0, 0, 0, 100)  # Semi-transparent black
        draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], outline=border_color, width=1)
        
        # Draw the text
        text_color = (0, 0, 0, 255)  # Black text
        draw.text((x, y), source_text, fill=text_color, font=font)
        draw.text((x, y + source_height + 5), date_text, fill=text_color, font=font)
        
        # Composite the overlay onto the original image
        img = Image.alpha_composite(img, overlay)
        
        # Convert back to RGB and save
        img = img.convert('RGB')
        img.save(image_path, 'PNG', quality=95)
        
        print(f"    Professional watermark added: {data_source}")
        return True
        
    except Exception as e:
        print(f"    Error adding professional watermark: {e}")
        return False

def get_satellite_image_from_gee(coordinates, output_path, image_size=2048, max_cloud_cover=20, zoom_out_factor=3):
    """
    Get high-quality satellite imagery from Google Earth Engine with enhanced metadata tracking
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
        
        print(f"    Original region size: {max_range:.4f} degrees (~{max_range*111:.1f}km)")
        
        # Better zoom out factor logic
        if max_range < 0.001:  # Very small region (< ~100m)
            zoom_out_factor = 3
        elif max_range < 0.01:  # Small region (< ~1km)
            zoom_out_factor = 3
        elif max_range < 0.1:  # Medium-large region (< ~10km)
            zoom_out_factor = 1.5
        else:  # Very large regions
            zoom_out_factor = 1.2
        
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
        
        # Proper scale calculation based on expanded area size
        region_size_meters = expanded_range * 111000  # Convert degrees to meters
        calculated_scale = region_size_meters / image_size
        
        # Set minimum scale based on satellite resolution and region size
        if expanded_range < 0.01:  # Small expanded region (< ~1km)
            min_scale = 2
        elif expanded_range < 0.05:  # Medium expanded region (< ~5km)  
            min_scale = 10
        elif expanded_range < 0.2:  # Large expanded region (< ~20km)
            min_scale = 20
        else:  # Very large expanded region
            min_scale = 50
        
        scale = max(calculated_scale, min_scale)
        
        print(f"    Zoom out factor: {zoom_out_factor}x")
        print(f"    Expanded region size: {expanded_range:.4f} degrees (~{expanded_range*111:.1f}km)")
        print(f"    Using scale: {scale:.1f}m per pixel")
        print(f"    Image size: {image_size}x{image_size} pixels")
        
        # Define satellite data sources with enhanced metadata
        satellite_sources = [
            {
                'name': 'Sentinel-2 (10m resolution)',
                'collection': 'COPERNICUS/S2_SR_HARMONIZED',
                'bands': ['B4', 'B3', 'B2'],  # RGB
                'scale': max(scale, 10),
                'date_range': ('2023-01-01', '2024-12-31'),
                'vis_params': {'min': 0, 'max': 3000, 'gamma': 1.2},
                'watermark_source': 'Sentinel-2 via Google Earth Engine',
                'cloud_property': 'CLOUDY_PIXEL_PERCENTAGE'
            },
            {
                'name': 'Landsat 9 (30m resolution)', 
                'collection': 'LANDSAT/LC09/C02/T1_L2',
                'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # RGB
                'scale': max(scale, 30),
                'date_range': ('2022-01-01', '2024-12-31'),
                'vis_params': {'min': 0, 'max': 20000, 'gamma': 1.2},
                'watermark_source': 'Landsat 9 via Google Earth Engine',
                'cloud_property': 'CLOUD_COVER'
            },
            {
                'name': 'Landsat 8 (30m resolution)',
                'collection': 'LANDSAT/LC08/C02/T1_L2', 
                'bands': ['SR_B4', 'SR_B3', 'SR_B2'],  # RGB
                'scale': max(scale, 30),
                'date_range': ('2020-01-01', '2024-12-31'),
                'vis_params': {'min': 0, 'max': 20000, 'gamma': 1.2},
                'watermark_source': 'Landsat 8 via Google Earth Engine',
                'cloud_property': 'CLOUD_COVER'
            }
        ]
        
        for source in satellite_sources:
            try:
                print(f"    Trying {source['name']} at {source['scale']:.1f}m resolution...")
                
                # Get image collection
                collection = ee.ImageCollection(source['collection']) \
                    .filterBounds(expanded_aoi) \
                    .filterDate(source['date_range'][0], source['date_range'][1]) \
                    .filter(ee.Filter.lte(source['cloud_property'], max_cloud_cover)) \
                    .sort(source['cloud_property'])
                
                # Check if any images are available
                count = collection.size().getInfo()
                if count == 0:
                    print(f"      No images available for {source['name']}")
                    continue
                
                print(f"      Found {count} images, using the clearest one")
                
                # Get the best (least cloudy) image and its metadata
                best_image = collection.first()
                image_for_viz = best_image.select(source['bands'])
                
                # Get image date
                image_date = ee.Date(best_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
                
                # Scale pixel values for visualization (Landsat needs scaling)
                if 'LANDSAT' in source['collection']:
                    image_for_viz = image_for_viz.multiply(0.0000275).add(-0.2) \
                        .multiply(10000).clamp(0, 10000).uint16()
                
                # Create visualization parameters for RGB
                vis_params = {
                    'bands': source['bands'],
                    **source['vis_params']
                }
                
                # Get the image URL for download
                url = image_for_viz.getThumbURL({
                    'region': expanded_aoi,
                    'dimensions': image_size,
                    'format': 'png',
                    **vis_params
                })
                
                print(f"      Requesting image from GEE...")
                
                # Download the image
                response = requests.get(url, timeout=120)
                if response.status_code == 200:
                    if len(response.content) > 10000:  # At least 10KB for a real image
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        
                        print(f"    ✅ Successfully downloaded satellite image from {source['name']}")
                        print(f"       Image date: {image_date}")
                        print(f"       File size: {len(response.content)} bytes")
                        
                        # Return success with metadata
                        return True, expanded_coords, coordinates, source['watermark_source'], image_date
                    else:
                        print(f"      Downloaded file too small ({len(response.content)} bytes)")
                        continue
                else:
                    print(f"      Failed to download: HTTP {response.status_code}")
                    continue
                
            except Exception as e:
                print(f"      Error with {source['name']}: {str(e)[:100]}...")
                continue
        
        print("    ❌ All GEE satellite sources failed")
        return False, None, None, None, None
        
    except Exception as e:
        print(f"    ❌ GEE satellite image generation failed: {e}")
        return False, None, None, None, None

def add_overlay_to_image(image_path, original_coordinates, expanded_coordinates, 
                        edge_color='red', face_color='none', line_width=3, alpha=0.6):
    """
    Add colored overlay to the satellite image
    """
    try:
        print("  Adding colored overlay to satellite image...")
        
        # Open the image
        img = Image.open(image_path).convert('RGBA')
        width, height = img.size
        
        # Create overlay
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
            x_norm = (lon - exp_lon_min) / (exp_lon_max - exp_lon_min)
            y_norm = 1 - (lat - exp_lat_min) / (exp_lat_max - exp_lat_min)  # Flip Y axis
            
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
                outline_color = outline_color[:3] + (255,)  # Make outline fully opaque
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

def resize_image_for_half_a4(image_path):
    """
    Resize image to appropriate dimensions for half A4 page
    """
    try:
        print("  Resizing image for half A4 page...")
        
        img = Image.open(image_path)
        
        # Target dimensions for half A4
        target_width = 1240
        target_height = 950
        
        # Resize maintaining aspect ratio, then crop to exact dimensions
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            new_height = target_height
            new_width = int(target_height * img_ratio)
        else:
            new_width = target_width
            new_height = int(target_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        img = img.crop((left, top, right, bottom))
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
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        gdf_mercator = gdf.to_crs(epsg=3857)
        
        # Calculate adaptive zoom
        zoom = calculate_adaptive_zoom(coordinates, min_zoom=12, max_zoom=20)
        
        # Create the plot
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
        
        # Determine zoom level based on region size
        if max_dimension < 100:    # Very small region (< 100m)
            zoom = 18
        elif max_dimension < 500:  # Small region (< 500m)
            zoom = 16
        elif max_dimension < 1000: # Medium region (< 1km)
            zoom = 15
        elif max_dimension < 2000: # Large region (< 2km)
            zoom = 14
        elif max_dimension < 5000: # Very large region (< 5km)
            zoom = 13
        else:
            zoom = 12
        
        # Ensure zoom is within bounds
        zoom = max(min_zoom, min(max_zoom, zoom))
        
        return zoom
        
    except Exception as e:
        return 13  # Default zoom

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

def generate_region_satellite_map_gee(coordinates, output_path="assets/images/region_screenshot.png", 
                                     figsize=(8, 6), alpha=0.6,
                                     edge_color='none', face_color='none',
                                     line_width=3, use_gee_first=True,
                                     add_padding=False, padding_factor=0.1,
                                     zoom_out_factor=3, add_watermark=True,
                                     watermark_position="top-left"):
    """
    Generate satellite map with professional watermark similar to Google Earth
    """
    
    try:
        print(f"Generating high-resolution satellite map for region...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to numpy array
        coords = np.array(coordinates)
        
        # Calculate region size to determine approach
        lon_range = coords[:, 0].max() - coords[:, 0].min()
        lat_range = coords[:, 1].max() - coords[:, 1].min()
        max_range = max(lon_range, lat_range)
        
        print(f"Region size: {max_range:.4f} degrees (~{max_range*111:.1f}km)")
        
        # Disable padding for medium/large regions
        if max_range > 0.02:  # Larger than ~2km
            add_padding = False
            print("  Disabled padding for large region")
        
        success = False
        data_source_used = None
        image_date = None
        
        # Method 1: Try Google Earth Engine first
        if use_gee_first:
            print(f"Method 1: Trying Google Earth Engine...")
            success, expanded_coords, original_coords, data_source_used, image_date = get_satellite_image_from_gee(
                coordinates=coords.tolist(),
                output_path=output_path,
                image_size=2048,
                zoom_out_factor=zoom_out_factor
            )
            
            # Add overlay if GEE was successful
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
            
            # RESIZE FIRST, THEN ADD WATERMARK
            if success:
                print("  Resizing image before adding watermark...")
                resize_image_for_half_a4(output_path)
                
                # Add professional watermark AFTER resizing
                if add_watermark:
                    print("  Adding watermark after resize...")
                    add_professional_watermark(
                        image_path=output_path,
                        data_source=data_source_used,
                        image_date=image_date,
                        position=watermark_position
                    )
        
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
            
            # Resize and add watermark for contextily fallback
            if success:
                resize_image_for_half_a4(output_path)
                if add_watermark:
                    add_professional_watermark(
                        image_path=output_path,
                        data_source="ESRI World Imagery via Contextily",
                        image_date=datetime.now(),
                        position=watermark_position
                    )
        
        # Final success message (no additional resize here)
        if success:
            print(f"  ✅ Region satellite map saved to: {output_path}")
        else:
            print(f"  ❌ All satellite sources failed")
            
        return success
        
    except Exception as e:
        print(f"  ❌ Error generating satellite map: {e}")
        return False


# Example usage functions
def example_usage():
    """
    Example of how to use the satellite mapping functions
    """
    
    # Example coordinates (a small area in New York City)
    example_coordinates = [
        [-74.0059, 40.7128],  # Southwest corner
        [-74.0059, 40.7180],  # Northwest corner  
        [-74.0000, 40.7180],  # Northeast corner
        [-74.0000, 40.7128],  # Southeast corner
        [-74.0059, 40.7128]   # Close the polygon
    ]
    
    print("Example 1: Basic satellite map with red outline")
    success1 = generate_region_satellite_map_gee(
        coordinates=example_coordinates,
        output_path="assets/images/example_red_outline.png",
        edge_color='red',
        face_color='none',
        line_width=3,
        add_watermark=True,
        watermark_position="top-left"
    )
    
    print(f"\nExample 1 result: {'Success' if success1 else 'Failed'}")
    
    print("\nExample 2: Satellite map with semi-transparent blue fill")
    success2 = generate_region_satellite_map_gee(
        coordinates=example_coordinates,
        output_path="assets/images/example_blue_fill.png",
        edge_color='blue',
        face_color='blue',
        alpha=0.3,
        line_width=2,
        add_watermark=True,
        watermark_position="bottom-right"
    )
    
    print(f"Example 2 result: {'Success' if success2 else 'Failed'}")
    
    print("\nExample 3: Clean satellite map without overlay but with watermark")
    success3 = generate_region_satellite_map_gee(
        coordinates=example_coordinates,
        output_path="assets/images/example_clean.png",
        edge_color='none',
        face_color='none',
        add_watermark=True,
        watermark_position="top-right"
    )
    
    print(f"Example 3 result: {'Success' if success3 else 'Failed'}")


def generate_map_from_metrics(metrics_data, output_path="assets/images/region_screenshot.png",
                            style_config=None):
    """
    Generate satellite map from your metrics data with customizable styling
    
    Args:
        metrics_data: Your metrics data object containing coordinates
        output_path: Where to save the generated map
        style_config: Dictionary with styling options
    """
    
    # Default style configuration
    default_style = {
        'edge_color': 'red',
        'face_color': 'none',
        'line_width': 3,
        'alpha': 0.6,
        'add_watermark': True,
        'watermark_position': 'top-left',
        'use_gee_first': True,
        'zoom_out_factor': 3
    }
    
    # Merge with user-provided style config
    if style_config:
        default_style.update(style_config)
    
    try:
        # Extract coordinates from your metrics data
        coordinates = extract_coordinates_from_metrics(metrics_data)
        
        print(f"Generating satellite map from metrics data...")
        print(f"Coordinates extracted: {len(coordinates)} points")
        
        # Generate the map
        success = generate_region_satellite_map_gee(
            coordinates=coordinates,
            output_path=output_path,
            **default_style
        )
        
        if success:
            print(f"✅ Satellite map successfully generated: {output_path}")
        else:
            print(f"❌ Failed to generate satellite map")
            
        return success
        
    except Exception as e:
        print(f"❌ Error generating map from metrics: {e}")
        return False


def add_watermark_to_existing_image(image_path, data_source=None, image_date=None, 
                                   position="top-left"):
    """
    Add watermark to an existing image
    
    Args:
        image_path: Path to existing image
        data_source: Source of the data (if None, tries to detect from filename)
        image_date: Date of the image (if None, uses current date)
        position: Position for the watermark
    """
    
    try:
        # Auto-detect data source if not provided
        if data_source is None:
            filename = os.path.basename(image_path).lower()
            if 'sentinel' in filename:
                data_source = "Sentinel-2 via Google Earth Engine"
            elif 'landsat' in filename:
                data_source = "Landsat via Google Earth Engine"
            elif 'esri' in filename or 'arcgis' in filename:
                data_source = "ESRI World Imagery"
            else:
                data_source = "Satellite Imagery"
        
        print(f"Adding watermark to existing image: {image_path}")
        
        success = add_professional_watermark(
            image_path=image_path,
            data_source=data_source,
            image_date=image_date,
            position=position
        )
        
        if success:
            print(f"✅ Watermark added successfully")
        else:
            print(f"❌ Failed to add watermark")
            
        return success
        
    except Exception as e:
        print(f"❌ Error adding watermark to existing image: {e}")
        return False


# Main execution function
if __name__ == "__main__":
    """
    Main execution - you can customize this section for your specific needs
    """
    
    print("🛰️  Satellite Imagery Generator with Professional Watermarks")
    print("=" * 60)
    
    # Run examples
    print("\n📍 Running example usage...")
    example_usage()
    
    print("\n" + "=" * 60)
    print("✅ Script execution completed!")
    print("\nTo use in your code:")
    print("1. Call generate_region_satellite_map_gee() with your coordinates")
    print("2. Use generate_map_from_metrics() with your metrics data")
    print("3. Use add_watermark_to_existing_image() for existing images")
    print("\nWatermark styles available:")
    print("- Professional Google Earth-style layout")
    print("- Customizable position (top-left, top-right, bottom-left, bottom-right)")
    print("- Automatic data source detection")
    print("- Date formatting and display")


# Additional utility functions for advanced usage

def batch_process_images(image_folder, data_source="Satellite Imagery", 
                        watermark_position="top-left"):
    """
    Add watermarks to all images in a folder
    """
    try:
        print(f"Batch processing images in: {image_folder}")
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.tif']
        processed_count = 0
        
        for filename in os.listdir(image_folder):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(image_folder, filename)
                
                print(f"Processing: {filename}")
                success = add_watermark_to_existing_image(
                    image_path=image_path,
                    data_source=data_source,
                    position=watermark_position
                )
                
                if success:
                    processed_count += 1
        
        print(f"✅ Processed {processed_count} images successfully")
        return processed_count
        
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        return 0


def create_comparison_map(coordinates, output_folder="assets/images/comparison/"):
    """
    Create multiple versions of the same region for comparison
    """
    try:
        print("Creating comparison maps for the same region...")
        
        os.makedirs(output_folder, exist_ok=True)
        
        # Different style configurations
        styles = {
            "clean": {
                'edge_color': 'none',
                'face_color': 'none',
                'watermark_position': 'top-left'
            },
            "red_outline": {
                'edge_color': 'red',
                'face_color': 'none',
                'line_width': 3,
                'watermark_position': 'top-right'
            },
            "blue_fill": {
                'edge_color': 'blue',
                'face_color': 'blue',
                'alpha': 0.3,
                'watermark_position': 'bottom-left'
            },
            "yellow_outline": {
                'edge_color': 'yellow',
                'face_color': 'none',
                'line_width': 4,
                'watermark_position': 'bottom-right'
            }
        }
        
        results = {}
        
        for style_name, style_config in styles.items():
            output_path = os.path.join(output_folder, f"comparison_{style_name}.png")
            
            print(f"\nGenerating {style_name} version...")
            success = generate_region_satellite_map_gee(
                coordinates=coordinates,
                output_path=output_path,
                **style_config
            )
            
            results[style_name] = success
            
        print(f"\n✅ Comparison maps created in: {output_folder}")
        return results
        
    except Exception as e:
        print(f"❌ Error creating comparison maps: {e}")
        return {}