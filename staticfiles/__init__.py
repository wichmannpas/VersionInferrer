import os

from importlib import import_module
from inspect import getmembers, isclass


static_files = [module for module_file in (
    (
        member
        for class_name, member in getmembers(
            import_module('staticfiles.{}'.format(module[:-3])),
            isclass)
        if (member.__module__.startswith('staticfiles.') and
            class_name != 'StaticFile'))
    for module
    in os.listdir('staticfiles')
    if module.endswith('.py')
) for module in module_file]

static_files_for_analysis = [
    static_file
    for static_file in static_files
    if static_file.USE_FOR_ANALYSIS
]

static_files_for_index = [
    static_file
    for static_file in static_files
    if static_file.USE_FOR_INDEX
]


del getmembers, import_module, isclass, os
