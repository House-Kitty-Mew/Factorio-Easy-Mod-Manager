# import the library
import difflib
import pickle
import zlib
import datetime
from appJar import gui
import json
from pathlib import Path
import os
import urllib.request
from time import sleep
import sqlite3
from sqlite3 import Error
import requests
from os import listdir
from os.path import isfile, join
import re
from os.path import exists
from zipfile import ZipFile
import base64

global debug_mode
debug_mode = 0
global busy
busy = 0
global busy_tmp
busy_tmp = 0

def debugme(msg, option = 0):
    if option == 1:
        print(msg)


def convertToBinaryData(filename):
    # Convert digital data to binary format
    try:
        with open(filename, 'rb') as file:
            blobData = file.read()
    except:
        return False
    return blobData

def insertBLOB(modname, modfilename, modversion, olddate = 0, quick_update = 0):
    sqliteConnection = sqlite3.connect('./mod-manager.db3')
    sql = 'CREATE TABLE IF NOT EXISTS "mods" ("mod_filename" TEXT NOT NULL UNIQUE, "mod_name" TEXT NOT NULL, "version" TEXT NOT NULL, "data_blob" BLOB NOT NULL)'
    cursor = sqliteConnection.cursor()
    cursor.execute(sql)
    sqliteConnection.commit()

    if quick_update == 1:
        pathing = './' + modfilename
        mod_data_blob = convertToBinaryData(pathing)
        cursor.execute('UPDATE mods SET data_blob = ? WHERE mod_filename = ?', (mod_data_blob, modfilename))
        sqliteConnection.commit()
        cursor.close()
        return False


    sqlite_insert_blob_query = "INSERT INTO mods (mod_filename, mod_name, version, data_blob) VALUES (?, ?, ?, ?)"

    cursor.execute('SELECT mod_filename FROM mods WHERE mod_filename = ?', (modfilename,))
    checker = cursor.fetchone()
    if checker != None:
        return False

    if olddate == 1:
        pathing = str(Path.home()) + r'\Appdata\roaming\Factorio\mods' + "\\" + modfilename
        mod_data_blob = convertToBinaryData(pathing)
    else:
        mod_data_blob = convertToBinaryData('./' + modfilename)
    # Convert data into tuple format
    data_tuple = (modfilename, modname, modversion, mod_data_blob)
    cursor.execute(sqlite_insert_blob_query, data_tuple)
    sqliteConnection.commit()
    cursor.close()


def get_hundred_percent(a, b):
    try:
        reply = round((a / b) * 100)
    except:
        reply = 0
    return reply

def add_table_data(name, enable, sleeping, modcount):
    sleep(sleeping)
    offline_mode_check = app.getCheckBox('Offline Mode')
    if offline_mode_check == True:
        status = 'Offline Mode'
    else:
        try:
            clean_name = name.replace(' ', '_')
            print(clean_name + ' is clean')
            status = get_mod_info_json(clean_name)
        except:
            status = '404'
    app.queueFunction(app.addTableRow, 'g1', [name, enable, status])
    progress_amount = get_hundred_percent(sleeping, modcount)
    app.queueFunction(app.setMeter, 'progress', progress_amount)

def get_mod_info_json(name, reply = 0):
    latest = []
    final_version = [0, 0]
    new_name = name.replace(' ', '_')
    with urllib.request.urlopen('https://mods.factorio.com/api/mods/' + new_name + '/full') as url:
        mod_info_raw = json.loads(url.read().decode())

    for mod_releases in mod_info_raw['releases']:

        latest.append(mod_releases['version'])
    if latest == []:
        return 'local'
    updated_release_count = len(latest) - 1
    old_release_count = updated_release_count - 2

    final_version[0] = latest[updated_release_count]
    if len(latest) > 1:
        final_version[1] = latest[old_release_count]


    main_mods_path = str(Path.home()) + r'\AppData\Roaming\Factorio\mods'


    for (root, dirs, files) in os.walk(main_mods_path):
        updated = 0
        # iterate over all the files in the folders and sub folders
        for file in files:
            # read the file from thing and write the file in example
            if name == 'base':
                continue
            updated_mod_name = new_name + '_' + final_version[0] + '.zip'
            download_url = mod_releases['download_url']
            reply_data = [updated_mod_name, download_url]

            if updated_mod_name == file:
                updated = 1

    if updated == 1:
        return 'ok'
    elif updated == 0:
        insertBLOB(name, name + '_' + final_version[0] + '.zip', final_version[0], 1)
        if reply == 1:
            return reply_data
        return 'UPDATE'
    else:
        return 'local'


