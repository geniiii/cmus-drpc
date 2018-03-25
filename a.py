#!/bin/python3
from discoIPC import ipc
from pydbus import SessionBus
from gi.repository.GLib import Error
from os import path

import subprocess
import datetime
import time


def update_presence(details: str, state: str, icon: str, status: str, end: int):
    activity = {
        'details': details,
        'state': state,
        'timestamps': {
            'start': int(time.time()),
            'end': int(time.time()) + end
        },
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
                print("cmus is compiled without mpris support or is not running")
                return

        metadata = remote_object.Metadata

        duration = metadata['mpris:length']
        position = remote_object.Position

        kbps = "{} kbps".format(str(metadata['cmus:bitrate'])[:-3])

        status = remote_object.PlaybackStatus

        file_path = metadata['cmus:file_path']
        icon = 'playing'

        duration = int(time.time() + duration / 1000000)
        position = int(time.time() + position / 1000000)

        artist_string = ""
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
        #position_duration = "{}/{}, {}".format(position, duration, kbps)
        position_duration = "{}".format(kbps)

        client = ipc.DiscordIPC("407579153060331521")
        client.connect()

        if status == 'Paused':
            icon = 'paused'

        client.update_activity(update_presence(
            artist_track, position_duration, icon, status, duration - position))

        time.sleep(15)


if __name__ == '__main__':
    main()
