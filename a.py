#!/bin/python3
from discoIPC import ipc
from pydbus import SessionBus

import subprocess
import datetime
import time

from gi.repository.GLib import Error
from os import path
import json


def update_presence(data: dict):
    if data['timestamp'] is False:
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
        loop = False
    elif loop == 'Track':
        loop = 'Looping Track'
    else:
        loop = 'Looping Playlist'
    return loop


def status_kbps_string(loop, kbps, status):
    stuff = list(filter(None.__ne__, [status, kbps, loop]))
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

        with open('config.json') as json_data:
            config = json.load(json_data)

        metadata = remote_object.Metadata
        status = remote_object.PlaybackStatus
        if config['loop'] == True:
            loop = loop_check(remote_object.LoopStatus)
        else:
            loop = None

        paused = False
        icon = 'playing'
        duration = 0

        try:
            if metadata['mpris:length'] != duration and status != 'Paused':
                duration = int(
                    time.time() + metadata['mpris:length'] / 1000000)
                position = int(time.time() + remote_object.Position / 1000000)
            elif status == 'Paused':
                paused = True
        except KeyError:
            print('no song is playing or timing failed, sleeping for 5 seconds...')
            time.sleep(5)
            continue

        try:
            if config['kbps'] == False:
                kbps = None
                return
            kbps = '{} kbps'.format(str(metadata['cmus:bitrate'])[:-3])
        except KeyError:
            print("hey!! your cmus version isn't my fork!!")

        try:
            if config['artist'] == False:
                artist = None
                return
            artist = artist_string(metadata['xesam:artist'])
        except KeyError:
            artist = '?'

        try:
            track = metadata['xesam:title']
        except KeyError:
            track = song_file_path(metadata['cmus:file_path'])

        artist_track = '{} - {}'.format(artist, track)
        status_kbps = status_kbps_string(loop, kbps, status)

        client = ipc.DiscordIPC('407579153060331521')
        client.connect()

        if status == 'Paused':
            icon = 'paused'

        data = {
            'artist_track': artist_track,
            'status_kbps': status_kbps,
            'icon': icon,
            'status': status,
            'timestamp': duration - position,
            'paused': paused
        }

        client.update_activity(update_presence(data))

        time.sleep(15)


if __name__ == '__main__':
    main()
