# base url for scrapying website FurAffinity
BASE_URL = 'https://www.furaffinity.net'

# all sub-url recognized by scraper
# default URL_TYPES
# URL_TYPES = ['view', 'gallery', 'favorites', 'user']
URL_TYPES = ['view', 'msg', 'msg/submissions', 'watchlist', 'gallery', 'scraps']

# categories that are scrapied by scaper
SCRAPIED_CATEGORIES = set(['Artwork (Digital)', 'All', 'Cellshading'])

# keywords to check for when downloading a description
# case is ignored..
DESCRIPTION_KEYWORDS = ['story', 'chapter', 'music', 'flash', 'animation']