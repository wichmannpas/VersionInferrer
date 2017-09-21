import os

from importlib import import_module
from inspect import getmembers, isclass


definitions = [module for module_file in (
    (
        member
        for class_name, member in getmembers(
            import_module('definitions.{}'.format(module[:-3])),
            isclass)
        if (member.__module__.startswith('definitions.') and
            class_name != 'SoftwareDefinition'))
    for module
    in os.listdir('definitions')
    if module.endswith('.py')
) for module in module_file]


del getmembers, import_module, isclass, os
