import json
import os
from subprocess import call

from analysis.wappalyzer import WappalyzerApp
from settings import BACKEND, BASE_DIR


apps_path = os.path.join(BASE_DIR, 'vendor/wappalyzer_apps.json')
if not os.path.isfile(apps_path):
    call(['vendor/update'])


with open(apps_path, 'r') as fh:
    apps = json.load(fh)['apps']

software_packages = BACKEND.retrieve_packages()
wappalyzer_apps = set()
for app_name, app_data in apps.items():
    for package in software_packages:
        if (package.name.lower() == app_name.lower() or
                any(name.lower() == app_name.lower()
                    for name in package.alternative_names)):
            wappalyzer_apps.add(WappalyzerApp(package, app_data))

wappalyzer_apps = frozenset(wappalyzer_apps)


del software_packages
