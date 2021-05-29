# coding: utf-8
import json
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from lib.csfdscraper.csfd import CSFDMovieScraper
from scraper_datahelper import get_params
from scraper_config import PathSpecificSettings, configure_csfd_artwork

ADDON_SETTINGS = xbmcaddon.Addon()
ID = ADDON_SETTINGS.getAddonInfo('id')

def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log(msg='[{addon}]: {msg}'.format(addon=ID, msg=msg), level=level)

def get_csfd_scraper(settings):
    return CSFDMovieScraper(ADDON_SETTINGS)

def search_for_movie(title, year, handle, settings):
    #log("Find movie with title '{title}' from year '{year}'".format(title=title, year=year), xbmc.LOGINFO)
    title = _strip_trailing_article(title)
    search_results = get_csfd_scraper(settings).search(title, year)
    if not search_results:
        return

    for movie in search_results:
        listitem = _searchresult_to_listitem(movie)
        xbmcplugin.addDirectoryItem(handle=handle, url=build_lookup_string(movie[0]), listitem=listitem, isFolder=True)

_articles = [prefix + article for prefix in (', ', ' ') for article in ("the", "a", "an")]
def _strip_trailing_article(title):
    title = title.lower()
    for article in _articles:
        if title.endswith(article):
            return title[:-len(article)]
    return title

def _searchresult_to_listitem(movie):
    movie_info = {'title': movie[1]}
    movie_label = movie[1]

    movie_year = movie[2] or None
    if movie_year:
        movie_label += ' ({})'.format(movie_year)
        movie_info['year'] = movie_year

    listitem = xbmcgui.ListItem(movie_label, offscreen=True)
    listitem.setInfo('video', movie_info)
    
    return listitem

# Low limit because a big list of artwork can cause trouble in some cases
# (a column can be too large for the MySQL integration),
# and how useful is a big list anyway? Not exactly rhetorical, this is an experiment.
IMAGE_LIMIT = 10

def add_artworks(listitem, artworks):
    for arttype, artlist in artworks.items():
        #xbmc.log('\n\n\n arttype:{} artlist{}'.format(arttype,artlist), xbmc.LOGDEBUG)
        if arttype == 'fanart':
            continue
        listitem.addAvailableArtwork(artlist['original'], arttype)

    if 'fanart' in artworks:
        fanart_to_set = [{'image': image['original'], 'preview': image['preview']}
            for image in artworks['fanart'][:IMAGE_LIMIT]]
            
        listitem.setAvailableFanart(fanart_to_set)
    #xbmc.log('\n\n\n fanart_to_set:{} '.format(fanart_to_set), xbmc.LOGDEBUG)

def get_details(url, handle, settings):
    
    if not url:
        return False
    details = get_csfd_scraper(settings).get_details(url)
    if not details:
        return False

    details = configure_csfd_artwork(details, settings)
    
    #xbmc.log('\n\ndetails:{}'.format(details), xbmc.LOGDEBUG) # debug

    listitem = xbmcgui.ListItem(details['info']['title'], offscreen=True)
    listitem.setInfo('video', details['info'])
    add_artworks(listitem, details['available_art'])
    if details['ratings']['rating']: listitem.setRating('csfd', details['ratings']['rating'], details['ratings']['votes'], True)
    

    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=listitem)
    return True

def build_lookup_string(uniqueids):
    return json.dumps(uniqueids)

def parse_lookup_string(uniqueids):
    try:
        return json.loads(uniqueids)
    except ValueError:
        #log("Can't parse this lookup string, is it from another add-on?\n" + uniqueids, xbmc.LOGWARNING)
        return None

def run():
    params = get_params(sys.argv[1:])
    enddir = True
    if 'action' in params:
        settings = ADDON_SETTINGS if not params.get('pathSettings') else \
            PathSpecificSettings(json.loads(params['pathSettings']), lambda msg: log(msg, xbmc.LOGWARNING))
        action = params["action"]
        if action == 'find' and 'title' in params:
            search_for_movie(params["title"], params.get("year"), params['handle'], settings)
        elif action == 'getdetails' and 'url' in params:
            enddir = not get_details(parse_lookup_string(params["url"]), params['handle'], settings)
            #BREAK
        elif action == 'NfoUrl' and 'nfo' in params:
            find_uniqueids_in_nfo(params["nfo"], params['handle'])
        else:
            log("unhandled action: " + action, xbmc.LOGWARNING)
    else:
        log("No action in 'params' to act on", xbmc.LOGWARNING)
    if enddir:
        xbmcplugin.endOfDirectory(params['handle'])

if __name__ == '__main__':
    run()
