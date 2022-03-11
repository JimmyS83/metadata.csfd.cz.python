# coding: utf-8
import json
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
CSFD_GALLERY_URL = CSFD_MOVIE_URL.format('{}/galerie/')
CSFD_COMMENTS_URL = CSFD_MOVIE_URL.format('{}/recenze/')
THUMB_URL = 'https://image.pmgstatic.com/files/images/film/posters/{}'
THUMB_PREVIEW_URL = 'https://image.pmgstatic.com/cache/resized/w420/files/images/film/posters/{}'
FANART_URL = 'https://image.pmgstatic.com/files/images/film/photos/{}'
FANART_PREVIEW_URL = 'https://image.pmgstatic.com/cache/resized/w360/files/images/film/photos/{}'

SEARCH_URL = BASE_URL.format('hledat/')
SEARCH_RESULT_MOVIES_REGEX =  re.compile(r'<h2>Filmy(.*)<h2>Seri.ly', re.DOTALL)
SEARCH_RESULT_REGEX = re.compile(r'film-title-nooverflow">.*?<a href="/(film/[^"]*)" class="film-title-name">([^<]*)</a>.*?<span class="info">\(([0-9]*)\)')

CSFD_CZTITLE_REGEX = re.compile(r'<h1[^>]*>([^<]*)<')
CSFD_ORIGINALTITLE_REGEX = re.compile(r'class="flag".*?>([^<]*)(.*)<')
CSFD_PLOT_REGEX = re.compile(r'plot-full.*\s*<p>\s*(.*)')
CSFD_THUMB_REGEX = re.compile(r'image\.pmgstatic\.com.*posters/([^ ]*\....)')
CSFD_RUNTIME_REGEX = re.compile(r'>(\d*) min')
CSFD_DIRECTOR_REGEX = re.compile(r'<h4>Re.ie[^>]*>[^>]*>([^<]*)')
CSFD_RATING_REGEX = re.compile(r'<div class=\"film-rating-average[^>]*>[^0-9]*([0-9]*)%')
CSFD_VOTES_REGEX = re.compile(r'Hodnocen.<span class="counter">\(([^\)]*)\)')
CSFD_CAST1_REGEX = re.compile(r'<h4>Hraj.: </h4>(.*)</span>', re.DOTALL)
CSFD_CAST2_REGEX = re.compile(r'<a href="/tvurc[^>]*>([^<]*)</a>')
CSFD_CAST_LIMIT = 8
CSFD_YEAR_REGEX = re.compile(r'"dateCreated":"(\d*)')
CSFD_GENRE_REGEX = re.compile(r'<div class="genres">([^<]*)')
CSFD_COUNTRY_REGEX = re.compile(r'<div class="origin">([^,]*),')
CSFD_TITLE_URL_REGEX = re.compile(r'\/film\/([^\/]*)\/galerie')
CSFD_FANART_REGEX = re.compile(r'srcset=.*\/photos\/([^ ]*\....)')
#CSFD_COMMENT_REGEX = re.compile(r'icon-permalink[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>\s*([^<]*)', re.DOTALL)
#CSFD_COMMENT_REGEX = re.compile(r'class=\"user-title-name\">([^<]*)[^>]*>[^>]*>[^>]*><span class=\"stars stars-(\d)\">[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>[^>]*>\s*([^<]*)', re.DOTALL)
CSFD_COMMENT_REGEX = re.compile(r'class=\"user-title-name\">(.*?)</a>.*?<span class=\"stars stars-(\d)\">.*?<p>(.*?)<span class=', re.DOTALL)

TMDB_PARAMS = {'api_key': 'f090bb54758cabf231fb605d3e3e0468'}
TMDB_URL = 'https://api.themoviedb.org/3/{}'
TMDB_SEARCH_URL = TMDB_URL.format('search/movie')
TMDB_MOVIE_URL = TMDB_URL.format('movie/{}')
TMDB_IMAGE_PREVIEW = 'https://image.tmdb.org/t/p/w500{}'
TMDB_IMAGE_ORIGINAL = 'https://image.tmdb.org/t/p/original{}'

