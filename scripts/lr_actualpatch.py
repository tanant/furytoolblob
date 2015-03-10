import os
import sys

root = r'H:\user\anthony.tan\development\lightroom_patch'
AgLibraryKeyWordImage = None
AgLibraryFile = r'AgLibraryFile.csv'
AgLibraryKeyword = r'AgLibraryKeyword.csv'
OTCLibraryList = r'FR_OTC_ArchiveLog_From5thKind_2013_02_25-spaceless.csv'

AgPatchOut = r'patchout_6.csv'
os.chdir(root)

import sqlite3
lrcat = r'OTC_files.lrcat'
#lrcat = r'x.lrcat'
conn = sqlite3.connect(lrcat)
#sqlstring = "INSERT INTO AgLibraryKeyWordImage (id_local, image, tag) VALUES (?,?,?)"
sqlstring = r'UPDATE AgLibraryKeywordImage SET tag=? WHERE image = ? AND tag=?'
rowid = 0
with open(AgPatchOut, 'rU') as fin:
    for row in fin:
        data = row.strip().split(',')
        conn.execute(sqlstring, (data[2], data[1], 107491))
        # conn.commit()
        # print "commit row:", data[0]
        rowid += 1
        if (rowid % 100) == 0:
            print rowid


conn.commit()
conn.close()
