import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Polygon
import warnings
import os

warnings.filterwarnings('ignore')

def generate_region_satellite_map(coordinates, output_path="assets/images/region_screenshot.png", 
                                 figsize=(12, 10), alpha=0.6, 
                                 edge_color='none', face_color='none',
                                 line_width=3, zoom='auto'):
    """
    Generate satellite map from coordinates and save to specified path
    
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
        Zoom level ('auto' for automatic, or integer 1-19)
    
    Returns:
    --------
    bool : True if successful, False otherwise
    """
    
    try:
        print(f"Generating satellite map for region...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert coordinates to numpy array and ensure polygon is closed
        coords = np.array(coordinates)
        if not np.array_equal(coords[0], coords[-1]):
            coords = np.vstack([coords, coords[0]])  # Close the polygon
        
        # Create a polygon from coordinates
        polygon = Polygon(coords)
        
        # Create GeoDataFrame with WGS84 coordinates
        gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
        
        # Reproject to Web Mercator (EPSG:3857) for contextily compatibility
        gdf_mercator = gdf.to_crs(epsg=3857)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Define satellite imagery providers with fallbacks
        providers_to_try = [
            ctx.providers.Esri.WorldImagery,
            ctx.providers.CartoDB.Voyager,
            ctx.providers.OpenStreetMap.Mapnik
        ]
        
        # Try each provider until one works
        basemap_added = False
        for i, tile_provider in enumerate(providers_to_try):
            try:
                print(f"  Trying satellite provider {i+1}...")
                
                # Plot the polygon first
                gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
                                edgecolor=edge_color, linewidth=line_width)
                
                # Add satellite basemap
                ctx.add_basemap(ax, crs=gdf_mercator.crs, source=tile_provider, 
                              zoom=zoom, attribution_size=0) # Bottom Left info, can't remove for some reasons
                
                basemap_added = True
                print(f"  ✅ Successfully added satellite imagery")
                break
                
            except Exception as e:
                print(f"  ❌ Provider {i+1} failed: {str(e)[:50]}...")
                ax.clear()  # Clear the plot for next attempt
                continue
        
        if not basemap_added:
            print("  ⚠️  All satellite providers failed. Creating styled map fallback...")
            # Fallback: create a styled map without satellite imagery
            gdf_mercator.plot(ax=ax, alpha=alpha, color=face_color, 
                            edgecolor=edge_color, linewidth=line_width)
            ax.set_facecolor('#f0f8e8')  # Light green background
            ax.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.5)
        
        # Customize the plot
        # ax.set_title('Region Overview', fontsize=16, fontweight='bold', pad=20)
        ax.set_axis_off()  # Remove axes for cleaner view
        
        # Ensure tight layout
        plt.tight_layout()
        
        # Save the map
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='none', edgecolor='none')
        plt.close()
        
        print(f"  ✅ Region map saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error generating satellite map: {e}")
        return False

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