IMDB_URL = 'https://www.imdb.com/{}'
IMDB_SEARCH_URL = IMDB_URL.format('find')
IMDB_SEARCH_RESULT_MOVIES_REGEX =  re.compile(r'<table class=\"findList\">.*</table>', re.DOTALL)
IMDB_SEARCH_RESULT_REGEX = re.compile(r'title/(tt[0-9]+)')
IMDB_MOVIE_URL = IMDB_URL.format('title/{}')
IMDB_LDJSON_REGEX = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
IMDB_RATING_REGEX = re.compile(r'AggregateRating\".*?ratingValue\":(.*?)}')
IMDB_VOTES_REGEX = re.compile(r'AggregateRating\".*?ratingCount\":(.*?),')

HTML_STRIP = re.compile('<.*?>')

def html_strip(input):
    replaces = ( ('&amp;', '&'), )
    for pattern, repl in replaces:
        input = re.sub(pattern, repl, input)
    input = re.sub(HTML_STRIP, '', input)
    return input
    
def get_imdb_info(title, year=None, uniqueid=None):
    #xbmc.log('\n IMDB info req. {} {} {}'.format(title, year, uniqueid), xbmc.LOGDEBUG)
    if uniqueid is not None: # direct lookup from .nfo
        response_movie = api_utils.load_info(uniqueid, resp_type='text')
    
    else:  # Search for movie fulltext
        params = {}
        params['q'] = title
        if year is not None:
            params['q'] = "{0} {1}".format(params['q'], str(year))

        response = api_utils.load_info(IMDB_SEARCH_URL, params=params, resp_type='text')
        #xbmc.log('\n IMDB search response {}.'.format(response.encode('utf-8')), xbmc.LOGDEBUG)
        response_movies = re.findall(IMDB_SEARCH_RESULT_MOVIES_REGEX, response)
        imdbid = re.findall(IMDB_SEARCH_RESULT_REGEX, response_movies[0])[0]
        imdb_movie = IMDB_MOVIE_URL.format(imdbid)
        #xbmc.log('\n IMDB founded movie {}.'.format(imdb_movie), xbmc.LOGDEBUG)
        response_movie = api_utils.load_info(imdb_movie, resp_type='text')

    match = re.search(IMDB_LDJSON_REGEX, response_movie)
    if not match:
        return {'rating': None, 'votes': None}
        
    try:
        ldjson = json.loads(match.group(1).replace('\n', ''))
    except json.decoder.JSONDecodeError:
        return {'rating': None, 'votes': None}

    try:
        aggregateRating = ldjson.get('aggregateRating', {})
        return {'rating': aggregateRating.get('ratingValue'), 'votes': aggregateRating.get('ratingCount')}
    except AttributeError:
        return {'rating': None, 'votes': None}

