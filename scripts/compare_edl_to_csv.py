#!/usr/bin/python

# accepts three arguments, the first is the input EDL, the second is an input CSV from filemaker
# the third is optional and is the name of the file to write. If omitted, defaults to 'report.csv'
# will provide results which should show the entirety of the CSV and EDL supplied


'''
Created on 12/09/2013

@author: OM005188
'''
import re
import math
import os
import sys
import csv

class FM_CSV(object):

    def __init__(self, fname):
        self.sourcefile = fname
        self.clips = []
        self._load_clips()

    def _load_clips(self):
        with open(self.sourcefile, 'rU') as fp_in:
            rawdata = csv.reader(fp_in, csv.QUOTE_ALL)
            for row in rawdata:
                # break into blocks of six. discard trailers
                for block in xrange(0, (len(row) // 6) * 6, 6):
                    scan_name = row[block]
                    if scan_name:
                        slate = row[block + 1]
                        src_in = row[block + 2]
                        src_out = row[block + 3]
                        length = row[block + 4]
                        print length
                        resolution = row[block + 5]
                        self.clips.append({'scan_name': scan_name,
                                           'slate': slate,
                                           'src_in': src_in,
                                           'src_out': src_out,
                                           'length': float(length),
                                           'resolution': resolution, })
        if self.clips == []:
            raise ZeroCSV('Empty CSV?')

    def __str__(self):
        report = "\"{title}\": {numclips} clips".format(title=self.sourcefile, numclips=len(self.clips))
        return report

class Error(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class BadFile(Error):
    pass

class ZeroCSV(Error):
    pass

class EDL(object):

    def __init__(self, edlfile):
        self.sourcefile = edlfile

        self.title = None
        self.header_unparsed = []
        self.body_unparsed = []

        # assumes that the files are small enough to do this
        with open(self.sourcefile, 'rU') as fp_in:
            self._raw_pos = -1
            self._raw_data = fp_in.readlines()

        self._load_header()
        self._load_clips()

    def _nextline(self):
        self._raw_pos += 1
        try:
            nextline = self._raw_data[self._raw_pos]
        except IndexError:
            return None

        return nextline

    def _seek_back(self):
        self._raw_pos -= 1

    def _prevline(self):
        self._raw_pos -= 1

        if self._raw_pos < 0:
            self._raw_pos = -1
            return None
        nextline = self._raw_data[self._raw_pos]
        return nextline

    def _load_clips(self):
        # FIXME: for performance you should call re.compile on these outside of the line loop:

        re_clipstartstring = (r'\s*',                       # any number of spaces (front pad)
                              r'(?P<edit_num>[0-9]+)\s+',   # a string of digits, then at least one space
                              r'(?P<name>[^\s]+)\s+',       # a string of non-space things, then at least one space
                              r'(?P<source>[^\s]+)\s+',   # a string of non-space things, then at least one space
                              r'(?P<transfer>[^\s]+)\s+',   # etc
                              r'(?P<src_in>[^\s]+)\s+',
                              r'(?P<src_out>[^\s]+)\s+',
                              r'(?P<edit_in>[^\s]+)\s+',
                              r'(?P<edit_out>[^\s]+)\s+',
                              r'$')                        # and nothing else

        re_ascsop = (r'\s*\*\s*',                                    # a star, with or without spaces
                     r'(?i)ASC_SOP\s+',                              # case insensitive magic ASC_SOP match
                     r'\((?P<slope>[0-9.-]+\s+[0-9.-]+\s+[0-9.-]+)\)\s*',  # triplets of within parentheses
                     r'\((?P<offset>[0-9.-]+\s+[0-9.-]+\s+[0-9.-]+)\)\s*',  # triplets of within parentheses
                     r'\((?P<power>[0-9.-]+\s+[0-9.-]+\s+[0-9.-]+)\)\s*',  # triplets of within parentheses
                     r'$')                                          # and nothing else

        re_ascsat = (r'\s*\*\s*',                            # a star, with or without spaces
                         r'(?i)ASC_SAT\s+',                      # case insensitive magic ASC_SAT match
                         r'\((?P<saturation>[0-9.-]+\s+[0-9.-]+\s+[0-9.-]+)\)\s*',  # triplets of numbers within parentheses
                         r'$')                                  # and nothing else

        re_fromclip = (r'\s*\*\s*',                           # a star, with or without spaces
                       r'(?i)FROM CLIP NAME:',                 # magic opening statement
                       r'(?P<from_clip_name>.+)',              # whatever you've got on the line
                       r'$')                                  # all the way to EOL

        understood = [re_ascsop, re_ascsat, re_fromclip, re_clipstartstring]

        exhausted = False

        current_clip = {}
        # it's a list.
        self.clips = []

        # bootstrap phase, hunt for the first clip
        while not exhausted:

            line = self._nextline()

            if line is None:
                # FIXME: I think you want to 'break' here
                exhausted = True
            elif not line.strip():  # skip blank lines
                # FIXME: I think you want a 'continue' here
                pass

            # FIXME: if line is None: this will fail (which is why you need the break above):
            result = re.search(re_clipstartstring, line)
            if result is not None:
                self._seek_back()
                break
            else:
                self.header_unparsed.append((line, self._raw_pos + 1))   # we consider this header junk

        # now we've bootstrapped so we can guarantee the next call here will be an re_clipstart
        while not exhausted:
            line = self._nextline()

            if line is None:
                if name in current_clip:
                    # there's data here waiting to be flushed, flush it
                    self.clips.append(current_clip)
                # we're done
                break

            if not line.strip():  # skip blank lines
                # FIXME: I think you want a 'continue' here
                # pass
                continue

            # find out which re_matches the line
            for re_command in understood:
                result = re.search(re_command, line)
                if result is not None:
                    break
            else:
                # we don't know how to handle. Discard non-silently
                self.body_unparsed.append((line, self._raw_pos + 1))
                continue

            if re_command == re_ascsop:
                current_clip['slope'] = map(float, result.group('slope').split())
                current_clip['offset'] = map(float, result.group('offset').split())
                current_clip['power'] = map(float, result.group('power').split())
            elif re_command == re_ascsat:
                current_clip['saturation'] = map(float, result.group('saturation'))
            elif re_command == re_fromclip:
                current_clip['from_clip_name'] = result.group('from_clip_name').strip()
            elif re_command == re_clipstartstring:
                # the canary/key is 'name'

                if name in current_clip:
                    # there's data here waiting to be flushed, flush it
                    self.clips.append(current_clip)
                    current_clip = {}

                # always start new
                current_clip['name'] = result.group('name').lower()
                current_clip['src_in'] = result.group('src_in')
                current_clip['src_out'] = result.group('src_out')
                current_clip['edit_in'] = result.group('edit_in')
                current_clip['edit_out'] = result.group('edit_out')

    def _load_header(self):
        # ignore empty lines
        re_titlestring = r'^\s*TITLE:\s+(?P<title>.+)\s+'
        re_endheaderstring = r'\s*[0-9]+\s+'    # anything that begins with a numeric ID

        exhausted = False
        while not exhausted:
            line = self._nextline()
            if line is None:
                exhausted = True
            elif not line.strip():  # skip blank lines
                pass
            elif self.title is None:   # this is a line to check
                try:
                    self.title = re.search(re_titlestring, line).group('title').rstrip()
                except AttributeError:
                    raise BadFile('something other than TITLE block found first')
            elif not re.search(re_endheaderstring, line):
                self.header_unparsed.append((line, self._raw_pos + 1))
            else:
                self._seek_back()
                return
        raise BadFile('non-conforming header')

    def __str__(self):
        report = "\"{title}\": {numclips} clips".format(title=self.title, numclips=len(self.clips))
        if self.header_unparsed != [] or self.body_unparsed != []:
            report += ' ({x} unknown header lines, {y} unknown body lines)'.format(x=len(self.header_unparsed), y=len(self.body_unparsed))
        return report

def frame_to_timecode(frame, fps=24):
    # dd hh mm ss ff
    #              1
    #          fps
    #       60*fps
    #    60*60*fps
    # 24*60*60*fps

    tc = []
    remaining = frame
    for x in [24 * 60 * 60 * fps, 60 * 60 * fps, 60 * fps, fps, 1]:
        consumed = math.trunc(remaining / float(x))
        remaining -= consumed * x
        tfm_csv.append(consumed)

    return '{dd:02d}:{hh:02d}:{mm:02d}:{ss:02d}.{ff:02d}'.format(dd=tc[0],
                                                                 hh=tc[1],
                                                                 mm=tc[2],
                                                                 ss=tc[3],
                                                                 ff=tc[4],
                                                                 )
def timecode_to_frame(timecodestring, fps=24):
    components = re.split(r'[^0-9]+', timecodestring)

    # the reversal of the components is
    # simply to take advantage of zip's halting condition
    return sum(map(lambda x: int(x[0]) * int(x[1]), zip([24 * 60 * 60 * fps, 60 * 60 * fps, 60 * fps, fps, 1][::-1], components[::-1])))


def frame_to_timecode(frame, fps=24):
    # dd hh mm ss ff
    #              1
    #          fps
    #       60*fps
    #    60*60*fps
    # 24*60*60*fps

    tc = []
    remaining = frame
    for x in [24 * 60 * 60 * fps, 60 * 60 * fps, 60 * fps, fps, 1]:
        consumed = math.trunc(remaining / float(x))
        remaining -= consumed * x
        tfm_csv.append(consumed)

    return '{dd:02d}:{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}'.format(dd=tc[0],
                                                                 hh=tc[1],
                                                                 mm=tc[2],
                                                                 ss=tc[3],
                                                                 ff=tc[4],
                                                                 )
def timecode_to_frame(timecodestring, fps=24):
    components = re.split(r'[^0-9]+', timecodestring)

    # the reversal of the components is
    # simply to take advantage of zip's halting condition
    # FIXME:  might be good to decompose this into a few lines for readability
    return sum(map(lambda x: int(x[0]) * int(x[1]), zip([24 * 60 * 60 * fps, 60 * 60 * fps, 60 * fps, fps, 1][::-1], components[::-1])))

# attach a new clipkey parameter
class comparison_EDL(EDL):

    def get_clip_from_key(self, key):

        if key in self.clipkeys.keys():
            index = self.clipkeys[key]
            del (self.clipkeys[key])
            return self.clips[index]
        else:
            return None

    def __init__(self, *args, **kwargs):
        super(comparison_EDL, self).__init__(*args, **kwargs)
        self.clipkeys = {}
        for index, clip in enumerate(self.clips):

            key = (clip['from_clip_name'].lower()[0:13] + '::' + clip['name']).lower()
            self.clipkeys[key] = index
            # print key

if __name__ == '__main__':
    import sys
    # edl = comparison_EDL(r'H:\user\anthony.tan\development\scripts\TO_048.edl')
    # for x in edl.clips:
    #    print x['name'], x['from_clip_name']
    #    print edl.clipkeys

    try:
        #edl = comparison_EDL(sys.argv[1])
        #fm_csv = FM_CSV(sys.argv[2])

        edl = comparison_EDL(r'P:\FromEditorial\001_Turnovers\193\to_edls\to_193_edl_old.edl')
        fm_csv = FM_CSV(r'P:\FromEditorial\001_Turnovers\193\to_edls\to_193.csv')
        print edl
    except BadFile as e:
        print "ERROR: EDL could not be understood..."
        print "first argument must be the EDL file, second must be the CSV"
        sys.exit(-1)

    except ZeroCSV as e:
        print "ERROR: CSV has no recognized entries"
        print "first argument must be the EDL file, second must be the CSV"
        sys.exit(-1)

    except (IOError, OSError, IndexError) as e:
        print "ERROR: one of the files could not be read"
        print "first argument must be the EDL file, second must be the CSV"
        print e
        sys.exit(-1)

    finally:
        pass

    try:
        outfile = sys.argv[3]
    except:
        outfile = "report.csv"

    report = []

    # now do a comparison, assuming CSV is lead.
    for clip in fm_csv.clips:
        all_good = True

        result = {}
        result['name'] = clip['scan_name']
        result['slate'] = clip['slate'].lower()[0:-4]

        key = clip['scan_name'] + '::' + clip['slate'].lower()[0:-4]   # strip out the .ari extension

        print 'found --> ', key
        found_edl_clip = edl.get_clip_from_key(key.lower())

        # assume it's all broken first
        result['match_duration'] = False
        result['match_all'] = False
        result['found_in_edl'] = False
        result['found_in_csv'] = True
        result['match_out'] = False
        result['match_in'] = False
        result['match_csv_duration_calculation'] = False
        result['csv_in_raw'] = clip['src_in']
        result['csv_out_raw'] = clip['src_out']
        result['csv_duration_raw'] = clip['length']
        result['csv_duration_calculated'] = timecode_to_frame(clip['src_out']) - timecode_to_frame(clip['src_in']) + 1
        if result['csv_duration_raw'] == result['csv_duration_calculated']:
            result['match_csv_duration_calculation'] = True

        result['edl_in_raw'] = "--:--:--:--"
        result['edl_out_raw'] = "--:--:--:--"
        result['edl_duration_calculated'] = 0

        if found_edl_clip is not None:
            result['edl_in_raw'] = found_edl_clip['src_in']
            result['edl_out_raw'] = found_edl_clip['src_out']
            result['edl_duration_calculated'] = timecode_to_frame(found_edl_clip['src_out']) - timecode_to_frame(found_edl_clip['src_in'])

            # and build the checks

            result['found_in_edl'] = True

            if result['csv_duration_raw'] == result['edl_duration_calculated']:
                result['match_duration'] = True

            if result['csv_in_raw'] == result['edl_in_raw']:
                result['match_in'] = True

            if timecode_to_frame(result['csv_out_raw']) == timecode_to_frame(result['edl_out_raw']) - 1:  # EDLs are +1 frame inclined
                result['match_out'] = True

            if result['match_out'] and \
               result['match_in'] and \
               result['match_duration'] and\
               result['match_csv_duration_calculation']:
                result['match_all'] = True

        report.append(result)

    for clipkey, clipindex in edl.clipkeys.items():
        result = {}
        clip = edl.clips[clipindex]

        result['name'] = clip['from_clip_name']
        result['slate'] = clip['name'].lower()

        print 'not in CSV --> ', clip['from_clip_name'] + '::' + clip['name']

        # assume it's all broken first
        result['match_duration'] = False
        result['match_all'] = False
        result['found_in_edl'] = True
        result['found_in_csv'] = False
        result['match_out'] = False
        result['match_in'] = False
        result['match_csv_duration_calculation'] = False
        result['csv_in_raw'] = "--:--:--:--"
        result['csv_out_raw'] = "--:--:--:--"
        result['csv_duration_raw'] = 0
        result['csv_duration_calculated'] = 0
        result['match_csv_duration_calculation'] = False

        result['edl_in_raw'] = clip['src_in']
        result['edl_out_raw'] = clip['src_out']
        result['edl_duration_calculated'] = timecode_to_frame(clip['src_out']) - timecode_to_frame(clip['src_in'])

        report.append(result)

    order = ['name',
             'slate',
             'match_all',
             'found_in_csv',
             'found_in_edl',
             'match_duration',
             'match_in',
             'match_out',
             'match_csv_duration_calculation',
             'csv_duration_raw',
             'csv_duration_calculated',
             'edl_duration_calculated',
             'csv_in_raw',
             'edl_in_raw',
             'csv_out_raw',
             'edl_out_raw', ]

    print "\n-------\nResults\n-------"

    try:
        with open(outfile, 'wb') as fp_out:
            out = csv.writer(fp_out)
            print "wrote the following results to:", outfile
            print "\n"
            out.writerow(order)
            for row in report:
                temprow = []
                for field in order:
                    temprow.append(row[field])
                out.writerow(temprow)
    except:
        print "Couldn't open output file: ", outfile
        print "\n"

    finally:    # always dump to stdout
        console = csv.writer(sys.stdout)
        console.writerow(order)
        for row in report:
            temprow = []
            for field in order:
                temprow.append(row[field])
            console.writerow(temprow)
