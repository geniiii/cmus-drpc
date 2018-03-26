#!/bin/python3
from discoIPC import ipc
from pydbus import SessionBus
from gi.repository.GLib import Error
from os import path

import subprocess
import datetime
import time


def update_presence(details: str, state: str, icon: str, status: str, end: int, pause: bool):
    if pause:
        timestamp = {}
    else:
        timestamp = {
            'start': int(time.time()),
            'end': int(time.time()) + end
        }

    activity = {
        'details': details,
        'state': state,
        'timestamps': timestamp,
        'assets': {
            'large_image': 'cmus',
            'small_image': icon,
            'large_text': 'cmus',
            'small_text': status
        }
    }
    return activity


def main():
    bus = SessionBus()

    while True:
        try:
            remote_object = bus.get(
                "org.mpris.MediaPlayer2.cmus",
                "/org/mpris/MediaPlayer2"
            )
        except Error as ex:
            if ex.args[0] == 'GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name org.mpris.MediaPlayer2.cmus was not provided by any .service files':
                print(
                    "cmus is compiled without mpris support or is not running, sleeping for 10s...")
                time.sleep(10)
                continue

        metadata = remote_object.Metadata
        status = remote_object.PlaybackStatus

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
            print("no song is playing or timing failed. sleeping for 5 seconds...")
            time.sleep(5)
            continue

        try:
            kbps = "{} kbps".format(str(metadata['cmus:bitrate'])[:-3])
            file_path = metadata['cmus:file_path']
        except KeyError:
            print("hey!! your cmus version isn't my fork!!")
            return

        try:
            artists = metadata['xesam:artist']
            if len(artists) > 1:
                artist_string = ", ".join(map(str, artists))
            else:
                artist_string = artists[0]
        except KeyError:
            artist_string = "?"

        try:
            track = metadata['xesam:title']
        except KeyError:
            _, file_name = path.split(file_path)
            track = file_name.rsplit('.', 1)[0]

        artist_track = "{} - {}".format(artist_string, track)

        status_kbps = "{}, {}".format(status, kbps)

        client = ipc.DiscordIPC("407579153060331521")
        client.connect()

        if status == 'Paused':
            icon = 'paused'

        client.update_activity(update_presence(
            artist_track, status_kbps, icon, status, duration - position, paused))

        time.sleep(15)


if __name__ == '__main__':
    main()
