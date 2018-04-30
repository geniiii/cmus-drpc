#!/bin/python3
from discoIPC import ipc
from pydbus import SessionBus

import subprocess
import datetime
import time

from gi.repository.GLib import Error
from os import path
import json

with open('config.json') as json_data:
    config = json.load(json_data)


def update_presence(data: dict):
    if data['paused'] is True or config['timestamp'] == 'off' or config['timestamp'] == 'status':
        timestamp = {}
    else:
        timestamp = {
            'start': int(time.time()),
            'end': int(time.time()) + data['timestamp']
        }

    activity = {
        'details': data['artist_track'],
        'state': data['status_kbps'],
        'timestamps': timestamp,
        'assets': {
            'large_image': 'cmus',
            'small_image': data['icon'],
            'large_text': 'cmus',
            'small_text': data['status']
        }
    }
    return activity


def loop_check(loop: str):
    if loop == 'None':
        loop = None
    elif loop == 'Track':
        loop = 'Looping Track'
    else:
        loop = 'Looping Playlist/Library'
    return loop


def status_string(loop, kbps, status, timestamp):
    stuff = list(filter(None.__ne__, [status, kbps, loop, timestamp]))
    stuff = [str(i) for i in stuff]

    status_kbps = ', '.join(stuff)
    return status_kbps


def song_file_path(file_path: str):
    _, file_name = path.split(file_path)
    track = file_name.rsplit('.', 1)[0]
    return track


def artist_string(artists):
    if len(artists) > 1:
        artist_string = ', '.join(map(str, artists))
    else:
        artist_string = artists[0]
    return artist_string


def main():
    old_data = {}

    client = ipc.DiscordIPC('407579153060331521')
    client.connect()

    bus = SessionBus()

    while True:
        try:
            remote_object = bus.get(
                'org.mpris.MediaPlayer2.cmus',
                '/org/mpris/MediaPlayer2'
            )
        except Error as ex:
            if ex.args[0] == 'GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name org.mpris.MediaPlayer2.cmus was not provided by any .service files':
                print(
                    'cmus is compiled without mpris support or is not running, sleeping for 10s...')
                time.sleep(10)
                continue

        metadata = remote_object.Metadata
        status = remote_object.PlaybackStatus
        if config['loop'] != True:
            loop = loop_check(remote_object.LoopStatus)
        else:
            loop = None

        paused = False
        icon = 'playing'

        timestamp = None

        try:
            position = int(time.time() + remote_object.Position / 1000000)
            if config['timestamp'] == 'status':
                duration = str(datetime.timedelta(
                    microseconds=int(metadata['mpris:length'])))
                position = str(datetime.timedelta(
                    microseconds=int(remote_object.Position)))
            elif status != 'Paused':
                duration = int(
                    time.time() + metadata['mpris:length'] / 1000000)
                timestamp = duration - position
            elif status == 'Paused':
                paused = True
                duration = 0
        except KeyError:
            print('no song is playing or timing failed, sleeping for 5 seconds...')
            time.sleep(5)
            continue

        try:
            if config['kbps'] == False:
                kbps = None
            else:
                kbps = '{} kbps'.format(str(metadata['cmus:bitrate'])[:-3])
        except KeyError:
            print(
                "hey!! your cmus version isn't my fork.. whatever, continuing..")
            kbps = None

        try:
            if config['artist'] == False:
                artist = None
            else:
                artist = artist_string(metadata['xesam:artist'])
        except KeyError:
            artist = '?'

        try:
            track = metadata['xesam:title']
        except KeyError:
            try:  # god has left us
                track = song_file_path(metadata['cmus:file_path'])
            except KeyError:
                track = '?'

        artist_track = '{} - {}'.format(artist, track)
        if config["timestamp"] == "status":
            status_thing = status_string(
                loop, kbps, status, "{}/{}".format(position, duration))
        else:
            status_thing = status_string(loop, kbps, status, None)

        if status == 'Paused':
            icon = 'paused'

        data = {
            'artist_track': artist_track,
            'status_kbps': status_thing,
            'icon': icon,
            'status': status,
            'timestamp': timestamp,
            'paused': paused
        }

        if data != old_data:
            client.update_activity(update_presence(data))
            old_data = data
            time.sleep(15)
        else:
            time.sleep(5)


if __name__ == '__main__':
    main()
