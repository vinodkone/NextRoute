from math import radians, sin, cos, asin, sqrt

class Geo(object):

  EARTH_RADIUS_MILES = 3956.0

  @staticmethod
  def haversine_distance(point1, point2):
    """
    Calculates the geographical distance (in miles) between two points
    point1 and point2 are tuples of (lat, lon) where lat and lon 
    are specified in degrees.
    """
    lat1, lon1 = (radians(coord) for coord in point1)
    lat2, lon2 = (radians(coord) for coord in point2)
    dlat, dlon = (lat2 - lat1, lon2 - lon1)
    a = sin(dlat / 2.0) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2.0) ** 2
    great_circle_distance = 2 * asin(min(1, sqrt(a)))
    d = Geo.EARTH_RADIUS_MILES * great_circle_distance
    return d

  @staticmethod
  def closest_point(point, points):
    """Calculates the closest point from a given array of points"""
    min_distance = None
    closest_point = None
    index = -1

    for i in xrange(len(points)):
      p = points[i]
      distance = Geo.haversine_distance(p, point)

      if (min_distance is None) or distance < min_distance:
        min_distance = distance
        closest_point = p
        index = i

    return (closest_point, index)

  @staticmethod
  def get_neighbors(point, points, distance):
    """
    Returns a list of (index,distance) of all those points that are 
    within a given distance (in miles) from the point
    """
    neighbors = [];

    for i in xrange(len(points)):
      dist = Geo.haversine_distance(point, points[i])

      if dist <= distance:
        neighbors.append((i, dist))

    return neighbors

if __name__ == '__main__':
  x = (37.160316546736745, -78.75)
  y = (39.095962936305476, -121.2890625)

  for i in range(100):
    Geo.haversine_distance(x, y)

  print Geo.closest_point(x, [y, x , y])
