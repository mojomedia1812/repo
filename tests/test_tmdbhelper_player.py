import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugin.video.xvault'))

from resources.lib import tmdbhelper_player


class TMDbHelperPlayerTests(unittest.TestCase):
    def test_movie_params_keep_existing_xvault_metadata_shape(self):
        prepared = tmdbhelper_player.prepare_params({
            'action': 'playTMDbHelper',
            'tmdbhelper': '1',
            'mediatype': 'movie',
            'title': 'Good Bye Lenin!',
            'originaltitle': 'Good Bye Lenin!',
            'year': '2003',
            'season': '0',
            'episode': '0',
            'imdb_id': 'tt0301357',
            'tmdb_id': '338',
            'poster': 'https://example.invalid/poster.jpg',
        }, get_mode=lambda: 'Autoplay')

        meta = json.loads(prepared['sysmeta'])
        self.assertEqual(meta['mediatype'], 'movie')
        self.assertEqual(meta['title'], 'Good Bye Lenin!')
        self.assertEqual(meta['year'], 2003)
        self.assertEqual(meta['imdb_id'], 'tt0301357')
        self.assertEqual(meta['imdbnumber'], 'tt0301357')
        self.assertNotIn('season', meta)
        self.assertNotIn('episode', meta)
        self.assertNotIn('select', prepared)

    def test_episode_uses_show_title_and_falls_back_from_directory_to_dialog(self):
        prepared = tmdbhelper_player.prepare_params({
            'action': 'playTMDbHelper',
            'tmdbhelper': 'true',
            'mediatype': 'tvshow',
            'title': 'Dark',
            'year': '2017',
            'season': '1',
            'episode': '2',
            'episode_title': 'Luegen',
            'episode_premiered': '2017-12-01',
            'imdbnumber': 'tt5753856',
            'tmdb_id': '70523',
        }, get_mode=lambda: 'Verzeichnis')

        meta = json.loads(prepared['sysmeta'])
        self.assertEqual(meta['mediatype'], 'tvshow')
        self.assertEqual(meta['title'], 'Dark')
        self.assertEqual(meta['season'], 1)
        self.assertEqual(meta['episode'], 2)
        self.assertEqual(meta['episode_title'], 'Luegen')
        self.assertEqual(meta['imdb_id'], 'tt5753856')
        self.assertEqual(prepared['select'], '0')

    def test_explicit_select_is_respected_for_tmdbhelper(self):
        prepared = tmdbhelper_player.prepare_params({
            'tmdbhelper': '1',
            'mediatype': 'tvshow',
            'title': 'Dark',
            'season': '1',
            'episode': '1',
            'select': '2',
        }, get_mode=lambda: 'Verzeichnis')

        self.assertEqual(prepared['select'], '2')

    def test_missing_optional_numbers_do_not_raise(self):
        prepared = tmdbhelper_player.prepare_params({
            'action': 'playTMDbHelper',
            'tmdbhelper': '1',
            'mediatype': 'movie',
            'title': 'M',
            'year': '',
            'season': 'None',
            'episode': 'None',
            'imdb': 'tt0022100',
        }, get_mode=lambda: 'Dialog')

        meta = json.loads(prepared['sysmeta'])
        self.assertEqual(meta['mediatype'], 'movie')
        self.assertEqual(meta['title'], 'M')
        self.assertNotIn('year', meta)
        self.assertEqual(meta['imdb_id'], 'tt0022100')


if __name__ == '__main__':
    unittest.main()