global home

if os.name == 'nt':
    home = str(Path.home()) + r'\AppData\Roaming\Factorio\mods\mod-list.json'

#define functions
def save_table():
    if app.getCheckBox('Confirmation') == False:
        return False
    tmp_dic = {'mods': [],}
    row_count = app.getTableRowCount('g1')
    tmp_count = 0
    while tmp_count < row_count:
        tmp_1 = app.getTableRow('g1', tmp_count)

        if int(tmp_1[1]) == 0:
            tmp_row_dic = {'name': tmp_1[0], 'enabled': False}
        else:
            tmp_row_dic = {'name': tmp_1[0], 'enabled': True}

        tmp_dic['mods'].append(tmp_row_dic)
        tmp_count += 1
    with open(home, 'w') as f:
        json.dump(tmp_dic, f)
    app.setCheckBox('Confirmation', ticked=False)

def return_load_button_timer(sleep_count):
    sleep(sleep_count)
    app.queueFunction(app.enableButton, 'Load Mods')
    app.queueFunction(app.enableButton, 'Save Mods')

def return_load_button(sleep_count):
    app.thread(return_load_button_timer, sleep_count)


def load_player_login_info():
    player_data_path = str(Path.home()) + r'\AppData\Roaming\Factorio\player-data.json'
    f = open(player_data_path, )
    data = json.load(f)
    reply = [data['service-username'], data['service-token']]
    return reply

def load_mods(b):
    global busy
    login_info = load_player_login_info()
    app.setEntry('Username:', login_info[0])
    app.setEntry('Token:', str(login_info[1]))
    app.setEntryValid('Username:')
    app.setEntryValid('Token:')
    #app.setEntry('Username:', 'Mod Updates Need Username.')
    #app.setEntryInvalid('Username:')
    #app.setEntry('Token:', 'Mod Updates Need (Player) Token')
    #app.setEntryInvalid('Token:')

    try:
        f = open(app.getEntry('filepath'), )
        app.setEntryValid('filepath')
    except:
        app.setEntryInvalid('filepath')
        return False
    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Iterating through the json
    # list
    tmp_mod_count = app.getTableRowCount('g1')
    if int(tmp_mod_count) >= 1:
        app.deleteAllTableRows('g1')
        return False
    sleep_count = 1
    progress_loading_mods_list = len(data['mods']) - 1
    app.thread(load_all_mods)
    for i in data['mods']:
        try:
            app.thread(add_table_data, i['name'], i['enabled'], sleep_count, progress_loading_mods_list)
            sleep_count += 1
        except:
            continue
    busy = sleep_count
    #app.queueFunction(return_load_button, sleep_count)



    # Closing file
    f.close()

    return True

def load_all_mods():
    pathing = str(Path.home()) + r'\Appdata\roaming\Factorio\mods' + "\\"
    onlyfiles = [f for f in listdir(pathing) if isfile(join(pathing, f))]
    count = 0
    for mod in onlyfiles:
        if mod == '':
            continue
        elif mod == 'mod-settings.dat':
            continue
        elif mod == 'mod-list.json':
            continue
        elif mod == '`':
            continue
        else:
            app.queueFunction(app.setEntry, 'Update Info', 'BU: ' + mod)
            try:
                insertBLOB('LocalBackup', mod, '0.0.0', 1)
                count += 1
            except:
                tried = 1

    app.queueFunction(app.setEntry, 'Update Info', 'Backed Up Mods')

