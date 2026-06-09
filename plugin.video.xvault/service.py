
# 2022-10-09
# edit 2025-07-15

import sys, os, requests, threading
from random import choice
from xbmcaddon import Addon
# from resources.lib.requestHandler import cRequestHandler
try:
    from resources.lib.tools import logger
    isLogger=True
except:
    isLogger=False
    pass


is_python2 = sys.version_info.major == 2
if is_python2:
    from xbmc import translatePath
    from urlparse import urlparse
else:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse

addonInfo = Addon().getAddonInfo
addonPath = translatePath(addonInfo('path'))
addonVersion = addonInfo('version')
setSetting = Addon().setSetting
_getSetting = Addon().getSetting
_settingsLock = threading.Lock()

def getSetting(Name, default=''):
    result = _getSetting(Name)
    if result: return result
    else: return default

# Html Cache beim KodiStart loeschen
def delHtmlCache():
    try:
        from resources.lib.requestHandler import cRequestHandler
        from time import time
        deltaDay = int(getSetting('cacheDeltaDay', 3))
        deltaTime = 60*60*24*deltaDay # Tage
        currentTime = int(time())
        # einmalig
        if getSetting('delHtmlCache') == 'true':
            cRequestHandler('').clearCache()
            setSetting('lastdelhtml', str(currentTime))
            setSetting('delHtmlCache', 'false')
        # alle x Tage
        elif currentTime >= int(getSetting('lastdelhtml', 0)) + deltaTime:
            cRequestHandler('').clearCache()
            setSetting('lastdelhtml', str(currentTime))
    except: pass

# Scraper(Seiten) ein- / ausschalten
#  [(providername, domainname), ...]     providername identisch mit dateiname
def _getPluginData():
    import importlib.util
    from os import path
    from scrapers import getActiveProviderFolder, getProviderModuleNames
    sPluginFolder = getActiveProviderFolder()
    if sPluginFolder not in sys.path:
        sys.path.append(sPluginFolder)
    aFileNames = getProviderModuleNames()
    aPluginsData = []
    for fileName in aFileNames:
        try:
            module_path = path.join(sPluginFolder, fileName + '.py')
            spec = importlib.util.spec_from_file_location('xvault_service_%s' % fileName, module_path)
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)
            # print(plugin.SITE_DOMAIN +'  '+ plugin.SITE_IDENTIFIER)
            aPluginsData.append({'domain': plugin.SITE_DOMAIN, 'provider': plugin.SITE_IDENTIFIER})
        except:
            pass
    return aPluginsData


def check_domains():
    domains = _getPluginData()
    threads = []
    try:
        for item in domains:
            _domain = item['domain']
            _provider = item['provider']
            t = threading.Thread(target=_checkdomain, args=(_domain, _provider), daemon=True)
            threads += [t]
            t.start()
    except:
        pass
    for t in threads:
        t.join(timeout=10)

def RandomUA():
    #Random User Agents aktualisiert 08.06.2025
    FF_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
    OPERA_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 OPR/119.0.0.0'
    ANDROID_USER_AGENT = 'Mozilla/5.0 (Linux; Android 15; SM-S931U Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36'
    EDGE_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
    CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    SAFARI_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15'

    _User_Agents = [FF_USER_AGENT, OPERA_USER_AGENT, EDGE_USER_AGENT, CHROME_USER_AGENT, SAFARI_USER_AGENT]
    return choice(_User_Agents)

def _checkdomain(_domain, _provider):
    try:
        requests.packages.urllib3.disable_warnings()  # weil verify = False - ansonst Fehlermeldungen im kodi log
        check=None
        status_code=None
        if _provider == 'vavoo':
            with _settingsLock:
                setSetting('provider.' + _provider + '.check', 'true')
            return
        domain = getSetting('provider.'+ _provider +'.domain', _domain)
        base_link = 'https://' + domain
        try:
            UA=RandomUA()
            headers = {
                "referer": base_link,
                "user-agent": UA,
            }
            r = requests.head(base_link, verify=False, headers=headers, timeout=8)
            status_code = r.status_code
            if 300 <= status_code <= 400:
                from urllib.parse import urljoin
                url = urljoin(base_link, r.headers.get('Location', ''))
                domain = urlparse(url).hostname
                check = 'true' if domain else 'false'
            elif status_code == 200:
                domain = urlparse(base_link).hostname
                check = 'true'
            else:
                check = 'false'
        except:
            check = 'false'
            #pass
        finally:
            wrongDomain = 'site-maps.cc', 'www.drei.at', 'notice.cuii.info'
            with _settingsLock:
                if domain in wrongDomain:
                    setSetting('provider.' + _provider + '.check', '')
                    setSetting('provider.' + _provider + '.domain', '')
                else:
                    setSetting('provider.' + _provider + '.check', check)
                    setSetting('provider.' + _provider + '.domain', domain)
            if isLogger: logger.info(' -> [service]: Provider: %s / Statuscode: %s / Domain: %s, Check: %s' % (_provider, status_code, domain, check))
    except: pass

if __name__ == "__main__":
	import xbmc
	if not xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)"):
		xbmc.executebuiltin('InstallAddon(inputstream.adaptive)')
		xbmc.executebuiltin('SendClick(11)')
	check_domains()
	delHtmlCache()
