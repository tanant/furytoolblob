'''
Created on 30/08/2013

@author: OM005188
'''


import re
import os
import sys
import datetime
import shutil
import socket

from TT_utilities.filesys import touch as touch
from FuryTools.deliverablepackage import DIDeliverable, EditorialDeliverable
# this is the target area where shots go.
# into the Bag we only place fragments/placeholders


# within the bag, the data storage is a simple code fragment file (os.listdir vs fopen)
# but conceptually, the shotbag contains deliverables and codes. Note that the shotbag is
# always live querying the filesystem.. hmmm..


# theoretically, each code fragment in the shotbag could be translated (safely)
# to something in the shotroot based thing. But this would make the shotbag require knowledge of the
# shotroot. FFS. needs a proper teardown/rebuild

class ShotBag(object):

    def __init__(self, bagroot=r'H:\production\dailies\shotBag'):
        self.root = bagroot

        if not os.path.exists(bagroot):
            try:
                os.makedirs(bagroot)
            except OSError as e:
                raise

    def close(self):
        touch(os.path.join(self.root, "LOCKED"), mode='a', contents=str(datetime.datetime.now()) + '::' + socket.gethostname() + '\n', overwrite=True)

    def open(self):
        try:
            os.remove(os.path.join(self.root, "LOCKED"))
        except OSError:
            pass

    def is_closed(self):
        return os.path.exists(os.path.join(self.root, "LOCKED")) or not os.path.exists(self.root)

    def is_open(self):
        return not self.is_closed()

    def make_ready(self, code, comment=None):
        # write out a text stub file indicating that the named shot is ready
        if comment is None:
            touch(os.path.join(self.root, code), mode='a', contents=str(datetime.datetime.now()) + '::' + socket.gethostname() + '\n', overwrite=True)
        else:
            touch(os.path.join(self.root, '_'.join([code, comment])), mode='a', contents=str(datetime.datetime.now()) + '::' + socket.gethostname() + '\n', overwrite=True)

    def contents(self):
        # return a tuple of items
        # { digital_intermediary:[{shot:1, seq:2, ],
        #   editorial:[] }

        # each stub is a pkg/comment tuple. pkgs have no way of being swallowed
        # so we're doing a wrapped comment approach

        stubs = {'di': [],
                 'editorial': [],
                 'unknown': []}
        try:
            candidates = os.listdir(self.root)
        except OSError as e:
            return stubs

        # what's the algo.. look hardest for a DI pack first, then if it's not..

        for x in candidates:
            if re.search('(?i)^(?P<body>[a-z0-9]{3}_[a-z0-9]{3}_v[0-9]{3}_[0-9]{3}_[0-9]{8})(_(?P<comment>.*))*$', x):
                result = re.search('(?i)^(?P<body>[a-z0-9]{3}_[a-z0-9]{3}_v[0-9]{3}_[0-9]{3}_[0-9]{8})(_(?P<comment>.*))*$', x)

                stubs['di'].append((result.group('body'), result.group('comment')))

            elif re.search('(?i)^(?P<body>[a-z0-9]{3}_[a-z0-9]{3}_v[0-9]{3}_[a-z0-9]{3})(_(?P<comment>.*))*$', x):
                result = re.search('(?i)^(?P<body>[a-z0-9]{3}_[a-z0-9]{3}_v[0-9]{3}_[a-z0-9]{3})(_(?P<comment>.*))*$', x)
                stubs['editorial'].append((result.group('body'), result.group('comment')))
            elif re.search('(?i)^LOCKED$', x):
                pass
            else:
                stubs['unknown'].append(x)

        return stubs

    def empty(self):
        try:
            for x in os.listdir(self.root):
                if os.path.isdir(os.path.join(self.root, x)):
                    shutil.rmtree(os.path.join(self.root, x))
                else:
                    os.remove(os.path.join(self.root, x))
        except OSError:
            pass

    def remove(self, code, comment=None):
        try:
            # write out a text stub file indicating that the named shot is ready
            if comment is not None:
                os.remove(os.path.join(self.root, code + '_' + comment))

            else:
                os.remove(os.path.join(self.root, code))
        except OSError:
            pass

    def cleanup(self):
        for x in self.contents()['unknown']:
            try:
                os.remove(os.path.join(self.root, x))
            except OSError:
                pass

    # returns the shot tuple if it can be found, None otherwise
    # ugh. because we're lacking any kind of nice coding/keying, we are doomed to have to manage
    # it all with os.listdirs.

    # check the status of the shot with the associated comment.
    # urgh, but the data is always going to have UID against it.
    def check_shot(self, seq, shot, major, minor, comment=None, di=False):
        c = self.contents()
        if di:
            candidates = c['di']
        else:
            candidates = c['editorial']

        code = "{seq}_{shot}_v{major}_{minor}".format(seq=seq, shot=shot, major=major, minor=minor)

        matches = []
        for x in candidates:
            if x[0].lower().startswith(code) and x[1] == comment:
                matches.append(x)
        return matches

    # just a quick stubhack to check for validity.
    def shotcode_exists(self, shotcode, comment=None):
        if comment is not None:
            return os.path.isfile(os.path.join(self.root, x + '_' + comment))
        else:
            return os.path.isfile(os.path.join(self.root, x))

    def latest_version(self, seq, shot, comment=None, di=False):
        c = self.contents()
        if di:
            candidates = c['di']
        else:
            candidates = c['editorial']

        code = ("{seq}_{shot}".format(seq=seq, shot=shot)).lower()
        matches = []
        for x in candidates:
            if x[0].lower().startswith(code) and x[1] == comment:
                matches.append(x[0])

        try:
            return sorted(matches)[-1]
        except IndexError:
            return None

    # useful checker stubs
    def latest_di_delivered(self, seq, shot, ascode=True):
        code = self.latest_version(seq, shot, comment='DELIVERED', di=True)
        if ascode:
            return self._split_code(code)
        else:
            return code

    def latest_di_approved(self, seq, shot, ascode=True):
        code = self.latest_version(seq, shot, comment='APPROVED', di=True)
        if ascode:
            return self._split_code(code)
        else:
            return code

    def latest_di_inbag(self, seq, shot, ascode=True):
        code = self.latest_version(seq, shot, di=True)
        if ascode:
            return self._split_code(code)
        else:
            return code

    def _split_code(self, code):
        if code is not None:
            seq, shot, maj, min, uid = code.split('_')
            maj = maj[1:]
        else:
            return None

        return {'seq': seq,
                'shot': shot,
                'maj': maj,
                'min': min,
                'uid': uid, }