def download_mod(data):
    app.queueFunction(app.setEntry, 'Update Info', 'Updating ' + data[1] + '...')
    app.queueFunction(app.setEntryWaitingValidation, 'Update Info')

    r = requests.get(data[0], allow_redirects=True, headers=data[2])  # to get content after redirection
    with open('./' + data[1], 'wb') as f:
        f.write(r.content)

    file_version = data[1].split('_')
    file_version_clean = file_version[1].strip('.zip')
    insertBLOB(data[3], data[1], file_version_clean)

    old_mod_row = app.getTableRow('g1', data[4])

    sqliteConnection = sqlite3.connect('./mod-manager.db3')
    sql = 'CREATE TABLE IF NOT EXISTS "mods" ("mod_filename" TEXT NOT NULL UNIQUE, "mod_name" TEXT NOT NULL, "version" TEXT NOT NULL, "data_blob" BLOB NOT NULL)'
    cursor = sqliteConnection.cursor()
    cursor.execute(sql)
    sqliteConnection.commit()

    pathing = str(Path.home()) + r'\Appdata\roaming\Factorio\mods'
    onlyfiles = [f for f in listdir(pathing) if isfile(join(pathing, f))]


    cursor.execute('SELECT version FROM mods WHERE mod_name = ?', (old_mod_row[0],))
    checker = cursor.fetchall()
    for mod_version in checker:

        old_mod_complete_name = old_mod_row[0] + '_' + mod_version[0] + '.zip'

        for file in onlyfiles:
            if file == old_mod_complete_name:
                delete_path = str(Path.home()) + r'\Appdata\roaming\Factorio\mods' + "\\" + old_mod_complete_name
                os.remove(delete_path)
                app.queueFunction(app.deleteTableRow, 'g1', data[4])
                app.queueFunction(app.addTableRow, 'g1', [data[3], data[1], 1])

    #for mod in onlyfiles:

    if app.getEntry('Update Info') == 'Failed DB Insert!':
        return False
    app.queueFunction(app.setEntryValid, 'Update Info')
    app.queueFunction(app.setEntry, 'Update Info', data[1] + 'Updated!')

def change_mod_activation(row_id):
    delete_mode = app.getCheckBox('Action Mode: Delete')
    if delete_mode == True:
        remove_mod(row_id)
        return True
    tmp = app.getTableRow('g1', row_id)

    update_mod_check = app.getCheckBox('Action Mode: Update Mod')
    offline_update_check = app.getCheckBox('Offline Mode')
    if update_mod_check == True:
        if offline_update_check == True:
            return False
        else:
            check_mod_updates = get_mod_info_json(tmp[0], 1)
            if check_mod_updates == 'ok':
                app.setEntryWaitingValidation('Update Info')
                app.setEntry('Update Info', 'Mod Current! ' + tmp[0])
            elif check_mod_updates == 'local':
                return False
            else:
                download_url = 'https://mods.factorio.com' + check_mod_updates[1] + '?username=' + app.getEntry('Username:') + '&token=' + app.getEntry('Token:')
                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
                mod_data = [download_url, check_mod_updates[0], headers, tmp[0], row_id]
                app.thread(download_mod, mod_data)

    if row_id == 0:
        return False
    if int(tmp[1]) == 1:
        tmp[1] = 0
        app.replaceTableRow('g1', row_id, tmp)
    else:
        tmp[1] = 1
        app.replaceTableRow('g1', row_id, tmp)

def add_mod(b):
    mod_name = app.getEntry('modname')
    if len(mod_name) < 3:
        return False
    app.addTableRow('g1', [mod_name, 1, 'Fresh'])

def remove_mod(modID):
    if modID <= 0:
        return False
    app.deleteTableRow('g1', modID)

def show_archives(b):
    app.showSubWindow('Archives', hide=False)
    app.thread(run_db_listing)

