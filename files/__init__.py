import os

from importlib import import_module
from inspect import getmembers, isclass


file_types = [module for module_file in (
    (
        member
        for class_name, member in getmembers(
            import_module('files.{}'.format(module[:-3])),
            isclass)
        if (member.__module__.startswith('files.') and
            class_name != 'File'))
    for module
    in os.listdir('files')
    if module.endswith('.py')
) for module in module_file]

file_types_for_analysis = [
    file
    for file in file_types
    if file.USE_FOR_ANALYSIS
]

file_types_for_index = [
    file
    for file in file_types
    if file.USE_FOR_INDEX
]


del getmembers, import_module, isclass, os
