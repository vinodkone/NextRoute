import string
import urllib

from difflib import SequenceMatcher
from elementtree.ElementTree import parse
from geo import Geo

class NextBus(object):

  BASE_URL = 'http://webservices.nextbus.com/service/publicXMLFeed'

  def __init__(self, agency='sf-muni'):
    self.agency = agency
    self.routes = {}
    self.routes_config = {}

  # TODO(vinod): Do some caching here
  def get_data(self, command, **kwargs):
    xml = None

    params = {'command' : command, 'a' : self.agency}
    params.update(**kwargs)
    params = urllib.urlencode(params)

    url = "%s?%s" % (NextBus.BASE_URL, params)
    print url

    try:
      xml = parse(urllib.urlopen(url))
    except Exception as e:
      print 'Error reading url: %s Error: %s' % (url, e)

    return xml

  def get_route_list(self):
    if not self.routes:
      xml = self.get_data('routeList')
      for element in xml.findall('route'):
        self.routes[element.get('tag')] = element.get('title')

    #pprint(self.routes)

  def get_route_config(self, route):
    if not self.routes_config.get(route):
      xml = self.get_data('routeConfig', r=route)

      for element in xml.findall('route'):
        self.routes_config[element.get('tag')] = []
        for subelement in element.findall('stop'):
          self.routes_config[element.get('tag')].append(subelement.attrib)

    #pprint(self.routes_config)

  def get_arrival_time(self, route, point):
    print 'Retrieving arrival time for route: %s point: %s' % (route, point)

    self.get_route_config(route)

    if not self.routes_config.get(route):
      return "'Route %s doesn't exist" % route

    stops = self.routes_config[route]
    points = [(float(stop['lat']), float(stop['lon'])) for stop in stops]

    #closest_stops = Geo.get_neighbors(point, points, 0.1) # within  half a mile
    closest_stop = Geo.closest_point(point, points)

    stop = stops[closest_stop[1]]

    print 'Closest stop for %s is %s' % (point, stop['title'])
    result = self._format(self.get_stop_arrival_time(route, stop['tag']))
    return result

  def get_arrival_time_xstreet(self, route, cross_street):
    print 'Retrieving arrival time for route: %s xstreet: %s' % (route, cross_street)

    self.get_route_config(route)

    if not self.routes_config.get(route):
      return "'Route %s doesn't exist" % route

    stops = self.routes_config[route]

    xstreets = [string.lower(stop['title']) for stop in stops]
    xstreets_r = []
    for xstreet in xstreets:
      xstreet = xstreet.split(' & ')
      xstreet.reverse()
      xstreets_r.append(' & '.join(xstreet)) # also search by flipping xstreet names

    xstreets.extend(xstreets_r)

    cross_street = string.lower(cross_street)

    s = SequenceMatcher(lambda x: x in ['and', '&', ' ', 'st', 'street']) # ignore these
    s.set_seq2(cross_street)

    max_ratio = 0
    index = -1

    for i in xrange(len(xstreets)):
      xstreet = xstreets[i]
      s.set_seq1(xstreet)
      ratio = s.ratio()

      if ratio > max_ratio:
        max_ratio = ratio
        index = i

    stop = stops[index % (len(xstreets) / 2)]

    print 'Closest stop for %s is stop:%s' % (cross_street, stop['title'])
    return self.get_stop_arrival_time(route, stop['tag'])

  def get_stop_arrival_time(self, route, stop):
    xml = self.get_data('predictions', r=route, s=stop)

    results = []
    for element in xml.findall('predictions'):
      result = '(Stop: %s)\n' % element.get('stopTitle')
      for subelement in element.findall('direction'):
        result += '%s:' % subelement.get('title')
        for subsubelement in subelement.findall('prediction'):
          result += '%s,' % (subsubelement.get('minutes'))
        result = result.rstrip(',')
        result += " min"
        results.append(result)
        result = ''

    results = self._format(';'.join(results))
    print results + " len: %d" % len(results)
    return results

  def _format_direction(self, dirname):
    return dirname.replace("Outbound to", "Out to").replace("Inbound to", "In to")

  def _format_xstreet(self, crosstreet):
    return crosstreet.replace(" St", "")

  def _format(self, text):
    return self._format_xstreet(self._format_direction(text))

if __name__ == '__main__':
  api = NextBus()
  api.get_route_list()
  api.get_route_config('30')

  api.get_arrival_time('30', [37.80161, -122.4294999])
  api.get_arrival_time('28', [37.803648610000003, -122.43538632000001])

  api.get_arrival_time_xstreet('30', '3rd and folsom')
