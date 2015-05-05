import os
import sys
import re
from TT_utilities import path_tools as path_tools

# always pass strings around
class DeliverablePackage(object):

    def __init__(self, seq=None, shot=None, major=None, minor=None, root=None, *args, **kwargs):

        if None in [seq, shot, major, minor, root]:
            print seq, shot, major, minor, root
            raise ValueError('incomplete deliverable specification')

        self.seq = seq
        self.shot = shot
        self.major = major
        self.minor = minor
        self.root = root  # this is a bootstrap
        self.type = "UNKNOWN"

    def __str__(self):
        return "root:{root} ({type}) {seq}_{shot}, v{major}_{minor}".format(**self.__dict__)

    def name(self):
        return "{seq}_{shot}_v{major}_{minor}".format(seq=self.seq.upper(), shot=self.shot.upper(), major=self.major, minor=self.minor)

    def code(self):
        return "{seq}_{shot}_v{major}_{minor}".format(**self.__dict__)

    def __eq__(self, other):
        try:
            return self.code == other.code
        except:
            return False


class DIDeliverable(DeliverablePackage):

    def __init__(self, *args, **kwargs):
        super(DIDeliverable, self).__init__(*args, **kwargs)

        self.type = 'digitalIntermediary'
        self.base = os.path.join(self.root, self.type, "{seq}_{shot}_v{major}_{minor}".format(**self.__dict__))
        newbase = os.path.join('{base}', '{seq}_{shot}_v{major}').format(**self.__dict__)
        try:
            newbase = path_tools.sensitise_to_case(newbase)
        except ValueError:
            print newbase
            raise
        # we have to sanitise and fix the newbase here, so that the os.path.isdir() call works case insensitively
        # the only tools that should be creating those files would be

        try:
            components = os.listdir(newbase)
            components = [x for x in components if not x.lower().startswith('.') and os.path.isdir(os.path.join(newbase, x))]

        except Exception as e:

            print e
            raise ValueError("internal directory doesn't match major/minor wrapper. Have you manually renamed stuff?")

        # filter out non directories and anything starting with a dot.
        # the UID is also assumed to be the latest in the list (sort asc)
        # print self.base
        self.uid = sorted([x for x in components if 'x' not in x])[-1]
        self.resolution = [x for x in components if 'x' in x][0]

    def get_mov(self):
        newbase = os.path.join('{base}', '{seq}_{shot}_v{major}', '{uid}').format(**self.__dict__)
        newbase = path_tools.sensitise_to_case(newbase)
        try:
            return os.path.join(newbase, [x for x in os.listdir(newbase) if x.lower().endswith('mov')][0])
        except:
            return None

    def get_ale(self):
        newbase = os.path.join('{base}', '{seq}_{shot}_v{major}', '{uid}').format(**self.__dict__)
        newbase = path_tools.sensitise_to_case(newbase)

        # reminde me again why we're doing an os.listdir? surely we know the ALE name by now?
        # os.path.join(newbase, {seq}_{shot}_v{major}.ale)
        try:
            return os.path.join(newbase, [x for x in os.listdir(newbase) if x.lower().endswith('ale')][0])
        except:
            return None

    def get_frame_base(self):
        newbase = os.path.join('{base}', '{seq}_{shot}_v{major}', '{resolution}').format(**self.__dict__)
        newbase = path_tools.sensitise_to_case(newbase)
        if os.path.isdir(newbase):
            return newbase
        else:
            return None

    def get_matte_base(self):
        newbase = os.path.join('{base}', '{seq}_{shot}_v{major}', '{resolution}', 'matte').format(**self.__dict__)
        newbase = path_tools.sensitise_to_case(newbase)
        if os.path.isdir(newbase):
            return newbase
        else:
            return None

    def code(self):
        return "{seq}_{shot}_v{major}_{minor}_{uid}".format(**self.__dict__)

    def name(self):
        return super(DIDeliverable, self).name() + " : ({uid})".format(**self.__dict__)
        # return "{seq}_{shot}_v{major}_{minor} : ({uid})".format(**self.__dict__)

    def prep_comp_path(self):
        return os.path.join(self.stereo_base_path(),
                            'st_layers',
                            '{seq}_{shot}_st_layers_v{major}_{minor}_specific.nk').format(**self.__dict__)

    def mini_comp_path(self):
        return os.path.join(self.stereo_base_path(),
                            'st_layers',
                            '{seq}_{shot}_st_layers_v{major}_{minor}_minicomp.nk').format(**self.__dict__)

    def stereo_base_path(self):
        return os.path.join(self.root,
                            'stereo',
                            '{seq}_{shot}_v{major}_{minor}',
                            '{seq}_{shot}_v{major}').format(**self.__dict__)

    # returns a full path string to where you should drop your layers
    # if you supply layerName you get it for free, otherwise you get {layer}
    def stereo_layer_template(self, layerName=None):
        base = os.path.join(self.stereo_base_path(),
                            'st_layers',
                            '{layer}',
                            '{seq}_{shot}_st_layers_'.format(**self.__dict__) + '{layer}' + '_v{major}_{minor}.#####.exr'.format(**self.__dict__))

        if layerName is not None:
            return base.format(layer=layerName)
        else:
            return base

    # checks to see if there's a stereo style package available
    def stereo_avail(self):
        # doing up a double check
        # two, presence of a minicomp
        # three, presence of a prepcomp

        if os.path.exists(self.prep_comp_path()) and os.path.exists(self.mini_comp_path()):
            return True
        else:
            return False

    def package_exists(self):
        return os.path.exists(self.get_frame_base())


