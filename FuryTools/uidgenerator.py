import sqlite3
from datetime import datetime


'''
db structure creation.

All we have is an autonumber field, which is the rowid.

Need some kind of way to ident a job because in future we may need to support farm splits
Ideally, a nuke job will internally (BEFORE SUBMISSION) request a UID 

Table should look like this:

CREATE TABLE di_uid    (script_name text, date_requested date)"

the rowid is an implicit field that SQLite packs in for you, with subsequent inserts incrementing 
from the rowid number

2013-05-17-AT: pushed live to the tools prod server. in use by nuke now.
'''

# some hashdefs
POSTVIS = 0b10101010
FURYFX = 0b01010101

vendor_digits = 2
shot_digits = 6
vendor_index = {'50': 'DI_Complex_Opticals',
                '60': 'PostVis',
                '70': 'FuryFx',
                '80': 'Method',
                '90': 'Method-Illoura',
                '31': 'TESTING-PLACEHOLDER-AT',
                '34': 'TESTING-PLACEHOLDER-AB',
                '36': 'TESTING-PLACEHOLDER-Myrtle',
                '35': 'TESTING-PLACEHOLDER-Random', }


di_uid_tablefile = {}

#di_uid_tablefile[POSTVIS] = r'//vfx/fury/user/anthony.tan/development/di_uid_60000000.sqlite'
#di_uid_tablefile[FURYFX] = r'//vfx/fury/user/anthony.tan/development/di_uid_70000000.sqlite'

di_uid_tablefile[POSTVIS] = r'\\vfx\fury\production\assetManager\UID\di_uid_60000000.sqlite'
di_uid_tablefile[FURYFX] = r'\\vfx\fury\production\assetManager\UID\di_uid_70000000.sqlite'


drop_string = r"DROP TABLE di_uid"
create_string = r"CREATE TABLE di_uid    (script_name text, date_requested date)"
init_string = r"INSERT INTO di_uid(rowid, script_name, date_requested) VALUES (?, 'initialisation_script_placeholder',?)"
insert_string = r"INSERT INTO di_uid( script_name, date_requested) VALUES (?,?)"
get_string = r"SELECT rowid FROM di_uid WHERE script_name = ? AND date_requested = ? ORDER BY rowid DESC LIMIT 1"
fetch_string = r"SELECT rowid, script_name, date_requested FROM di_uid "

# each retry roughly corresponds to 5 seconds..
max_retries = 3


def initialise_di_uid_generator(which_db, startcode=None):
    '''starts our UID generator by creating the sqlite3 db and padding the 
    first row with a dummy init entry. We're taking advantage of the SQLite 
    behaviour

    Yes. This name is delibrately long and convoluted. You shouldn't be
    doing an init very often..
    '''

    if startcode == None:
        if which_db == POSTVIS:
            startcode = '60000000'
        elif which_db == FURYFX:
            startcode = '70000000'
        else:
            raise ValueError('db needs to be one of POSTVIS or FURYFX')

    date_requested = str(datetime.now())
    with sqlite3.connect(di_uid_tablefile[which_db]) as db_conn:
        db_cursor = db_conn.cursor()

        try:
            db_cursor.execute(drop_string)
        except sqlite3.OperationalError:
            pass

        db_cursor.execute("VACUUM")
        db_cursor.execute(create_string)
        db_cursor.execute(init_string, [startcode, date_requested])
        db_conn.commit()


# it's a lookup table that checks your first two digits
# does not raise errors if your code is too shot
def uid_to_vendor(uidcode):
    '''convienience function to translate a uid code into a vendor name. 

    Will raise TypeError if the UID code is too short or an int but will 
    NOT raise an error if it's an unknown vendor anticipating the day when
    we need to put in new vendors but don't have time to patch the file.
    '''
    try:
        if len(uidcode) < (vendor_digits + shot_digits):
            raise AttributeError
    except TypeError:
        raise TypeError("UID code specified must be string, not integer")
    except AttributeError:
        raise TypeError("UID code wrong length (must be {length} characters)".format(length=vendor_digits + shot_digits))
    try:
        ven_code = uidcode[0:vendor_digits]
        return vendor_index[ven_code]
    except KeyError:
        return 'Unknown Vendor'


