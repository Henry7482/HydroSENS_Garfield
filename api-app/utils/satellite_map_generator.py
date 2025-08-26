
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Polygon
import warnings
import os

warnings.filterwarnings('ignore')

def calculate_adaptive_zoom(coordinates, min_zoom=10, max_zoom=18):
    """
    Calculate appropriate zoom level based on region size
    
    Parameters:
    -----------
    coordinates : list
        List of [longitude, latitude] coordinate pairs
    min_zoom : int
        Minimum zoom level to use
    max_zoom : int
        Maximum zoom level to use
        
    Returns:
    --------
    int : Recommended zoom level
    """
    try:
        coords = np.array(coordinates)
        
        # Calculate bounding box dimensions
        lon_min, lon_max = coords[:, 0].min(), coords[:, 0].max()
        lat_min, lat_max = coords[:, 1].min(), coords[:, 1].max()
        
        # Calculate width and height in degrees
        width_deg = lon_max - lon_min
        height_deg = lat_max - lat_min
        
        # Calculate approximate dimensions in meters (rough approximation)
        # 1 degree longitude ≈ 111320 * cos(latitude) meters
        # 1 degree latitude ≈ 110540 meters
        avg_lat = (lat_min + lat_max) / 2
        width_meters = width_deg * 111320 * np.cos(np.radians(avg_lat))
        height_meters = height_deg * 110540
        
        # Use the larger dimension for zoom calculation
        max_dimension = max(width_meters, height_meters)
        
        print(f"  Region dimensions: {width_meters:.1f}m x {height_meters:.1f}m")
        print(f"  Max dimension: {max_dimension:.1f}m")
        
        # Adaptive zoom based on region size
        if max_dimension < 200:        # Very small (< 200m)
            zoom = max_zoom           # Use highest zoom (18)
        elif max_dimension < 500:      # Small (< 500m)  
            zoom = 17
        elif max_dimension < 1000:     # Medium-small (< 1km)
            zoom = 16
        elif max_dimension < 2000:     # Medium (< 2km)
            zoom = 15
        elif max_dimension < 5000:     # Medium-large (< 5km)
            zoom = 14
        elif max_dimension < 10000:    # Large (< 10km)
            zoom = 13
        elif max_dimension < 20000:    # Very large (< 20km)
            zoom = 12
        else:                         # Huge (> 20km)
            zoom = min_zoom
        
        # Ensure zoom is within bounds
        zoom = max(min_zoom, min(max_zoom, zoom))
        
        print(f"  Calculated zoom level: {zoom}")
        return zoom
        
    except Exception as e:
        print(f"  Error calculating zoom level: {e}")
        return 15  # Safe default