def run_db_listing():
    app.queueFunction(app.setEntry, 'Archive Info', 'Preloading List...')
    sqliteConnection = sqlite3.connect('./mod-manager.db3')
    sql = 'CREATE TABLE IF NOT EXISTS "mods" ("mod_filename" TEXT NOT NULL UNIQUE, "mod_name" TEXT NOT NULL, "version" TEXT NOT NULL, "data_blob" BLOB NOT NULL)'
    cursor = sqliteConnection.cursor()
    cursor.execute(sql)
    sqliteConnection.commit()

    sql = 'SELECT mod_name, mod_filename, version FROM mods'
    cursor.execute(sql)
    db_list = cursor.fetchall()
    path_string = r"\AppData\roaming\Factorio\mods"
    check_rows = app.getTableRowCount('Archives')
    if check_rows > 0:
        #app.queueFunction(app.deleteAllTableRows, 'Archives')
        app.queueFunction(app.setEntry, 'Archive Info', 'Removed Stale Data')



    tmp_cache = []
    for i in db_list:
        if exists(str(Path.home()) + path_string + "\\" + i[1]):
            tmp_cache.append([i[0], i[1], i[2], 'Yes' ])
        else:
            tmp_cache.append([i[0], i[1], i[2], 'No'])

    app.queueFunction(app.replaceAllTableRows, 'Archives', tmp_cache, deleteHeader=False)
    app.queueFunction(app.setEntry, 'Archive Info', 'Finished Loading')

def writeTofile(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)

def readBlobData(row_id):
    global player_username
    global player_token
    debugme('Setup Globals player_username and player_token')
    app.setEntry('Archive Info', 'Installing Mod...')
    app.setEntryWaitingValidation('Archive Info')
    app.queueFunction(app.setEntry, 'Archive Info', 'Installing mods...')

    sqliteConnection = sqlite3.connect('./mod-manager.db3')
    cursor = sqliteConnection.cursor()
    debugme('Setup db and connecting cursor')

    mod_row_info = app.getTableRow('Archives', row_id)
    debugme('Grabbing mod info from the Archives tables with row_id ' + str(row_id))

    sql_fetch_blob_query = "SELECT data_blob from mods where mod_filename = ?"
    cursor.execute(sql_fetch_blob_query, (mod_row_info[1],))
    debugme('Selecting the binary Data stored in the DB using the mods filename of ' + mod_row_info[1])

    record = cursor.fetchone()[0]
    debugme('Now shove the result from the cursor into our own object')

    if record == 0:
        debugme('Turns out the record either didnt get saved right or code error, were gonna try to redownload newest version for use')

        mod_info = get_mod_info_json(mod_row_info[0], 1)
        debugme('Grabbing the mod info from over the internet using the function get_mod_info_json and it used the name ' + mod_row_info[0])

        tmp_name = mod_info[1]
        debugme('shove result from old data source to new object with mod_info[1]=' + mod_info[1])

        sql = 'DELETE FROM mods WHERE mod_filename = ?'
        debugme('Setup sql to remove the entry from db')

        data_tmp = (tmp_name,)
        debugme('Issues with inputing some types of names, so chose to shove into a tupe first with data ' + str(data_tmp))

        cursor.execute(sql, data_tmp)
        debugme('Run the sql command')

        sqliteConnection.commit()
        debugme('Now save changes to database')
        app.queueFunction(app.deleteTableRow, 'Archives', row_id)
        app.queueFunction(app.addTableRow, 'Archives', [mod_row_info[0], mod_row_info[1], mod_row_info[2], 'New'])
        tmp_player_info = load_player_login_info()
        download_url = 'https://mods.factorio.com' + tmp_name + '?username=' +tmp_player_info[0] + '&token=' + tmp_player_info[1]

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        r = requests.get(download_url, allow_redirects=True, headers=headers)  # to get content after redirection
        with open('./' + mod_info[0], 'wb') as f:
            f.write(r.content)
        insertBLOB(mod_row_info[0], mod_info[0], 0, 0, 1)
        app.queueFunction(app.setEntry, 'Archive Info', 'Download & Install Done')
        record = convertToBinaryData('./' + mod_info[0])
        os.remove('./' + mod_info[0])

    pathing = str(Path.home()) + r'\Appdata\roaming\Factorio\mods' + "\\"
    onlyfiles = [f for f in listdir(pathing) if isfile(join(pathing, f))]
    reply_final_check = difflib.get_close_matches(mod_row_info[1], onlyfiles)
    #TODO setup windopane to remove old mod
    if reply_final_check != []:

        for i in reply_final_check:
            if i != mod_row_info[1]:
                app.queueFunction(app.showSubWindow, 'OldModFound')
                app.queueFunction(app.addTableRow, 'oldmods', [i, pathing+i])

    path = str(Path.home()) + r'\AppData\roaming\Factorio\mods' + "\\" + mod_row_info[1]
    writeTofile(record, path)
    cursor.close()

    app.queueFunction(app.replaceTableRow, 'Archives', row_id, [mod_row_info[0], mod_row_info[1], mod_row_info[2], 'Yes'])
    app.queueFunction(app.setEntry, 'Archive Info', 'Mod Installed!')
    app.queueFunction(app.setEntryValid, 'Archive Info')

