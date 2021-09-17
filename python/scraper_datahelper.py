import re
try:
    from urlparse import parse_qsl
except ImportError: # py2 / py3
    from urllib.parse import parse_qsl

# get addon params from the plugin path querystring
def get_params(argv):
    result = {'handle': int(argv[0])}
    if len(argv) < 2 or not argv[1]:
        return result

    result.update(parse_qsl(argv[1].lstrip('?')))
    return result

def find_uniqueids_in_text(input_text):
    result = {}
    res = re.search(r'(csfd.cz/film/)([0-9]+)', input_text)
    if (res):
        result['csfd'] = res.group(2)
    else:
        return False  # In case missing CSFD in nfo we wouldnt get to the directory name for query
    res = re.search(r'(themoviedb.org/movie/)([0-9]+)', input_text)
    if (res):
        result['tmdb'] = res.group(2)
    res = re.search(r'imdb....?/title/tt([0-9]+)', input_text)
    if (res):
        result['imdb'] = 'tt' + res.group(1)
    else:
        res = re.search(r'imdb....?/Title\?t{0,2}([0-9]+)', input_text)
        if (res):
            result['imdb'] = 'tt' + res.group(1)
    return result