# testing blob
if __name__ == "__main__":
    from TT_utilities import path_tools as path_tools

    sb = ShotBag(path_tools.make_standard(r'H:\user\anthony.tan\garbage\shotbag'))
    sb.make_ready('chickens', comment='APPROVED')
    sb.make_ready('buz_123_v123_398_1238364', comment='APPROVED')
    sb.make_ready('buz_123_v123_398_12383623', comment='APPROVED')
    sb.make_ready('buz_123_v123_398', comment='APPROVED')
    sb.make_ready('ATS_540_v023_001_7000233_sparecode', comment='APPROVED')
    sb.make_ready('buz_123_v123_999_00000000_commentary', comment='APPROVED')
    sb.make_ready('buz_123_v123_999_00001111_commentaryandmore', comment='APPROVED')
    sb.make_ready('buz_123_v123_999_00001111_co_mmentaryandmore', comment='APPROVED')
    sb.make_ready('buz_560_v002_008_70002058', comment='DELIVERED')
    sb.make_ready('buz_560_v002_008_70002159', comment='DELIVERED')
    sb.make_ready('buz_560_v002_008_70002150', comment='DELIVERED')
    sb.make_ready('buz_560_v002_008_70002019')
    sb.make_ready('buz_560_v002_089', comment='APPROVED')

    # if you've put it in the bag, and then rendered over the top of it, what next? we can solve this with pre-render checks.
    # would be nice to extend SB to query what's in the bag in an efficient way.

    print sb.contents()
    print sb.check_shot('buz', '560', '002', '008', di=True, comment='APPROVED')
    print sb.check_shot('buz', '560', '002', '089', di=False, comment='APPROVED')
    print sb.latest_version('buz', '560', di=True, comment='DELIVERED')

    sb.cleanup()
    print sb.contents()
    sb.remove(sb.contents()['editorial'][0][0])
    print sb.contents()
    sb.empty()
    print sb.contents()

    print sb.is_closed()
    sb.close()
    print sb.is_closed()
    sb.open()
    print sb.is_closed()