def archive_button(row_id):
    if app.getCheckBox('Install'):
        if app.getCheckBox('Remove Archive'):
            return False
        app.setEntry('Archive Info', 'Installing Mod...')
        app.thread(readBlobData, row_id)
    elif app.getCheckBox('Remove Archive'):
        print(row_id)
        filename = app.getTableRow('Archives', row_id)
        app.deleteTableRow('Archives', row_id)
        sqliteConnection = sqlite3.connect('./mod-manager.db3')
        sql = 'CREATE TABLE IF NOT EXISTS "mods" ("mod_filename" TEXT NOT NULL UNIQUE, "mod_name" TEXT NOT NULL, "version" TEXT NOT NULL, "data_blob" BLOB NOT NULL)'
        cursor = sqliteConnection.cursor()
        cursor.execute(sql)
        sqliteConnection.commit()
        sql = 'DELETE FROM mods WHERE mod_filename = ?'
        data = (row_id,)
        cursor.execute(sql, data)
        sqliteConnection.commit()
        cursor.close()
        pathing = str(Path.home()) + r'\Appdata\roaming\Factorio\mods' + "\\" + filename[1]
        try:
            os.remove(pathing)
        except:
            app.setEntry('Update Info', 'Failed remove Archive Mod!')
        app.setEntry('Archive Info', 'Removed Mod!')
        app.setEntryValid('Archive Info')


    return False

def close_archive(b):
    app.hideSubWindow('Archives')

def busy_app():
    global busy
    global busy_tmp
    if busy == -1:
        app.disableButton('Load Mods')
        app.disableButton('Save Mods')
        app.disableButton('Archives')
        app.disableButton('Add Mod')
        busy = 0
    elif busy == -2:
        app.enableButton('Load Mods')
        app.enableButton('Save Mods')
        app.enableButton('Archives')
        app.enableButton('Add Mod')
        busy = 0
    elif busy > 0:
        busy_tmp = busy * 4
        busy = -1

    if busy_tmp > 0:
        if busy_tmp == 1:
            busy = -2
            busy_tmp = 0
        elif busy_tmp > 1:
            busy_tmp -= 1

def delete_old_mod(row_id):
    oldmodstabledata = app.getTableRow('oldmods', row_id)
    os.remove(oldmodstabledata[1])
    app.deleteAllTableRows('oldmods')
    app.hideSubWindow('OldModFound')

def clear_old_mods_list(b):
    app.queueFunction(app.deleteAllTableRows('oldmods'))

def GearHash(plain_text: str) -> int:
    r = zlib.adler32(str.encode('UTF-8'))
    return r