def generate_region_satellite_map(coordinates, output_path="assets/images/region_screenshot.png", 
                                 figsize=(12, 10), alpha=0.6, 
                                 edge_color='none', face_color='none',
                                 line_width=3, zoom='auto', force_zoom=None,
                                 add_padding=True, padding_factor=0.2):
    """
    Generate satellite map from coordinates with adaptive zoom and padding
    
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
    zoom : str or int
        Zoom level ('auto' for adaptive calculation, or integer 1-19)
    force_zoom : int or None
        Force specific zoom level, overrides adaptive calculation
    add_padding : bool
        Whether to add padding around small regions
    padding_factor : float
        How much padding to add (0.2 = 20% of region size)
    
    Returns:
    --------
    bool : True if successful, False otherwise
    """
    
    try:
        print(f"Generating satellite map for region...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to numpy array
        coords = np.array(coordinates)
        
        # Add padding for very small regions
        if add_padding:
            coords = add_region_padding(coords, padding_factor)
            print(f"  Added {padding_factor*100}% padding to region")
        
        # Ensure polygon is closed
        if not np.array_equal(coords[0], coords[-1]):
            coords = np.vstack([coords, coords[0]])
        
        # Create a polygon from coordinates
        polygon = Polygon(coords)
        
        # Create GeoDataFrame with WGS84 coordinates
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        
        # Reproject to Web Mercator (EPSG:3857) for contextily compatibility
        gdf_mercator = gdf.to_crs(epsg=3857)
        
        # Calculate zoom level
        if force_zoom is not None:
            calculated_zoom = force_zoom
            print(f"  Using forced zoom level: {calculated_zoom}")
        elif zoom == 'auto':
            calculated_zoom = calculate_adaptive_zoom(coordinates)
        else:
            calculated_zoom = zoom
            print(f"  Using manual zoom level: {calculated_zoom}")
        
        # Create the plot
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Define satellite imagery providers with fallbacks
        providers_to_try = [
            ("ESRI World Imagery", ctx.providers.Esri.WorldImagery),
            ("CartoDB Voyager", ctx.providers.CartoDB.Voyager),
            ("OpenStreetMap", ctx.providers.OpenStreetMap.Mapnik)
        ]
        
        # Try each provider until one works
        basemap_added = False
        for i, (provider_name, tile_provider) in enumerate(providers_to_try):
            try:
                print(f"  Trying provider {i+1}: {provider_name}")
                print(f"    Zoom level: {calculated_zoom}")
                print(f"    Bounds: {gdf_mercator.total_bounds}")
                
                # Plot the polygon first (if not 'none')
                if face_color != 'none' or edge_color != 'none':
                    gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
                                    edgecolor=edge_color, linewidth=line_width)
                
                # Add satellite basemap with calculated zoom
                ctx.add_basemap(ax, crs=gdf_mercator.crs, source=tile_provider, 
                              zoom=calculated_zoom, attribution_size=0)
                
                basemap_added = True
                print(f"  Successfully added satellite imagery from {provider_name}")
                break
                
            except Exception as e:
                print(f"  Provider {i+1} ({provider_name}) failed: {str(e)[:100]}...")
                ax.clear()  # Clear the plot for next attempt
                
                # Try with different zoom levels if the current one fails
                if "zoom" in str(e).lower() or "tile" in str(e).lower():
                    for retry_zoom in [calculated_zoom-1, calculated_zoom+1, 15, 16, 14]:
                        if retry_zoom < 10 or retry_zoom > 18:
                            continue
                        try:
                            print(f"    Retrying with zoom level {retry_zoom}...")
                            
                            if face_color != 'none' or edge_color != 'none':
                                gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
                                                edgecolor=edge_color, linewidth=line_width)
                            
                            ctx.add_basemap(ax, crs=gdf_mercator.crs, source=tile_provider, 
                                          zoom=retry_zoom, attribution_size=0)
                            
                            basemap_added = True
                            print(f"  Success with retry zoom {retry_zoom}")
                            break
                        except Exception as retry_e:
                            ax.clear()
                            continue
                    
                    if basemap_added:
                        break
                
                continue
        
        if not basemap_added:
            print("  All satellite providers failed. Creating styled map fallback...")
            # Fallback: create a styled map without satellite imagery
            gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
                            edgecolor=edge_color, linewidth=line_width)
            ax.set_facecolor('#f0f8e8')  # Light green background
            ax.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.5)
        
        # Customize the plot
        ax.set_axis_off()  # Remove axes for cleaner view
        
        # Ensure tight layout
        plt.tight_layout()
        
        # Save the map
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='none', edgecolor='none')
        plt.close()
        
        print(f"  Region map saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"  Error generating satellite map: {e}")
        return False

def add_region_padding(coordinates, padding_factor=0.2):
    """
    Add padding around small regions to ensure good satellite imagery
    
    Parameters:
    -----------
    coordinates : numpy.array
        Array of [longitude, latitude] coordinate pairs
    padding_factor : float
        Fraction of region size to add as padding (0.2 = 20%)
        
    Returns:
    --------
    numpy.array : Padded coordinates
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
    Modify this function based on your actual data structure
    """
    try:
        # Option 1: If coordinates are directly in metrics_data
        if hasattr(metrics_data, 'coordinates'):
            return metrics_data.coordinates
        
        # Option 2: If coordinates are in a nested structure
        if hasattr(metrics_data, 'region') and hasattr(metrics_data.region, 'coordinates'):
            return metrics_data.region.coordinates
        
        # Option 3: If it's a dictionary
        if isinstance(metrics_data, dict):
            if 'coordinates' in metrics_data:
                return metrics_data['coordinates']
            elif 'region' in metrics_data and 'coordinates' in metrics_data['region']:
                return metrics_data['region']['coordinates']
        
        # Option 4: Default example coordinates if none found
        print("  No coordinates found in metrics_data, using default region")
        return [
            [-74.0059, 40.7128],  # Default: New York area
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
            [-74.0059, 40.7128]
        ]
        
    except Exception as e:
        print(f"  Error extracting coordinates: {e}")
        # Return default coordinates as fallback
        return [
            [-74.0059, 40.7128],
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
            [-74.0059, 40.7128]
        ]

# def generate_region_satellite_map(coordinates, output_path="assets/images/region_screenshot.png", 
#                                  figsize=(12, 10), alpha=0.6, 
#                                  edge_color='none', face_color='none',
#                                  line_width=3, zoom='auto'):
#     """
#     Generate satellite map from coordinates and save to specified path
    
#     Parameters:
#     -----------
#     coordinates : list or array
#         List of [longitude, latitude] coordinate pairs
#     output_path : str
#         Path where to save the generated map image
#     figsize : tuple
#         Figure size (width, height) in inches
#     alpha : float
#         Transparency of the region overlay (0-1)
#     edge_color : str
#         Color of the region border
#     face_color : str
#         Fill color of the region
#     line_width : int
#         Width of the region border
#     zoom : str or int
#         Zoom level ('auto' for automatic, or integer 1-19)
    
#     Returns:
#     --------
#     bool : True if successful, False otherwise
#     """
    
#     try:
#         print(f"Generating satellite map for region...")
        
#         # Ensure output directory exists
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
#         # Convert coordinates to numpy array and ensure polygon is closed
#         coords = np.array(coordinates)
#         if not np.array_equal(coords[0], coords[-1]):
#             coords = np.vstack([coords, coords[0]])  # Close the polygon
        
#         # Create a polygon from coordinates
#         polygon = Polygon(coords)
        
#         # Create GeoDataFrame with WGS84 coordinates
#         gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        
#         # Reproject to Web Mercator (EPSG:3857) for contextily compatibility
#         gdf_mercator = gdf.to_crs(epsg=3857)
        
#         # Create the plot
#         fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
#         # Define satellite imagery providers with fallbacks
#         providers_to_try = [
#             ctx.providers.Esri.WorldImagery,
#             ctx.providers.CartoDB.Voyager,
#             ctx.providers.OpenStreetMap.Mapnik
#         ]
        
#         # Try each provider until one works
#         basemap_added = False
#         for i, tile_provider in enumerate(providers_to_try):
#             try:
#                 print(f"  Trying satellite provider {i+1}...")
                
#                 # Plot the polygon first
#                 gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
#                                 edgecolor=edge_color, linewidth=line_width)
                
#                 # Add satellite basemap
#                 ctx.add_basemap(ax, crs=gdf_mercator.crs, source=tile_provider, 
#                               zoom=zoom, attribution_size=0) # Bottom Left info, can't remove for some reasons
                
#                 basemap_added = True
#                 print(f"  ✅ Successfully added satellite imagery")
#                 break
                
#             except Exception as e:
#                 print(f"  ❌ Provider {i+1} failed: {str(e)[:50]}...")
#                 ax.clear()  # Clear the plot for next attempt
#                 continue
        
#         if not basemap_added:
#             print("  ⚠️  All satellite providers failed. Creating styled map fallback...")
#             # Fallback: create a styled map without satellite imagery
#             gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
#                             edgecolor=edge_color, linewidth=line_width)
#             ax.set_facecolor('#f0f8e8')  # Light green background
#             ax.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.5)
        
#         # Customize the plot
#         # ax.set_title('Region Overview', fontsize=16, fontweight='bold', pad=20)
#         ax.set_axis_off()  # Remove axes for cleaner view
        
#         # Ensure tight layout
#         plt.tight_layout()
        
#         # Save the map
#         plt.savefig(output_path, dpi=300, bbox_inches='tight', 
#                    facecolor='none', edgecolor='none')
#         plt.close()
        
#         print(f"  ✅ Region map saved to: {output_path}")
#         return True
        
#     except Exception as e:
#         print(f"  ❌ Error generating satellite map: {e}")
#         return False

# def extract_coordinates_from_metrics(metrics_data):
    """
    Extract coordinates from your metrics_data object
    Modify this function based on your actual data structure
    """
    try:
        # Option 1: If coordinates are directly in metrics_data
        if hasattr(metrics_data, 'coordinates'):
            return metrics_data.coordinates
        
        # Option 2: If coordinates are in a nested structure
        if hasattr(metrics_data, 'region') and hasattr(metrics_data.region, 'coordinates'):
            return metrics_data.region.coordinates
        
        # Option 3: If it's a dictionary
        if isinstance(metrics_data, dict):
            if 'coordinates' in metrics_data:
                return metrics_data['coordinates']
            elif 'region' in metrics_data and 'coordinates' in metrics_data['region']:
                return metrics_data['region']['coordinates']
        
        # Option 4: Default example coordinates if none found
        print("  ⚠️  No coordinates found in metrics_data, using default region")
        return [
            [-74.0059, 40.7128],  # Default: New York area
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
            [-74.0059, 40.7128]
        ]
        
    except Exception as e:
        print(f"  ❌ Error extracting coordinates: {e}")
        # Return default coordinates as fallback
        return [
            [-74.0059, 40.7128],
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
            [-74.0059, 40.7128]
        ]