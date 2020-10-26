import math

wgs84_a = 6378137.0     # Semi-major axis
wgs84_b = 6356752.3142451793    # Semi-minor axis
wgs84_e2 = 0.0066943799901975848  # First eccentricity squared
wgs84_a2 = wgs84_a ** 2
wgs84_b2 = wgs84_b ** 2
radians_per_degree = math.pi / 180.0
degree_per_radians = 180.0 / math.pi


def LLH2ECEF(lon, lat, alt):
    lat *= radians_per_degree
    lon *= radians_per_degree

    def n(x):
        return wgs84_a / (math.sqrt(1 - wgs84_e2 * (math.sin(x) ** 2)))

    x = (n(lat) + alt) * math.cos(lat) * math.cos(lon)
    y = (n(lat) + alt) * math.cos(lat) * math.sin(lon)
    z = (n(lat) * (1 - wgs84_e2) + alt) * math.sin(lat)

    return [x, y, z]


def ECEF2LLH(x, y, z):
    ep = math.sqrt((wgs84_a2 - wgs84_b2) / wgs84_b2)
    p = math.sqrt(x ** 2 + y ** 2)
    th = math.atan2(wgs84_a * z, wgs84_b * p)
    lon = math.atan2(y, x)
    lat = math.atan2(
        z + ep ** 2 * wgs84_b * math.sin(th) ** 3,
        p - wgs84_e2 * wgs84_a * math.cos(th) ** 3
    )
    N = wgs84_a / math.sqrt(1 - wgs84_e2 * math.sin(lat) ** 2)
    alt = p / math.cos(lat) - N

    lon *= degree_per_radians
    lat *= degree_per_radians

    return [lon, lat, alt]

# x =   4.2010e+06
# y =   1.7246e+05
# z =   4.7801e+06
# ECEF2LLH(x, y, z)
#
# lat = 48.8567
# lon = 2.3508
# h = 80
# LLH2ECEF(lon,lat,h)