class DIDeliverable_legacy(DeliverablePackage):

    def __init__(self, uid=None, *args, **kwargs):
        if uid is None:
            raise ValueError('legacy DI package requires UID to be specified')

        self.type = 'digitalIntermediary'

        super(DIDeliverable_legacy, self).__init__(major='999', minor='999', *args, **kwargs)
        self.uid = uid
        self.base = os.path.join(self.root, self.type, "{uid}".format(**self.__dict__))

    def get_mov(self):
        newbase = os.path.join('{base}', '1920x1080').format(**self.__dict__)
        try:
            return os.path.join(newbase, [x for x in os.listdir(newbase) if x.lower().endswith('mov')][0])
        except:
            return None

    def get_ale(self):
        newbase = os.path.join('{base}', '1920x1080').format(**self.__dict__)
        try:
            return os.path.join(newbase, [x for x in os.listdir(newbase) if x.lower().endswith('ale')][0])
        except:
            return None

    def get_frame_base(self):
        newbase = os.path.join('{base}', '2150x1210').format(**self.__dict__)
        if os.path.isdir(newbase):
            return newbase
        else:
            return None

    def get_matte_base(self):
        newbase = os.path.join('{base}', '2150x1210', 'matte').format(**self.__dict__)
        if os.path.isdir(newbase):
            return newbase
        else:
            return None

    def name(self):
        return "{seq}_{shot}_v{major}_{minor} : ({uid})".format(**self.__dict__)

    def code(self):
        return "{seq}_{shot}_v{major}_{minor}_{uid}".format(**self.__dict__)

class EditorialDeliverable(DeliverablePackage):

    def __init__(self, *args, **kwargs):
        super(EditorialDeliverable, self).__init__(*args, **kwargs)

        self.type = 'editorial'
        self.base = os.path.join(self.root, self.type, "{seq}_{shot}_v{major}_{minor}".format(**self.__dict__))

    def get_mov(self):
        try:
            return os.path.join(self.base, [x for x in os.listdir(self.base) if x.lower().endswith('mov')][0])
        except:
            print self.base
            print os.listdir(self.base)
            return None

    def get_ale(self):
        try:
            return os.path.join(self.base, [x for x in os.listdir(self.base) if x.lower().endswith('ale')][0])
        except:
            return None


if __name__ == '__main__':

    did = DIDeliverable(seq='aaf',
                        shot='050',
                        major='004',
                        minor='001',
                        #uid = '70004712',
                        root=r'\\vfx\fury\shots\aaf\aaf_050\deliverables')

    print did
    print did.prep_comp_path()
    print did.stereo_avail()
    print did.stereo_layer_template()
    print did.stereo_layer_template(layerName="magic_chicken")

    print EditorialDeliverable(seq='aaf',
                               shot='010',
                               major='006',
                               minor='004',
                               # uid = '70000449',
                               root=r'\\vfx\fury\shots\aaf\aaf_010\deliverables')
