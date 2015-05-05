# compatible with the 2.6.4 mayapy.exe interpreter if you need.


import re
import subprocess
import sys
import os
import time
import datetime


def _error(msg):
    raise ValueError(str(datetime.datetime.now()) + " [ERROR]: " + msg)

def _info(msg):
    print str(datetime.datetime.now()) + " [INFO]: " + msg

def _launch(command_list, list_of_subprocs, poll_interval=0.1):
    launched = False
    # print list_of_subprocs
    while not launched:
        for idx, slot in enumerate(list_of_subprocs):
            try:
                if slot.poll() is not None:
                    launched = True
                    break
            except:
                launched = True
                break

        if launched:
            list_of_subprocs[idx] = subprocess.Popen(command_list)
            # FIXME: what's this pass doing here?
            pass

def _cleanup(list_of_subprocs, poll_interval=0.1):
    # FIXME: I don't think this works: spawn_slots is not defined in this scope
    cleanup = False
    while spawn_slots:
        for x in list_of_subprocs:
            try:
                if x.poll() is not None:
                    spawn_slots.pop(spawn_slots.index(x))
            except AttributeError:  # trap for the case when no procs are spawned, x will be None so x.poll() fails
                spawn_slots.pop(spawn_slots.index(x))

        if spawn_slots == []:
            cleanup = True


def convert_dir(directory, overwrite=False, binary_override=None, spawn_instances=1):
    accepted = ['dpx']
    if binary_override is None:
        if sys.platform == 'darwin':
            # this still needs to be scavenged potentially due to the macos annoying
            # system to mounts (read: AFP/CIFS/suffix-appending misery)
            executable = r'/Volumes/fury-1/tools/software/FFmpeg/macos/ffmpeg-2.0.1-tessus'
        else:
            executable = r'\\vfx\fury\tools\software\FFmpeg\win64\ffmpeg-20130809-git-3b2e99f-win64-static\bin\ffmpeg.exe'
    else:
        executable = binary_override

    # command = ['{binary}', '-v', '0', '-loglevel', '0', '{overwrite}', '-i', '{src}', '-q:v','2', '{dest}']
    binary = r'{ffmpeg}'

    extra_args = [r'-i', '{infile}',  # input file
                  r'-q:v', r'{quality}',  # quality level
                  r'-loglevel', r'{loglevel}',  # libav* log level form one
                  r'-v', r'{loglevel}',  # libav* log level form two
                  r'{overwrite_flag}',  # overwrite or not. a simple -y/-n flag
                  r'{outfile}',  # output file
                  ]

    execstring = [binary] + extra_args

    # defaults
    quality = '2'
    loglevel = '0'

    found = False
    if os.path.exists(executable):
        _info('Found {0}'.format(executable))
        found = True

    if not found:
        _error("No conversion helper found")

    basedir = directory
    targetdir = os.path.join(os.path.dirname(basedir), 'JPG')
    _info("mini-converter v0.2-functional (FFMPEG)")
    _info("checking files in : {0}\n\n".format(basedir))

    # you can set a flag so that you don't overwrite (safe mode..)
    overwrite = False
    overwrite_flag = '-n'
    try:
        if sys.argv[2] == 'overwrite':
            _info("OVERWRITING")
            overwrite = True
            overwrite_flag = '-y'
    except:
        pass

    # we're going to allow multi-threaded spawning, this is default set to 4
    # but can be overidden as part of the command string.
    spawn = spawn_instances

    spawn_slots = []
    for x in range(0, spawn):
        spawn_slots.append(None)
    _info("Allowing {0} spawn slots".format(spawn))

    try:
        os.makedirs(targetdir)
        exists = False
    except:
        exists = True


    skipped = 0
    processed = 0

    _info("starting processing")
    candidates = [x for x in sorted(os.listdir(basedir))
                  if x.split('.')[-1].lower() in accepted]

    for idx, file in enumerate(candidates):
        newfile = '.'.join(file.split('.')[0:-1] + ['jpg'])

        # fire off the conversion command
        src = os.path.join(basedir, file)
        dest = os.path.join(targetdir, newfile)
        if os.path.exists(dest) and not overwrite:
            _info("skipping\n{dest}\n".format(dest=dest))
            skipped += 1
        else:
            _launch([x.format(ffmpeg=executable, quality=quality,
                              loglevel=loglevel, overwrite_flag=overwrite_flag,
                              infile=src, outfile=dest) for x in execstring],
                    spawn_slots)

            _info("converting\n{src} ---> {dest}\n".format(src=src, dest=dest))
            processed += 1

    _info("waiting for conversion to finish")
    _cleanup(spawn_slots)
    _info("done!")
    _info("{0} skipped, {1} processed".format(skipped, processed))
    _info("overwrite: {0}".format(overwrite))
    _info("targetdir: {0}".format(targetdir))
    _info("using: {0}".format(binary))


# convert_dir(r'H:\shots\BUZ\BUZ_020\input\029-G-002G\dpx',spawn_instances=32)
