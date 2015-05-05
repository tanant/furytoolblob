if True:
    import csv
    import os
    import sys
    import re
    import subprocess
    import time
    import datetime

    import math
    import re

    src_dir = r'P:\FromEditorial\003_Additional Requests\131207\Dailies_AJ\DAYR015_batch2'
    src_watermark = r'H:\user\anthony.tan\WATERMARK_AJ_20131206.png'

    dirname = src_dir
    outdir = os.path.join(dirname, "AJ_watermarked_output")
    binary = r'H:\tools\software\FFmpeg\win64\ffmpeg-20130809-git-3b2e99f-win64-static\bin\ffmpeg.exe'
    sentry = os.path.join(src_dir, 'go')
    sentry_alt = os.path.join(src_dir, 'go.txt')
    progress = os.path.join(src_dir, 'processing')
    sleep = 30

    while True:
        if os.path.exists(sentry) or os.path.exists(sentry_alt):
            with open(progress, 'wt') as fp_out:
                pass

            # just incase you get the problem with .txt file extensions being hidden.
            try:
                os.remove(sentry)
            except:
                pass

            try:
                os.remove(sentry_alt)
            except:
                pass

            try:
                os.mkdir(outdir)
            except:
                pass

            process_list = sorted([x for x in os.listdir(dirname) if x.lower().endswith('mov')])
            for x in process_list:
                repack_string = [binary,
                                 '-r',
                                 '24',
                                 '-i',
                                 os.path.join(dirname, x),
                                 '-i',
                                 src_watermark,
                                 '-filter_complex',
                                 'overlay',
                                 '-pix_fmt',
                                 'yuv420p',
                                 '-profile:v',
                                 'baseline',
                                 '-g',
                                 '4',
                                 '-r',
                                 '24',
                                 '-threads',
                                 '0',
                                 '-y',  # just overwrite
                                 os.path.join(outdir, x),
                                 ]
                print repack_string
                if os.path.exists(os.path.join(outdir, x)):
                    print "skipping, outexists"
                elif os.path.exists(progress):
                    subprocess.check_call(repack_string)
                else:
                    break
            try:
                os.remove(progress)  # remove in progress note
            except OSError:
                pass

        else:
            print "\n{dt} - can't find a file called 'go' in the monitored folder: {tgt}. Sleeping for {sleep}".format(dt=datetime.datetime.now(), sleep=sleep, tgt=src_dir),
            for x in xrange(0, sleep, 5):
                time.sleep(5)
                print '.',
