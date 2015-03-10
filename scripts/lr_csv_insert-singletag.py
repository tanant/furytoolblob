'''
Created on 26/02/2015

@author: OM005188
'''


import os
import csv
import re


def maketagdict(row):
    tagdict = dict()
    tagdict["PRODUCTION"] = row[0]
    tagdict["COMPANY"] = row[1]
    tagdict["DEPT"] = row[2]
    tagdict["DEPT_CODE"] = row[3]
    tagdict["DEPT_SUB_CODE"] = row[4]
    tagdict["ASSET_TYPE"] = row[5]
    tagdict["INSERT_DATE"] = row[6]
    return tagdict


root = r'H:\user\anthony.tan\development\lightroom_patch'
AgLibraryKeyWordImage = None
AgLibraryFile = r'AgLibraryFile.csv'
AgLibraryKeyword = r'AgLibraryKeyword.csv'
AgLibraryImportImage = r'AgLibraryImportImage.csv'  # oh FFS.
AdobeImages = r'Adobe_images.csv'
OTCLibraryList = r'FR_OTC_ArchiveLog_From5thKind_2013_02_25-spaceless.csv'
AgPatchOut = r'patchout_tag.csv'
os.chdir(root)

keyidx = 6
AgPatchOut = r'patchout' + '_' + str(keyidx) + '.csv'

lr_filecat = dict()
lr_keywords = dict()
lr_translation_table = dict()


# LOAD UP THE LIGHTOOM DATABASE OF FILES TO BE TAGGED
# digest/load and create the things
# the key for this is the uppercase baseName (so NOT the ID code)
with open(AgLibraryFile) as fin:
    library_file = csv.reader(fin)
    library_file.next()  # lazy skip the header
    for row in library_file:
        lr_filecat[row[8]] = row
# note - there are collisions where the key needs to be joined with the extension

'''
# verification that there are keys avail
print len(lr_filecat.keys())
print lr_filecat["002_GM_Max'sStory_FuryRoadasasilentfilm.mp4"]

# luckily, there are no collisions here, so we can use an uppercased name as a unique path.

'''

# develop a translation table between a file and an image. Key is the file. Ident
with open(AdobeImages) as fin:
    library_file = csv.reader(fin)
    library_file.next()  # lazy skip the header
    for row in library_file:
        # if row[11] in lr_keywords.keys():
            # print "Key collision:",
            # print row[11]
        lr_translation_table[row[27]] = row[0]


# LOAD UP THE LIGHTOOM DATABASE OF KEYWORDS
# digest/load and create the things
# the key for this is the uppercase baseName (so NOT the ID code)
with open(AgLibraryKeyword) as fin:
    library_file = csv.reader(fin)
    library_file.next()  # lazy skip the header
    for row in library_file:
        # if row[11] in lr_keywords.keys():
            # print "Key collision:",
            # print row[11]
        lr_keywords[row[0]] = row

lr_keyword_index = dict()
for key, item in lr_keywords.iteritems():
    try:
        lr_keyword_index[item[11]] += [item[0]]
    except KeyError:
        lr_keyword_index[item[11]] = [item[0]]

'''
load the keyword DB using the id_local
build a subsequent index to allow us to glue a key string across 
'''

# print len(lr_keywords)
# print lr_keywords.keys()

'''
there are two "camera test" keywords. parents are 106421 (== DEPT CODE) and 107217 (== ASSET TYPE)
'''

# load up the thing we want to hack out.. later. test first
# "532P_guard1_ST.jpg","Fury Road","Weta","Costumes","Platform Guard","Concepts ARCHIVAL","Concept Art","OTC insert 02-02-2010","/movie_man/files/proxies/acd/acddbf5092a019ce6c03092a0af73e4d.jpg"

autonum = 1
keyerrors = []
# load up the inbound file.


# this takes a file, and does a join between file and tagname
# still needs to take the file and convert to an Image. Which means translation table