def request(which_db, script_name=r'path\to\nuke\script\and\filename.nk'):
    '''requests a uid code by inserting a new row into the database and then
    reading it straight out, but checking the rowid field. This is a sqlite3
    specific implementation however so if we port this to MySQL or Postgres 
    it's not going to be a trivial switchover.

    argv[0] must be one of FuryTools.uidgenerator.POSTVIS or FURYFX 

    Note as well, minor updates to the SQL required if you're going to use
    the additional fields for script name

    (the concept should work fine though)
    '''
    retry = 0
    date_requested = str(datetime.now())
    if which_db == POSTVIS or which_db == FURYFX:
        pass
    else:
        raise ValueError('db needs to be one of POSTVIS or FURYFX')

    while(retry < max_retries):
        try:
            with sqlite3.connect(di_uid_tablefile[which_db]) as db_conn:
                db_cursor = db_conn.cursor()
                db_cursor.execute(insert_string, [script_name, date_requested])
                db_conn.commit()
                db_cursor.execute(get_string, [script_name, date_requested])
                result = db_cursor.fetchone()
            return result[0]

        except sqlite3.IntegrityError:
            db_conn.close()
            return None

        # database is locked - try one more time.
        # this will also be a problem if the db isn't initialised, but
        # we can't protect for everything..
        except sqlite3.OperationalError:
            retry += 1
            pass

    db_conn.close()


def fetchAll(*args, **kwargs):
    ''' fetch all used UIDs from the database specified. Convienience dump
    function

    in pref order *args[0] > kwargs['db']

    '''

    this_fetch_string = fetch_string + " ORDER BY rowid DESC"

    if len(args) > 0:
        which_db = args[0]
    else:
        raise ValueError('either a code or a database must be set. Try uidgen.POSTVIS or uidgen.FURYFX')

    if which_db == POSTVIS or which_db == FURYFX:
        pass
    else:
        try:
            if kwargs['db'] == POSTVIS:
                which_db = POSTVIS
            elif kwargs['db'] == FURYFX:
                which_db = FURYFX
            else:
                raise ValueError('db needs to be one of POSTVIS or FURYFX, or your code needs to be from the 60000000 or 70000000 series')
        except:
            raise ValueError('db needs to be one of POSTVIS or FURYFX, or your code needs to be from the 60000000 or 70000000 series')

    print "I'd be fetching using query string: {0}".format(fetch_string)
    try:
        with sqlite3.connect(di_uid_tablefile[which_db]) as db_conn:
            db_cursor = db_conn.cursor()
            db_cursor.execute(this_fetch_string)
            result = db_cursor.fetchall()
        return result
    except:
        db_conn.close()
        raise

def fetch(*args, **kwargs):
    ''' fetches one or more rows based on a provided key. If supplied as 
    an arg (e.g. fetch(1234123)) treats it as a UID. If you want something
    other than UID, supply it as a kwarg (e.g. fetch(script_name = 32000000))

    in pref order *args[0] > uid > script_name
    '''

    key = None

    this_fetch_string = fetch_string

    # assume the first one could be a POSTVIS or FURYFX ident
    # or just a straight string
    if len(args) > 0:
        which_db = args[0]
    else:
        raise ValueError('either a code or a database must be set. Try uidgen.POSTVIS or uidgen.FURYFX')

    if which_db == POSTVIS or which_db == FURYFX:
        pass
    else:
        if uid_to_vendor(str(which_db)) == uid_to_vendor('60000000'):
            which_db = POSTVIS
        elif uid_to_vendor(str(which_db)) == uid_to_vendor('70000000'):
            which_db = FURYFX
        else:
            raise ValueError('db needs to be one of POSTVIS or FURYFX, or your code needs to be from the 60000000 or 70000000 series')

    if len(args) > 0:
        key = 'uid'
        this_fetch_string += "WHERE rowid = ?"
        kwargs[key] = args[0]

    elif 'uid' in kwargs:
        key = 'uid'
        this_fetch_string += "WHERE rowid = ?"

    elif 'script_name' in kwargs:
        key = 'script_name'
        this_fetch_string += "WHERE script_name = ?"
    elif len(args) == 0:
        this_fetch_string += "ORDER BY rowid DESC LIMIT 1"
        # no appending a WHERE clause so you get the latest
        pass
    else:
        return None

    try:
        with sqlite3.connect(di_uid_tablefile[which_db]) as db_conn:
            db_cursor = db_conn.cursor()
            if key is not None:
                db_cursor.execute(this_fetch_string, [kwargs[key]])
            else:
                db_cursor.execute(this_fetch_string)
            result = db_cursor.fetchall()
        return result
    except:
        db_conn.close()
        raise
