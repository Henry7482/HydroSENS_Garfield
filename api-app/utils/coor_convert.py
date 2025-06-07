
def lon_to_utm_zone(lon):
    return int((lon + 180) / 6) + 1

def build_utm_wkt(zone, is_northern):
    epsg_code = 32600 + zone if is_northern else 32700 + zone
    central_meridian = zone * 6 - 183
    return f'''PROJCS["WGS 84 / UTM zone {zone}{'N' if is_northern else 'S'}",
  GEOGCS["WGS 84",
    DATUM["WGS_1984",
      SPHEROID["WGS 84",6378137,298.257223563,
        AUTHORITY["EPSG","7030"]],
      AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]],
  PROJECTION["Transverse_Mercator"],
  PARAMETER["latitude_of_origin",0],
  PARAMETER["central_meridian",{central_meridian}],
  PARAMETER["scale_factor",0.9996],
  PARAMETER["false_easting",500000],
  PARAMETER["false_northing",{0 if is_northern else 10000000}],
  UNIT["metre",1,AUTHORITY["EPSG","9001"]],
  AUTHORITY["EPSG","{epsg_code}"]]'''
