import json
import os
from subprocess import call

from settings import BACKEND
from settings import BASE_DIR


apps_path = os.path.join(BASE_DIR, 'vendor/wappalyzer_apps.json')
if not os.path.isfile(apps_path):
    call(['vendor/update'])


with open(apps_path, 'r') as fh:
    apps = json.load(fh)['apps']

software_packages = BACKEND.retrieve_packages()
wappalyzer_apps = {}
for app_name, app_data in apps.items():
    for package in software_packages:
        if package.name.lower() == app_name.lower():
            wappalyzer_apps[package] = app_data


del software_packages
