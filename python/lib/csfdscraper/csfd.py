from . import api_utils
import xbmc
import re
try:
    from typing import Optional, Text, Dict, List, Any  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass


class CSFDMovieScraper(object):
    def __init__(self, url_settings):
        self.url_settings = url_settings

    def search(self, title, year=None):
        result = search_movie(query=title, year=year)
        return result

    def get_details(self, url):
        details = get_movie(url, self.url_settings)
        if not details:
            return None
        return details


HEADERS_CSFD = (
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20120101 Firefox/33.0'),
)
HEADERS_TMDB = (
    ('User-Agent', 'Kodi Movie scraper by Team Kodi'),
    ('Accept', 'application/json'),
)
api_utils.set_headers(dict(HEADERS_CSFD))

BASE_URL = 'https://www.csfd.cz/{}'
GALLERY_URL = 'https://www.csfd.cz/film/{}/galerie/'
THUMB_URL = 'https://image.pmgstatic.com/files/images/film/posters/{}'
THUMB_PREVIEW_URL = 'https://image.pmgstatic.com/cache/resized/w420/files/images/film/posters/{}'
FANART_URL = 'https://image.pmgstatic.com/files/images/film/photos/{}.jpg'
FANART_PREVIEW_URL = 'https://image.pmgstatic.com/cache/resized/w360/files/images/film/photos/{}.jpg'

SEARCH_URL = BASE_URL.format('hledat/')
SEARCH_RESULT_REGEX = re.compile(r'film-title-nooverflow">.*?<a href="/(film/[^"]*)" class="film-title-name">([^<]*)</a>.*?<span class="info">\(([0-9]*)\)')

CSFD_CZTITLE_REGEX = re.compile(r'<h1[^>]*>([^<]*)<')
CSFD_ORIGINALTITLE_REGEX = re.compile(r'class="flag".*?>([^<]*)<')
CSFD_PLOT_REGEX = re.compile(r'body--plots">[^>]*>[^<]*<p>([^<]*)')
CSFD_THUMB_REGEX = re.compile(r'image\.pmgstatic\.com.*posters/([^ ]*)')
CSFD_RUNTIME_REGEX = re.compile(r', (\d*) min')
CSFD_DIRECTOR_REGEX = re.compile(r'<h4>Re.ie[^>]*>[^>]*>[^>]*>([^<]*)')
CSFD_RATING_REGEX = re.compile(r'<div class="rating-average rating-average-withtabs">[^0-9]*([0-9]*)%')
CSFD_VOTES_REGEX = re.compile(r'Hodnocen.<span class="counter">\(([^\)]*)\)')
CSFD_CAST1_REGEX = re.compile(r'<h4>Hraj.[^>]*>[^>]*>(.*)<span class="more-member-1', re.DOTALL)
CSFD_CAST2_REGEX = re.compile(r'<a href=".[^>]*>([^<]*)</a>')
CSFD_YEAR_REGEX = re.compile(r'<span itemprop="dateCreated"[^>]*>([^<]*)<')
CSFD_GENRE_REGEX = re.compile(r'<div class="genres">([^<]*)')
CSFD_COUNTRY_REGEX = re.compile(r'<div class="origin">([^,]*),')
CSFD_GALLERYURL_REGEX = re.compile(r'\/film\/([^\/]*)\/galerie')
CSFD_FANART_REGEX = re.compile(r'srcset=.*\/photos\/([^ ]*).jpg')

TMDB_PARAMS = {'api_key': 'f090bb54758cabf231fb605d3e3e0468'}
TMDB_URL = 'https://api.themoviedb.org/3/{}'
TMDB_SEARCH_URL = TMDB_URL.format('search/movie')
TMDB_MOVIE_URL = TMDB_URL.format('movie/{}')
THUMB_FANART_PREVIEW = 'https://image.tmdb.org/t/p/w500/{}'
THUMB_FANART_ORIGINAL = 'https://image.tmdb.org/t/p/original/{}'

