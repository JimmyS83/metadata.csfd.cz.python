# coding: utf-8
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
CSFD_MOVIE_URL = BASE_URL.format('film/{}')
GALLERY_URL = 'https://www.csfd.cz/film/{}/galerie/'
THUMB_URL = 'https://image.pmgstatic.com/files/images/film/posters/{}'
THUMB_PREVIEW_URL = 'https://image.pmgstatic.com/cache/resized/w420/files/images/film/posters/{}'
FANART_URL = 'https://image.pmgstatic.com/files/images/film/photos/{}.jpg'
FANART_PREVIEW_URL = 'https://image.pmgstatic.com/cache/resized/w360/files/images/film/photos/{}.jpg'

SEARCH_URL = BASE_URL.format('hledat/')
SEARCH_RESULT_MOVIES_REGEX =  re.compile(r'<h2>Filmy(.*)<h2>Seri.ly', re.DOTALL)
SEARCH_RESULT_REGEX = re.compile(r'film-title-nooverflow">.*?<a href="/(film/[^"]*)" class="film-title-name">([^<]*)</a>.*?<span class="info">\(([0-9]*)\)')

CSFD_CZTITLE_REGEX = re.compile(r'<h1[^>]*>([^<]*)<')
CSFD_ORIGINALTITLE_REGEX = re.compile(r'class="flag".*?>([^<]*)<')
CSFD_PLOT_REGEX = re.compile(r'plot-full.*\s*<p>\s*(.*)')
CSFD_THUMB_REGEX = re.compile(r'image\.pmgstatic\.com.*posters/([^ ]*\.jpg)')
CSFD_RUNTIME_REGEX = re.compile(r', (\d*) min')
CSFD_DIRECTOR_REGEX = re.compile(r'<h4>Re.ie[^>]*>[^>]*>[^>]*>([^<]*)')
CSFD_RATING_REGEX = re.compile(r'<div class="rating-average rating-average-withtabs">[^0-9]*([0-9]*)%')
CSFD_VOTES_REGEX = re.compile(r'Hodnocen.<span class="counter">\(([^\)]*)\)')
CSFD_CAST1_REGEX = re.compile(r'<h4>Hraj.[^>]*>.*<span >(.*)</span>', re.DOTALL)
CSFD_CAST2_REGEX = re.compile(r'<a href="/tvurc[^>]*>([^<]*)</a>')
CSFD_CAST_LIMIT = 8
CSFD_YEAR_REGEX = re.compile(r'<span itemprop="dateCreated"[^>]*>([^<]*)<')
CSFD_GENRE_REGEX = re.compile(r'<div class="genres">([^<]*)')
CSFD_COUNTRY_REGEX = re.compile(r'<div class="origin">([^,]*),')
CSFD_GALLERYURL_REGEX = re.compile(r'\/film\/([^\/]*)\/galerie')
CSFD_FANART_REGEX = re.compile(r'srcset=.*\/photos\/([^ ]*).jpg')

TMDB_PARAMS = {'api_key': 'f090bb54758cabf231fb605d3e3e0468'}
TMDB_URL = 'https://api.themoviedb.org/3/{}'
TMDB_SEARCH_URL = TMDB_URL.format('search/movie')
TMDB_MOVIE_URL = TMDB_URL.format('movie/{}')
TMDB_IMAGE_PREVIEW = 'https://image.tmdb.org/t/p/w500{}'
TMDB_IMAGE_ORIGINAL = 'https://image.tmdb.org/t/p/original{}'

IMDB_MOVIE_URL = 'https://www.imdb.com/title/{}'

def get_tmdb_info(title, year=None, uniqueid=None):
    params = TMDB_PARAMS.copy()
    
    if uniqueid is not None: # direct lookup from .nfo
        #xbmc.log('\n direct URL from nfo {}{} to get TMDB fanart'.format(TMDB_MOVIE_URL.format(uniqueid), params), xbmc.LOGDEBUG)
        api_utils.set_headers(dict(HEADERS_TMDB))  # MAYBE NOT NEEDED
        response = api_utils.load_info(TMDB_MOVIE_URL.format(uniqueid), params=params)
        if 'error' in response:
            return False
        return {'poster': response['poster_path'], 'fanart': response['backdrop_path']}
    
    else: # query search
        params['query'] = title.encode('utf-8')
        if year is not None:
            params['year'] = str(year)
        
        #xbmc.log('\n using movie query query {}{} to get TMDB fanart'.format(TMDB_SEARCH_URL, params), xbmc.LOGDEBUG)
        api_utils.set_headers(dict(HEADERS_TMDB))  # MAYBE NOT NEEDED
        response = api_utils.load_info(TMDB_SEARCH_URL, params=params)

        if 'error' in response or response['total_results'] == 0:
            return False

        return {'poster': response['results'][0]['poster_path'], 'fanart': response['results'][0]['backdrop_path']}

