import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugin.video.xvault'))

xbmc = types.ModuleType('xbmc')
xbmc.executebuiltin = lambda *args, **kwargs: None
xbmc.sleep = lambda *args, **kwargs: None
sys.modules.setdefault('xbmc', xbmc)

control = types.ModuleType('resources.lib.control')
control.addonName = 'xVAULT'
control.addonProfilePath = str(ROOT / '.codex-tmp')
control.getSetting = lambda name, default='': default


class _Progress:
    def create(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def close(self):
        pass


control.progressDialog = _Progress()
sys.modules.setdefault('resources.lib.control', control)

log_utils = types.ModuleType('resources.lib.log_utils')
log_utils.LOGWARNING = 'WARNING'
log_utils.log = lambda *args, **kwargs: None
sys.modules.setdefault('resources.lib.log_utils', log_utils)

from resources.lib import linear_tv


class LinearTVLogoTests(unittest.TestCase):
    def test_logo_parser_uses_alt_names_and_dach_countries(self):
        parsed = linear_tv._parse_logo_data(
            [
                {
                    'channel': 'RTLZwei.de',
                    'in_use': True,
                    'format': 'PNG',
                    'width': 900,
                    'url': 'https://example.invalid/rtlzwei.png',
                },
                {
                    'channel': 'SRFzwei.ch',
                    'in_use': True,
                    'format': 'PNG',
                    'width': 900,
                    'url': 'https://example.invalid/srfzwei.png',
                },
                {
                    'channel': 'ORFIII.at',
                    'in_use': True,
                    'format': 'PNG',
                    'width': 900,
                    'url': 'https://example.invalid/orfiii.png',
                },
            ],
            [
                {
                    'id': 'RTLZwei.de',
                    'name': 'RTL Zwei',
                    'alt_names': ['RTL 2'],
                    'country': 'DE',
                    'network': None,
                },
                {
                    'id': 'SRFzwei.ch',
                    'name': 'SRF zwei',
                    'alt_names': [],
                    'country': 'CH',
                    'network': None,
                },
                {
                    'id': 'ORFIII.at',
                    'name': 'ORF III',
                    'alt_names': [],
                    'country': 'AT',
                    'network': None,
                },
            ],
            [],
        )

        logos = parsed['logos']
        self.assertEqual(self._logo_for('RTL2 HD', logos), 'https://example.invalid/rtlzwei.png')
        self.assertEqual(self._logo_for('SRF 2', logos), 'https://example.invalid/srfzwei.png')
        self.assertEqual(self._logo_for('ORF 3', logos), 'https://example.invalid/orfiii.png')

    def test_logo_parser_prefers_current_png_logo(self):
        parsed = linear_tv._parse_logo_data(
            [
                {
                    'channel': 'Nitro.de',
                    'in_use': False,
                    'format': 'SVG',
                    'width': 2000,
                    'url': 'https://example.invalid/old.svg',
                },
                {
                    'channel': 'Nitro.de',
                    'in_use': True,
                    'format': 'PNG',
                    'width': 500,
                    'url': 'https://example.invalid/current.png',
                },
            ],
            [
                {
                    'id': 'Nitro.de',
                    'name': 'Nitro',
                    'alt_names': ['RTL Nitro'],
                    'country': 'DE',
                    'network': None,
                },
            ],
            [],
        )

        self.assertEqual(self._logo_for('RTL Nitro HD', parsed['logos']), 'https://example.invalid/current.png')

    def _logo_for(self, name, logos):
        return linear_tv._logo_for_aliases(linear_tv._live_channel_aliases({'name': name}), logos)


if __name__ == '__main__':
    unittest.main()
