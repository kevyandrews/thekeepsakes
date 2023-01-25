"""Setlist generator."""

from PyPDF2 import PdfMerger
import os
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import argparse


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

    argParser = argparse.ArgumentParser()
    argParser.add_argument("-p", "--playlistUrl", help="spotify playlist url")
    argParser.add_argument("-c", "--clientId", help="spotify api client id")
    argParser.add_argument("-s", "--clientSecret", help="spotify api client secret")
    argParser.add_argument("-r", "--repertoire", help="path to repertoire")
    argParser.add_argument("-o", "--outputPath", help="path to output files")


    args = argParser.parse_args()
    print("args=%s" % args)

    # Paste the Spotify playlist link.
    playlist_id = args.playlistUrl

    # Paste the client ID and client secret from https://developer.spotify.com/
    client_id = args.clientId
    client_secret = args.clientSecret

    # Paste the path to the folder containing the sheet music.
    repertoire = args.repertoire

    # Paste the path to the folder where the PDFs should be saved in.
    save_location = args.outputPath

    # Define which instruments to create parts for.
    instruments = ["Drums", "Bass", "Tenor", "Alto", "Trombone", "Keys"]

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
    """Return list of PDF files."""
    pdfs = []
    for song_title in setlist:
        file_to_add = None
        for dir in os.listdir(repertoire):
            if dir in strip_characters(song_title):
                song_dir = os.path.join(repertoire, dir)
                file_to_add = get_instrument_file(song_dir, instrument)
                
                if file_to_add is None and (instrument == "Bass" or instrument == "Keys"):
                    file_to_add = get_instrument_file(song_dir, "chord")
                if file_to_add is None and instrument == "Keys":
                    file_to_add = get_instrument_file(song_dir, "Piano")
                if file_to_add is None and (instrument == "Bass" or instrument == "Keys"):
                    file_to_add = get_instrument_file(song_dir, "rhythm")
                if file_to_add is None and instrument == "Keys":
                    file_to_add = get_instrument_file(song_dir, "Bass")
                
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
    """Return associated instrument part from a song's folder."""
    for file in os.listdir(song_dir):
        if re.search(instrument, file, re.IGNORECASE) and ".pdf" in file:
            path = os.path.join(song_dir, file)
            return path


if __name__ == "__main__":
    main()