def search_movie(query, year=None):
    #xbmc.log('using title: %s to find movie' % query, xbmc.LOGDEBUG)
    params = {}
    params['q'] = query
    if year is not None:
        params['q'] = "{0} {1}".format(params['q'], str(year))
    response = api_utils.load_info(SEARCH_URL, params=params, resp_type='text')
    response_movies = re.findall(SEARCH_RESULT_MOVIES_REGEX, response)
    result = re.findall(SEARCH_RESULT_REGEX, response_movies[0])
        
    result_fixed = []
    for row in result:
        result_fixed.append((BASE_URL.format(row[0]).decode('utf-8'), row[1], row[2]))
    
    return result_fixed


def get_movie(url, settings):
    #xbmc.log(' using movie from url %s to get movie details' % url, xbmc.LOGDEBUG)
    uniqueids = {'csfd' : None, 'tmdb' : None, 'imdb' : None}
    
    if type(url) is dict:  
        if 'csfd' in url: uniqueids['csfd'] = CSFD_MOVIE_URL.format(url['csfd'])
        if 'tmdb' in url: uniqueids['tmdb'] = url['tmdb']
        if 'imdb' in url: uniqueids['imdb'] = IMDB_MOVIE_URL.format(url['imdb'])
        
        if uniqueids['csfd'] is not None: url = uniqueids['csfd'] # direct lookup from .nfo, 

    response = api_utils.load_info(url, resp_type='text')
    info = {}
    
    match = CSFD_CZTITLE_REGEX.findall(response)
    if (match): info['title'] = match[0].strip()

    match = CSFD_ORIGINALTITLE_REGEX.findall(response)
    if (match): info['originaltitle'] = match[0].strip()
    else: info['originaltitle'] = info['title'] # fallback to czech title

    match = CSFD_PLOT_REGEX.findall(response)
    if (match): 
        plot = match[0].strip()
        info['plot'] = re.sub(r'<[^>]*>', '', plot, flags=re.MULTILINE)

    match = CSFD_RUNTIME_REGEX.findall(response)
    if (match): info['duration'] = int(match[0])*60
    
    match = CSFD_DIRECTOR_REGEX.findall(response)
    if (match): info['director'] = match[0].split(", ")
    
    match = CSFD_CAST1_REGEX.findall(response)
    if (match): 
        match = CSFD_CAST2_REGEX.findall(match[0].strip())
        info['cast'] = [] 
        for actor in match[:CSFD_CAST_LIMIT]:
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
    
    if settings.getSettingBool('tmdbfanart') or settings.getSettingBool('tmdbposter'): 
        tmdb_info = get_tmdb_info(info['originaltitle'], info['year'], uniqueids['tmdb'])
        
        if tmdb_info:
            if tmdb_info['poster'] is not None:
                poster = {'original' : TMDB_IMAGE_ORIGINAL.format(tmdb_info['poster']), 'preview' : TMDB_IMAGE_PREVIEW.format(tmdb_info['poster'])}
            if tmdb_info['fanart'] is not None:
                fanart = [{'original' : TMDB_IMAGE_ORIGINAL.format(tmdb_info['fanart']), 'preview' : TMDB_IMAGE_PREVIEW.format(tmdb_info['fanart'])}]

    if not settings.getSettingBool('tmdbposter') or not tmdb_info or tmdb_info['poster'] is None:  # TMDB poster OFF or fallback 
        match = CSFD_THUMB_REGEX.findall(response)
        if (match): poster = {'original' : THUMB_URL.format(match[0]), 'preview' : THUMB_PREVIEW_URL.format(match[0])}        
    
    if not settings.getSettingBool('tmdbfanart') or not tmdb_info or tmdb_info['fanart'] is None:  # TMDB fanart OFF or fallback
        fanart = []
        match = CSFD_GALLERYURL_REGEX.findall(response)
        if (match): gallery_url = GALLERY_URL.format(match[0])
        response = api_utils.load_info(gallery_url, resp_type='text')
        match = CSFD_FANART_REGEX.findall(response)
        if (match):
            match_fixed = [i for n, i in enumerate(match) if i not in match[:n]]  # remove duplicites
            for image in match_fixed:
                fanart_original = FANART_URL.format(image)
                fanart_preview = FANART_PREVIEW_URL.format(image)
                fanart.append({
                    'original': fanart_original,
                    'preview': fanart_preview
                }) 
    
    if rating: rating = {'rating': float(rating)/10, 'votes': int(votes.replace(u'\xa0', u''))}
    else : rating = {'rating': False, 'votes': int(votes.replace(u'\xa0', u''))}
    available_art = {'poster': poster, 'fanart': fanart}
    
    #xbmc.log('\n DETAILS :{}{}{}'.format(info, rating, available_art), xbmc.LOGDEBUG)
    return {'info': info, 'ratings': rating, 'available_art': available_art}
