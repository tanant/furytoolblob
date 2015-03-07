'''
Fury Road Shot Tools

a utility package containing some simple stringslicing functions
and hooks that allow us to manage user lists and suchlike.

2013-05-14-AT: Refactoring. Again. Cleaning up so that it's all just neat and 
    tidy and ShotBucket and ShotManager are stablized
2013-04-26-AT: Created

'''

# TODO: use pkgutil
# import pkgutil
# copied from http://stackoverflow.com/questions/3365740/how-to-import-all-submodules
#__all__ = []
#for loader, module_name, is_pkg in  pkgutil.walk_packages(__path__):
#    __all__.append(module_name)
#    module = loader.find_module(module_name).load_module(module_name)
#    print(module_name)
#    exec('%s = module' % module_name)
#    # TODO: cleanup here?


import os
import sys


__author__ = 'Anthony Tan <anthony.tan@rhubarbfizz.com>'
__date__ = '10 May 2013'


frozen = getattr(sys, 'frozen', '')
if not frozen:  
    __pkgroot__ = os.path.dirname(os.path.realpath(__file__))
else:
    __pkgroot__ = os.path.dirname(sys.executable)
    
    


def main(*argv, **kwargs):
    print("main!")
    print __pkgroot__
    
if __name__ == '__main__':
    main(sys.argv)