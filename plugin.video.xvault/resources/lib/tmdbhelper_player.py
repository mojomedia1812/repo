import json


EMPTY_VALUES = ('', 'None', 'none', 'NULL', 'null')
INT_KEYS = {
    'year',
    'season',
    'episode',
    'number_of_seasons',
    'number_of_episodes',
    'playcount',
}
IGNORED_KEYS = {
    'action',
    'select',
    'tmdbhelper',
}
MODE_DIRECTORY = '1'
MODE_DIALOG = '0'

MODE_ALIASES = {
    '0': MODE_DIALOG,
    'dialog': MODE_DIALOG,
    '1': MODE_DIRECTORY,
    'directory': MODE_DIRECTORY,
    'folder': MODE_DIRECTORY,
    'verzeichnis': MODE_DIRECTORY,
    '2': '2',
    'autoplay': '2',
}

PARAM_ALIASES = {
    'media_type': 'mediatype',
    'tmdb': 'tmdb_id',
    'tvdb': 'tvdb_id',
}


def prepare_params(params, get_mode=None):
    prepared = dict(params)
    sysmeta = build_sysmeta(params)
    prepared['sysmeta'] = json.dumps(sysmeta)

    if is_tmdbhelper_call(params) and not _clean_value(params.get('select')):
        current_mode = _get_current_mode(get_mode)
        if current_mode == MODE_DIRECTORY:
            prepared['select'] = MODE_DIALOG

    return prepared


def build_sysmeta(params):
    sysmeta = {}
    mediatype = _normalise_mediatype(
        _clean_value(params.get('mediatype') or params.get('media_type')),
        params.get('season')
    )

    for key, value in params.items():
        target = PARAM_ALIASES.get(key, key)
        if target in IGNORED_KEYS:
            continue
        if target == 'mediatype':
            continue

        value = _clean_value(value)
        if value is None:
            continue
        if target in INT_KEYS:
            value = _to_int(value)
            if value is None:
                continue
            if value == 0 and not (target == 'season' and mediatype == 'tvshow'):
                continue

        sysmeta[target] = value

    if mediatype:
        sysmeta['mediatype'] = mediatype

    imdb = sysmeta.get('imdb_id') or sysmeta.get('imdbnumber') or sysmeta.get('imdb')
    if imdb:
        sysmeta.setdefault('imdb_id', imdb)
        sysmeta.setdefault('imdbnumber', imdb)
        sysmeta.setdefault('imdb', imdb)

    if mediatype == 'tvshow' and not sysmeta.get('title'):
        showname = _clean_value(params.get('showname'))
        if showname:
            sysmeta['title'] = showname

    return sysmeta


def is_tmdbhelper_call(params):
    return str(params.get('tmdbhelper', '')).strip().lower() in ('1', 'true', 'yes')


def fail_resolved_url():
    try:
        import sys
        import xbmcgui
        import xbmcplugin
        handle = int(sys.argv[1]) if len(sys.argv) > 1 else -1
        if handle > 0:
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())
    except Exception:
        pass


def _clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    if value in EMPTY_VALUES:
        return None
    return value


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalise_mediatype(value, season):
    if value:
        value = value.lower()
        if value in ('movie', 'movies'):
            return 'movie'
        if value in ('tv', 'show', 'episode', 'episodes', 'tvshow', 'tvshows'):
            return 'tvshow'

    season = _to_int(_clean_value(season))
    if season is None:
        return 'movie'
    return 'movie' if season == 0 else 'tvshow'


def _normalise_mode(value):
    value = _clean_value(value)
    if value is None:
        return None
    return MODE_ALIASES.get(value.lower())


def _get_current_mode(get_mode):
    try:
        mode = get_mode() if get_mode else None
        if mode is None:
            from resources.lib import playback_settings
            mode = playback_settings.get_mode()
        return _normalise_mode(mode) or mode
    except Exception:
        return None
