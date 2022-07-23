"""Setlist generator"""

from PyPDF2 import PdfMerger
import os
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def main():
    """Combine each instruments' parts into one PDF file for each instrument.

    Notes
    -----
    Uses Spotipy module to interface with Spotify's API. This requires the user
    to sign up for and create an application at https://developer.spotify.com/

    Create a new application, and then copy and paste the client ID and client
    secret into this code. These hardcoded values allow Spotipy to authenticate
    user info without having to define environment variables or log in.

    Copy and paste the Spotify playlist link into the code. The Spotipy module
    returns the song information from the playlist as a dictionary.

    The dictionary is parsed for the track names, which are then searched for
    in the repertoire folder on the local drive of the user. The user must
    define the pathname to this repertoire folder.

    """

    # Paste the Spotify playlist link.
    playlist_id = "https://open.spotify.com/playlist/0G5qU6zKlFRgLe8Y0Vr1Em"

    # Paste the client ID and client secret from https://developer.spotify.com/
    client_id = "d10bfbf0560b4ca3abff165985ef0e12"
    client_secret = "070b6159ab674c30a9c9499f7034828c"

    # Paste the path to the folder containing the sheet music.
    repertoire = "/Users/kevyandrews/My Drive/Repertoire"

    # Paste the path to the folder where the PDFs should be saved in.
    save_location = "/Users/kevyandrews/My Drive/Setlists/0725_AmsterdamBarHall/"

    # Define which instruments to create parts for.
    instruments = ["Drums", "Bass", "Tenor", "Alto", "Trombone"]

    # Returns setlist as list.
    setlist = get_setlist_from_spotify(client_id, client_secret, playlist_id)

    for instrument in instruments:
        pdfs = get_pdf_files(setlist, repertoire, instrument)
        merge_pdfs(pdfs, save_location, instrument)

def merge_pdfs(pdfs, save_location, instrument):
    """Merge multiple PDF files into one PDF file."""

    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(pdf)
    merger.write(save_location + instrument + "_Setlist.pdf")
    merger.close()

def get_pdf_files(setlist, repertoire, instrument):
    """Returns list of PDF files."""

    pdfs = []
    for song_title in setlist:
        file_to_add=None
        for dir in os.listdir(repertoire):
            if dir in strip_characters(song_title):
                song_dir = os.path.join(repertoire, dir)
                file_to_add = get_instrument_file(song_dir, instrument)

                if file_to_add is None and instrument == "Bass":
                    file_to_add = get_instrument_file(song_dir, "chord")
                if file_to_add is None and instrument == "Bass":
                    file_to_add = get_instrument_file(song_dir, "rhythm")
                if file_to_add is None and instrument == "Drums":
                    file_to_add = get_instrument_file(song_dir, "rhythm")
                if file_to_add is not None:
                    pdfs.append(file_to_add)

    return pdfs

def strip_characters(song_title):
    """Strip non-alphanumeric characters, including spaces from song title."""

    return re.sub(r'[^a-zA-Z0-9]', '', song_title)

def get_setlist_from_spotify(client_id, client_secret, playlist_id):
    """Return setlist as list from Spotify playlist link."""

    auth_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    results = sp.playlist_tracks(playlist_id)
    setlist = []

    for item in results['items']:
        print(item['track']['name'])
        setlist.append(item['track']['name'])
    return setlist

def get_instrument_file(song_dir, instrument):
    """Return associated instrument from a song's folder."""

    for file in os.listdir(song_dir):
        if re.search(instrument, file, re.IGNORECASE) and ".pdf" in file:
            path = os.path.join(song_dir, file)
            return path

if __name__ == "__main__":
    main()