with open(OTCLibraryList) as fin:   # data source for reading
    with open(AgPatchOut, "wt") as fout:  # data source for writing
        incoming_file = csv.reader(fin)
        incoming_file.next()  # lazy skip the header
        for row in incoming_file:
            file = row[0]
            tags = maketagdict(row[1:-1])

            try:
                image = lr_filecat[file][0]
                tagids = []

                key = tags.keys()[keyidx]

                # conflict resolution - if there are more than one tag candidates..
                try:
                    if len(lr_keyword_index[tags[key]]) > 1:
                        for conflict in lr_keyword_index[tags[key]]:
                            parent = lr_keywords[conflict][-1]  # thisis the parent
                            if lr_keywords[parent][11] == key:
                                # print "keymatch:", conflict
                                tagids += [conflict]
                            else:
                                # print "nomatch:", conflict
                                pass
                    else:
                        if lr_keyword_index[tags[key]][0] == '21':  # empty tag
                            pass
                        else:
                            tagids += lr_keyword_index[tags[key]]
                except KeyError as e:
                    pass
                    # just skip that borked key

                for x in tagids:
                    fout.write('{autonum},{image},{tag}\n'.format(autonum=autonum, image=lr_translation_table[image], tag=x))
                    autonum += 1

            except KeyError:
                keyerrors += [file]

                '''
                
                if file.endswith('jpg'):
                    pass
                if file.endswith('pdf'):
                    pass
                    
                
                if file.endswith('mov'):
                    print file
                    print key
                    print tags[key]
                    print lr_keyword_index["16 March 2010"]
                    raise
                '''

            # print autonum
            # print image
            # print tagids
            # for x in tagids:
            #    print lr_keywords[x]


print "Key Errors found, manual patch?"
print len(keyerrors)
print keyerrors


'''
row = "532P_guard1_ST.jpg","Fury Road","Weta","Costumes","Platform Guard","Concepts ARCHIVAL","Concept Art","OTC insert 02-02-2010","/movie_man/files/proxies/acd/acddbf5092a019ce6c03092a0af73e4d.jpg".split(',')
file = row[0]
tags = maketagdict(row[1:-1])

autonum = "999"
image = lr_filecat[file][0]
tagids = []

for key in tags:
    #print tags[key] + ":",
    #print lr_keyword_index[tags[key]]
    # conflict resolution - if there are more than one tag candidates..
    if len(lr_keyword_index[tags[key]]) > 1:
        for conflict in lr_keyword_index[tags[key]]:
            parent = lr_keywords[conflict][-1] # thisis the parent
            if lr_keywords[parent][11] == key:
                #print "keymatch:", conflict
                tagids += [conflict]
            else:
                #print "nomatch:", conflict
                pass
    else:
        tagids += lr_keyword_index[tags[key]]

print autonum
print image
print tagids
for x in tagids:
    print lr_keywords[x]
'''

'''
# the input CSV has the following form:
[0]: filename(spaceless)
[1:-1]: tag,tag,tag,tag..

and tags are:
PRODUCTION    COMPANY    DEPT    DEPT CODE    DEPT SUB CODE    ASSET TYPE    INSERT DATE

'''


'''
root = r'H:\user\anthony.tan\development\lightroom_patch'
AgLibraryKeyWordImage = None
AgLibraryFile = r'AgLibraryFile.csv'
AgLibraryKeyword = r'AgLibraryKeyword.csv'
OTCLibraryList = r'FR_OTC_ArchiveLog_From5thKind_2013_02_25-spaceless.csv'

AgPatchOut = r'patchout.csv'
os.chdir(root)

import sqlite3
lrcat = r'OTC_files.lrcat'
conn = sqlite3.connect(lrcat)
sqlstring = "INSERT INTO AgLibraryKeyWordImage (image, tag) VALUES (?,?)"
with open(AgPatchOut) as fin:
    for row in fin:
        conn.execute(sqlstring, row[1], row[2])

conn.close()
'''