def get_tmdb_info(title, year=None, uniqueid=None, settings=None):
    params = TMDB_PARAMS.copy()
    
    if uniqueid is not None: # direct lookup from .nfo
        #xbmc.log('\n direct URL from nfo {}{} to get TMDB fanart'.format(TMDB_MOVIE_URL.format(uniqueid), params), xbmc.LOGDEBUG)
        api_utils.set_headers(dict(HEADERS_TMDB))  # MAYBE NOT NEEDED
        params['language'] = 'cs'
        response = api_utils.load_info(TMDB_MOVIE_URL.format(uniqueid), params=params)
        if 'error' in response:
            return False

        if not response['overview'] and settings.getSettingBool('tmdbenplot'):  # fallback to TMDB eng plot
            params['language'] = None
            
            response_eng = api_utils.load_info(TMDB_MOVIE_URL.format(uniqueid), params=params)
            if response_eng['overview']:
                response['overview'] = response_eng['overview']

            if 'error' in response:
                return False
        
        return {'poster': response['poster_path'], 'fanart': response['backdrop_path'], 'rating': response['vote_average'],'votes': response['vote_count'], 'plot': response['overview']}
    
    else: # query search
        params['query'] = title
        if year is not None:
            params['year'] = str(year)
        
        #xbmc.log('\n using movie query query {}{} to get TMDB fanart'.format(TMDB_SEARCH_URL, params), xbmc.LOGDEBUG)
        
        params['language'] = 'cs'
        api_utils.set_headers(dict(HEADERS_TMDB))  # MAYBE NOT NEEDED
        response = api_utils.load_info(TMDB_SEARCH_URL, params=params)
        #xbmc.log('\n TMDB returns movie details {}'.format(response), xbmc.LOGDEBUG)

        if 'error' in response or response['total_results'] == 0:
            return False
        
        if not response['results'][0]['overview'] and settings.getSettingBool('tmdbenplot'):  # fallback to TMDB eng plot
            params['language'] = None
            
            response_eng = api_utils.load_info(TMDB_SEARCH_URL, params=params)
            if response_eng['results'][0]['overview']:
                response['results'][0]['overview'] = response_eng['results'][0]['overview']

            if 'error' in response or response['total_results'] == 0:
                return False

        return {'poster': response['results'][0]['poster_path'], 'fanart': response['results'][0]['backdrop_path'], 'rating': response['results'][0]['vote_average'],'votes': response['results'][0]['vote_count'], 'plot': response['results'][0]['overview']}

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
        result_fixed.append((BASE_URL.format(row[0]), row[1], row[2]))
    
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
    plotoutline=[]
    
    match = CSFD_CZTITLE_REGEX.findall(response)
    if (match): 
        info['title'] = match[0].strip()
        info['title'] = html_strip(info['title'])
    else: xbmc.log('Nemame CSFD Title', xbmc.LOGWARNING)

    match = CSFD_ORIGINALTITLE_REGEX.findall(response)
    if (match):
        for x in match:
            if not re.search(r'pracovn', x[1]): 
                info['originaltitle'] = x[0].strip()
                break
    else: info['originaltitle'] = info['title'] # fallback to czech title
    try:
        if info['originaltitle'] == '': info['originaltitle'] = info['title'] # fallback when scrapper returns empty string
        info['originaltitle'] = html_strip(info['originaltitle'])
    except KeyError:
        info['originaltitle'] = info['title'] # fallback when scrapper returns empty string  

    match = CSFD_PLOT_REGEX.findall(response)
    if (match): 
        plot = match[0].strip()
        info['plot'] = re.sub(r'<[^>]*>', '', plot, flags=re.MULTILINE)
    else: xbmc.log('Nemame CSFD Plot', xbmc.LOGWARNING)

    match = CSFD_RUNTIME_REGEX.findall(response)
    if (match): info['duration'] = int(match[0])*60
    else: xbmc.log('Nemame CSFD Runtime', xbmc.LOGWARNING)
    
    match = CSFD_DIRECTOR_REGEX.findall(response)
    if (match): info['director'] = match[0].split(", ")
    else: xbmc.log('Nemame CSFD Director', xbmc.LOGWARNING)
    
    match = CSFD_CAST1_REGEX.findall(response)
    if (match): 
        match = CSFD_CAST2_REGEX.findall(match[0].strip())
        info['cast'] = [] 
        for actor in match[:CSFD_CAST_LIMIT]:
            info['cast'].append(actor)
    else: xbmc.log('Nemame CSFD Cast', xbmc.LOGWARNING)
    
    match = CSFD_RATING_REGEX.findall(response)
    if (match): rating = match[0]
    else: xbmc.log('Nemame CSFD Rating', xbmc.LOGWARNING)
    
    match = CSFD_VOTES_REGEX.findall(response)
    if (match): votes = match[0]
    else: xbmc.log('Nemame CSFD Votes', xbmc.LOGWARNING)
    
    match = CSFD_YEAR_REGEX.findall(response)
    if (match): info['year'] = int(match[0])
    else: xbmc.log('Nemame CSFD Rok', xbmc.LOGWARNING)
    
    match = CSFD_GENRE_REGEX.findall(response)
    if (match): info['genre'] = match[0].split(" / ")
    else: xbmc.log('Nemame CSFD Genre', xbmc.LOGWARNING)
    
    match = CSFD_COUNTRY_REGEX.findall(response)
    if (match): info['country'] = match[0].split(" / ")
    else: xbmc.log('Nemame CSFD Country', xbmc.LOGWARNING)
    
    if settings.getSettingBool('csfdlongcomments') and settings.getSettingBool('csfdcomments'):
        match = CSFD_TITLE_URL_REGEX.findall(response)
        if (match): 
            comments_url = CSFD_COMMENTS_URL.format(match[0])
            response_comments = api_utils.load_info(comments_url, resp_type='text')
            match = CSFD_COMMENT_REGEX.findall(response_comments)
    else: match = CSFD_COMMENT_REGEX.findall(response)
    if (match):
        for comment in match:
            plotoutline.append('{0} ({1}/5): {2}{3}'.format(comment[0],comment[1],html_strip(comment[2].strip()), '\n-----\n'))
        if settings.getSettingBool('csfdcomments'): info['plotoutline'] = ''.join(plotoutline)
    else: xbmc.log('Nemame CSFD Comments', xbmc.LOGWARNING)
    
    if settings.getSettingBool('tmdbfanart') or settings.getSettingBool('tmdbposter') or settings.getSettingString('rating')=='TMDB' or 'plot' not in info: 
        tmdb_info = get_tmdb_info(info['originaltitle'], info['year'], uniqueids['tmdb'], settings)
        #xbmc.log(' TMDB RESPONSE {}'.format(tmdb_info) , xbmc.LOGDEBUG)
        
        if tmdb_info:
            if tmdb_info['poster'] is not None:
                poster = {'original' : TMDB_IMAGE_ORIGINAL.format(tmdb_info['poster']), 'preview' : TMDB_IMAGE_PREVIEW.format(tmdb_info['poster'])}
            if tmdb_info['fanart'] is not None:
                fanart = [{'original' : TMDB_IMAGE_ORIGINAL.format(tmdb_info['fanart']), 'preview' : TMDB_IMAGE_PREVIEW.format(tmdb_info['fanart'])}]
            if tmdb_info['plot'] and 'plot' not in info:
                info['plot'] = tmdb_info['plot']
                
        if 'plot' not in info and plotoutline:   #fallback to first CSFD comment instead plot
            info['plot'] = '{0}\n{1}'.format(u'KOMENTÁŘ NA ČSFD:', plotoutline[0])

    if not settings.getSettingBool('tmdbposter') or not tmdb_info or tmdb_info['poster'] is None:  # TMDB poster OFF or fallback 
        match = CSFD_THUMB_REGEX.findall(response)
        poster = {'original' : '', 'preview' : ''}
        if (match): poster = {'original' : THUMB_URL.format(match[0]), 'preview' : THUMB_PREVIEW_URL.format(match[0])}        
    
    if not settings.getSettingBool('tmdbfanart') or not tmdb_info or tmdb_info['fanart'] is None:  # TMDB fanart OFF or fallback
        fanart = []
        match = CSFD_TITLE_URL_REGEX.findall(response)
        if (match): 
            gallery_url = CSFD_GALLERY_URL.format(match[0])
            response_gallery = api_utils.load_info(gallery_url, resp_type='text')
            match = CSFD_FANART_REGEX.findall(response_gallery)
            if (match):
                match_fixed = [i for n, i in enumerate(match) if i not in match[:n]]  # remove duplicites
                for image in match_fixed:
                    fanart_original = FANART_URL.format(image)
                    fanart_preview = FANART_PREVIEW_URL.format(image)
                    fanart.append({
                        'original': fanart_original,
                        'preview': fanart_preview
                    }) 
    
    if rating: 
        rating = {'rating': float(rating)/10, 'votes': int(votes.replace(u'\xa0', u''))}
    else : rating = {'rating': False, 'votes': int(votes.replace(u'\xa0', u''))}
    
    if settings.getSettingString('rating')=='TMDB' and tmdb_info and tmdb_info['rating'] is not None:
            rating = {'rating': float(tmdb_info['rating']), 'votes': int(tmdb_info['votes'])}
    elif settings.getSettingString('rating')=='IMDB':    
        imdb_info = get_imdb_info(info['originaltitle'], info['year'], uniqueids['imdb'])
        if imdb_info and imdb_info['rating'] is not None:
            rating = {'rating': float(imdb_info['rating']), 'votes': int(imdb_info['votes'])}
    
    available_art = {'poster': poster, 'fanart': fanart}
    
    #xbmc.log('\n DETAILS :{}{}{}'.format(info, rating, available_art), xbmc.LOGDEBUG)
    return {'info': info, 'ratings': rating, 'available_art': available_art}
