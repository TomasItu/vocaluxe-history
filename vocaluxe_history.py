from typing import Optional, Tuple

import time
from pathlib import Path
from datetime import datetime

import requests


VOCALUXE_SERVER_URL = 'http://localhost'
VOCALUXE_SERVER_PORT = '3000'

API_GET_CURRENT_SONG_ID_URL = 'getCurrentSongId'
API_GET_SONG_DETAILS_URL = 'getSong?songId='

# The frequency to poll the vocaluxe server (in seconds).
POLL_FREQUENCY = 1


# Makes a request to the vocaluxe server.
def request(url: str) -> requests.models.Response:
    request_url = VOCALUXE_SERVER_URL + ':' + VOCALUXE_SERVER_PORT + '/' + url

    response = requests.get(request_url)

    if response.status_code != 200:
        raise ConnectionError('Error contacting the vocaluxe server')

    return response


# Returns the current song or None if no song is playing.
# Songs are formatted as a 3-tuple (songID, songTitle, songArtist).
def getCurrentSong() -> Optional[Tuple[int, str, str]]:
    # Get current song ID from the vocaluxe server.
    response = request(API_GET_CURRENT_SONG_ID_URL)

    currentSongId = int(response.text)

    # When no song is playing vocaluxe will return a -1.
    if currentSongId == -1:
        return None

    # Get current song details from the vocaluxe server.
    song_details_url = API_GET_SONG_DETAILS_URL + str(currentSongId)
    response = request(song_details_url)

    song_data = response.json()

    return (song_data['SongId'], song_data['Title'], song_data['Artist'])


# Main function
def main():
    # Create output folder if it does not exist.
    output_folder = Path('./Vocaluxe History/')
    output_folder.mkdir(exist_ok=True)

    # Create a file to record the history into.
    # History is grouped by date, so the file may already exist.
    history_file = output_folder.joinpath(datetime.now().strftime('%b-%d-%Y') + '.txt')
    history_file.touch(exist_ok=True)

    print('Recording vocaluxe play history...', end='\r')

    # Setup event loop.
    # Script has no formal exit condition, it will either crash when vocaluxe is closed, or be terminated by the user.
    previous_song = (-1, 'NONE', 'NONE')
    timeout_flag = False
    while(True):
        time.sleep(POLL_FREQUENCY)
        try:
            current_song = getCurrentSong()
            if timeout_flag:
                timeout_flag = False
                print('\033[K', end='\r')
                print('Recording vocaluxe play history...', end='\r')
        except requests.exceptions.ConnectionError:
            if not timeout_flag:
                timeout_flag = True
                print('\033[K', end='\r')
                print('Can\'t connect to the vocaluxe server, retrying...', end='\r')
            continue

        # Only log the current song if it is new.
        if current_song and current_song[0] != previous_song[0]:
            # Log data as tab (\t) separated values for use in other programs or scripts.
            log_string = '{0}\t{1}\t{2}\n'.format(datetime.now().strftime('%H:%M:%S'), current_song[1], current_song[2])
            with open(history_file, 'a') as f:
                f.write(log_string)

            previous_song = current_song


if __name__ == '__main__':
    main()