def slot_work(row_id):
    if( app.getCheckBox('Overwrite Current mod-list.json') == True and app.getCheckBox('Save Current mod-list.json') == True):
        return False

    sqliteConnection = sqlite3.connect('./mod-manager.db3')
    sql = 'CREATE TABLE IF NOT EXISTS "save_slots" ("name" TEXT NOT NULL, "current_date" TEXT NOT NULL, "save_blob" TEXT NOT NULL)'
    cursor = sqliteConnection.cursor()
    cursor.execute(sql)
    sqliteConnection.commit()

    player_data_path = str(Path.home()) + r'\Appdata\Roaming\Factorio\mods\mod-list.json'

    if row_id == 'Action':
        sql = 'SELECT name,current_date FROM save_slots'
        cursor.execute(sql)
        raw_out = cursor.fetchall()
        if raw_out != []:
            app.queueFunction(app.replaceAllTableRows, 'save_slots', raw_out, deleteHeader=False)

    if app.getCheckBox('Overwrite Current mod-list.json'):
        #TODO fix this fucking broken ass shit
        app.setEntry('Update Info', 'Overwrite WIP')
        app.setEntryInvalid('Update Info')
        return False

        if row_id == 'Action':
            return False

        tmp_data = app.getTableRow('save_slots', row_id)
        print(tmp_data[1])
        cursor.execute('SELECT save_blob FROM save_slots WHERE current_date = ?', (tmp_data[1], ))
        raw_blob = cursor.fetchone()[0]
        print(raw_blob)

       # writeTofile(raw_file, './test.json' )#player_data_path)
        #app.setEntry('Update Info', 'File Was Overwritten!')


    if app.getCheckBox('Save Current mod-list.json'):


        data = open(player_data_path, "r").read()
        tmp = load_player_login_info()

        #hasing the playername, wanted privacy so left out saving any idenifying means
        player_hash = GearHash(tmp[0])
        current_time = datetime.datetime.now()

        cursor.execute('INSERT INTO save_slots VALUES (?, ?, ?)', (player_hash, current_time, data))
        sqliteConnection.commit()
        cursor.close()
        app.queueFunction(app.addTableRow, 'save_slots', [player_hash, current_time])




# create a GUI variable called app
app = gui()


app.startFrame("LEFT", row=0, column=0)

app.startToggleFrame("Options", 0, 0)

app.addValidationEntry('filepath')
app.setEntry('filepath', home)

app.addLabelValidationEntry('Username:')
app.addLabelValidationEntry('Token:')

app.addCheckBox('Action Mode: Delete')
app.addCheckBox('Action Mode: Update Mod')
app.addCheckBox('Offline Mode')

app.stopToggleFrame()

app.addButton('Load Mods', load_mods)

app.stopFrame()


app.addTable("g1",[["Name", "Enabled", 'Updated'],], 0, 1, action=change_mod_activation)

app.startToggleFrame('Save Menu')
app.addButton('Save Mods', save_table, 1, 0)
app.addCheckBox('Confirmation')
app.stopToggleFrame()

app.addHorizontalSeparator(2,0,4, colour="black")

app.addButton('Archives', show_archives, 3, 0)
app.addMeter('progress', 3, 1)

app.addButton('Add Mod', add_mod, 4, 0)
app.addEntry('modname', 4, 1)

app.addHorizontalSeparator(7, 0, 5)

app.addLabelValidationEntry('Update Info', 9, 0)
app.startToggleFrame('Save Slots', 9, 1)
app.addTable('save_slots', [['Name', 'Date'],], action=slot_work)
app.addCheckBox('Overwrite Current mod-list.json')
app.addCheckBox('Save Current mod-list.json')
app.addButton('Action', slot_work)
app.stopToggleFrame()

app.setStretch('both')



app.startSubWindow("Archives", modal=True)
app.addTable('Archives', [['Name', 'File', 'Version', 'Installed'],], 0, 1, 4, 4, action=archive_button)
app.setTableWidth('Archives', 700)
app.startToggleFrame('Archive Options')
app.addCheckBox('Install', 1, 0)
app.addCheckBox('Remove Archive', 2, 0)
app.addCheckBox('Auto Full Reinstall (Disabled by Website ATM)', 3, 0)
app.addButton('Clear OldMods List', clear_old_mods_list)
app.stopToggleFrame()
app.addLabelValidationEntry('Archive Info', 3, 0)
app.addButton('Close Archives', close_archive,  4, 0)
app.setStretch('both')
app.stopSubWindow()


app.startSubWindow("OldModFound", modal=False)
app.addTable('oldmods', [['Filename', 'Path'],], action=delete_old_mod)
app.addLabel('OldModDeleteLabel', 'These are possible Old Versions\n Use the Action button to remove.')
app.setStretch('both')
app.setTableWidth('oldmods', 500)
app.stopSubWindow()



app.registerEvent(busy_app)




# start the GUI
app.go()