def get_tmdb_fanart(title, year=None):
        
    params = TMDB_PARAMS.copy()
    params['query'] = title.encode('utf-8')
    if year is not None:
        params['year'] = str(year)
    
    #xbmc.log('\n\nusing movie query query {}{} to get TMDB fanart'.format(TMDB_SEARCH_URL, params), xbmc.LOGDEBUG)
    
    api_utils.set_headers(dict(HEADERS_TMDB))  # MAYBE NOT NEEDED
    response = api_utils.load_info(TMDB_SEARCH_URL, params=params)

    if 'error' in response or response['results'][0]['backdrop_path'] is None:
        return False
    
    fanart = [{
            'original': THUMB_FANART_ORIGINAL.format(response['results'][0]['backdrop_path']),
            'preview': THUMB_FANART_PREVIEW.format(response['results'][0]['backdrop_path'])
    }]

    return fanart

def search_movie(query, year=None):
    #xbmc.log('using title: %s to find movie' % query, xbmc.LOGDEBUG)
    params = {}
    params['q'] = query
    if year is not None:
        params['q'] = "{0} {1}".format(params['q'], str(year))
    response = api_utils.load_info(SEARCH_URL, params=params, resp_type='text')
    result = re.findall(SEARCH_RESULT_REGEX, response)
    
    result_fixed = []
    for row in result:
        result_fixed.append((BASE_URL.format(row[0]).decode('utf-8'), row[1], row[2]))
    
    return result_fixed


def get_movie(url, settings):
    #xbmc.log(' using movie from url %s to get movie details' % url, xbmc.LOGDEBUG)
    response = api_utils.load_info(url, resp_type='text')
    info = {}
    
    match = CSFD_CZTITLE_REGEX.findall(response)
    if (match): info['title'] = match[0].strip()

    match = CSFD_ORIGINALTITLE_REGEX.findall(response)
    if (match): info['originaltitle'] = match[0].strip()

    match = CSFD_PLOT_REGEX.findall(response)
    if (match): info['plot'] = match[0].strip()

    match = CSFD_THUMB_REGEX.findall(response)
    if (match):
        poster_original = THUMB_URL.format(match[0])
        poster_preview = THUMB_PREVIEW_URL.format(match[0])        
    
    match = CSFD_RUNTIME_REGEX.findall(response)
    if (match): info['duration'] = int(match[0])*60
    
    match = CSFD_DIRECTOR_REGEX.findall(response)
    if (match): info['director'] = match[0].split(", ")
    
    match = CSFD_CAST1_REGEX.findall(response)
    if (match): 
        match = CSFD_CAST2_REGEX.findall(match[0].strip())
        info['cast'] = [] 
        for actor in match:
            info['cast'].append(actor)
    
    match = CSFD_RATING_REGEX.findall(response)
    if (match): rating = match[0]
    
    match = CSFD_VOTES_REGEX.findall(response)
    if (match): votes = match[0]
    
    match = CSFD_YEAR_REGEX.findall(response)
    if (match): info['year'] = int(match[0])
    
    match = CSFD_GENRE_REGEX.findall(response)
    if (match): info['genre'] = match[0].split(" / ")
    
    match = CSFD_COUNTRY_REGEX.findall(response)
    if (match): info['country'] = match[0].split(" / ")
    
    if settings.getSettingBool('tmdbfanart'): 
        fanart = get_tmdb_fanart(info['title'], info['year'])
    
    
    if not settings.getSettingBool('tmdbfanart') or not fanart: 
        match = CSFD_GALLERYURL_REGEX.findall(response)
        if (match): gallery_url = GALLERY_URL.format(match[0])
        response = api_utils.load_info(gallery_url, resp_type='text')
        match = CSFD_FANART_REGEX.findall(response)
        if (match):
            match_fixed = [i for n, i in enumerate(match) if i not in match[:n]]  # remove duplicites
            fanart = [] 
            for image in match_fixed:
                fanart_original = FANART_URL.format(image)
                fanart_preview = FANART_PREVIEW_URL.format(image)
                fanart.append({
                    'original': fanart_original,
                    'preview': fanart_preview
                }) 
    
    rating = {'rating': float(rating)/10, 'votes': int(votes.replace(u'\xa0', u''))}
    available_art = {'poster': {'original' : poster_original, 'preview' : poster_preview}, 'fanart': fanart}
    
    return {'info': info, 'ratings': rating, 'available_art': available_art}

