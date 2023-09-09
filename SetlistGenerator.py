"""Setlist generator."""

from PyPDF2 import PdfMerger
from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.generic import RectangleObject
from spotipy.oauth2 import SpotifyClientCredentials
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm, inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


import os
import re
import spotipy
import io
import argparse

pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))

TEMP_DIR ="temp_char_dir"
FONT = "Vera"
PAGE_SIZE = (8.5 * inch, 11 * inch)
COVER_PAGE_INCREMENT = 20
SET_BREAK_SONG_NAME = "--- SET BREAK ---"
TOMS_BASS_STUFF_DIR = "Tom_s Bass Stuff"



class SongPDF:
  def __init__(self, song_name, instrument, file_path):
    self.song_name = song_name
    self.instrument = instrument
    self.file_path = file_path
    self.page_count = get_page_count(file_path)

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
    instruments = ["Drums","CustomBass", "Bass", "Tenor", "Alto", "Trombone", "Keys", "Lyrics"]

    # Returns setlist as list.
    setlist = get_setlist_from_spotify(client_id, client_secret, playlist_id)
    if len(setlist) > 30:
        cover_page_size = (PAGE_SIZE[0], 150 + (len(setlist)*COVER_PAGE_INCREMENT))
    else:
        cover_page_size = PAGE_SIZE

    setlist_name = get_playlist_name(client_id, client_secret, playlist_id)

    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)
    if not os.path.exists(save_location):
        os.mkdir(save_location)
      
    text_packet = create_home_pdf()
    home_page_reader = PdfFileReader(text_packet)
    for instrument in instruments:
        merged_file_name = os.path.join(TEMP_DIR, instrument +'_Merged.pdf')
        song_pdfs = get_pdf_files(setlist, repertoire, instrument)
        cover_pages = create_cover_pages(song_pdfs, instrument, setlist_name, cover_page_size)
        for cover_page in cover_pages:
            song_pdfs.insert(0, cover_page)
        merge_pdfs(song_pdfs, merged_file_name)
        output_path = os.path.join(save_location, instrument + f'_Setlist_{setlist_name}.pdf')
        add_links_to_cover_page(song_pdfs, merged_file_name, output_path, cover_page_size)

def merge_pdfs(song_pdfs: list[SongPDF], save_path):
    """Merge multiple PDF files into one PDF file."""
    merger = PdfMerger()
    for song_pdf in song_pdfs:
        merger.append(song_pdf.file_path)
    merger.write(save_path)
    merger.close()

def get_page_count(file):
    pdf_reader = PdfFileReader(open(file,'rb'))
    return pdf_reader.getNumPages()

def create_home_pdf():
    packet = io.BytesIO()
    can = Canvas(packet)
    can.setFont(FONT, 16)
    can.drawString(4, 4, "Return To Top ^")
    can.save()
    #move to the beginning of the StringIO buffer
    packet.seek(0)
    return packet

def create_cover_pages(song_pdfs: list[SongPDF], instrument, setlist_name, cover_page_size):
    ret_song_pdfs = []
    file_name = os.path.join(TEMP_DIR, "TempCoverPage.pdf")
    # Write text out to pdf file
    canvas = Canvas(file_name)
    canvas.setPageSize(cover_page_size)
    canvas.setFont(FONT, 24)
    canvas.drawString(50, cover_page_size[1]-50, f"{setlist_name} Setlist - {instrument}")
    canvas.setFont(FONT, 14)
    i = cover_page_size[1]-100
    for song_pdf in song_pdfs:
        if song_pdf.song_name == SET_BREAK_SONG_NAME:
            canvas.setFillColorRGB(1,0,0)
        else:
            canvas.setFillColorRGB(0,0,0)
        canvas.drawString(50, i, song_pdf.song_name)
        i-=COVER_PAGE_INCREMENT
    canvas.save()
    ret_song_pdfs.append(SongPDF(song_name="", instrument=instrument, file_path=file_name))
    return ret_song_pdfs

def create_set_break_page():
    file_name = os.path.join(TEMP_DIR, "TempSetBreakPage.pdf")
    # Write text out to pdf file
    canvas = Canvas(file_name)
    canvas.setPageSize(PAGE_SIZE)
    canvas.setFont(FONT, 40)
    canvas.drawString(50, 400, f"SET BREAK")
    canvas.setFont(FONT, 14)
    canvas.save()
    return SongPDF(song_name=SET_BREAK_SONG_NAME, instrument="", file_path=file_name)


def add_links_to_cover_page(song_pdfs: list[SongPDF],input_file_name, output_file_name, cover_page_size):
    # Add clickable links over newly created pdf file
    text_packet = create_home_pdf()
    home_page_reader = PdfFileReader(text_packet)
    pdf_writer = PdfFileWriter()
    pdf_reader = PdfFileReader(open(input_file_name, 'rb'))
    num_of_pages = pdf_reader.getNumPages()

    for page in range(num_of_pages):
        current_page = pdf_reader.getPage(page)
        if page > 0:
            current_page.mergePage(home_page_reader.getPage(0))
        pdf_writer.addPage(current_page)
    
    # Add back to top links
    for i in range(1, num_of_pages):
        pdf_writer.addLink(
            pagenum=i, # index of the page on which to place the link
            pagedest=0, # index of the page to which the link should go
            rect=RectangleObject([2,2,200,30]), # clickable area x1, y1, x2, y2 (starts bottom left corner)
            border=[1, 1, 1]
        )
    i = (cover_page_size[1]-100)+(COVER_PAGE_INCREMENT*.75)
    pages_consumed=1
    # Add links for each song - skip page 1
    for song_pdf in song_pdfs[1:]:
        pdf_writer.addLink(
            pagenum=0, # index of the page on which to place the link
            pagedest=pages_consumed, # index of the page to which the link should go
            rect=RectangleObject([40,i,450,i-COVER_PAGE_INCREMENT]), # clickable area x1, y1, x2, y2 (starts bottom left corner)
            border=[1, 1, 1]
        )
        
        pages_consumed+=song_pdf.page_count
        i-=COVER_PAGE_INCREMENT

    with open(output_file_name, 'wb') as link_pdf:
        pdf_writer.write(link_pdf)
    #os.rename('temp.pdf', file_path)


def create_empty_song_page(song_title, instrument):
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)
    temp_file_name = os.path.join(TEMP_DIR, song_title + "_" + instrument + "_TempChart.pdf")
    canvas = Canvas(temp_file_name)
    canvas.setPageSize(PAGE_SIZE)
    canvas.setFont(FONT, 22)
    canvas.drawString(20, 730.0, song_title + " - " + instrument)
    canvas.setFont(FONT, 14)
    canvas.drawString(20, 700.0, f"This page is intentionally left blank. No matching {instrument} part found :)")
    canvas.save()
    print(f"Did not find appropriate {instrument} chart for {song_title} - creating place holder")
    return temp_file_name

def get_pdf_files(setlist, repertoire, instrument):
    """Return list of PDF files."""
    song_pdfs = []
    for song_title in setlist:
        file_to_add = None
        for dir in os.listdir(repertoire):
            if strip_characters(dir.lower()) in strip_characters(song_title.lower()):
                song_dir = os.path.join(repertoire, dir)

                if instrument == "CustomBass":
                    # Prioritize Tom's bass stuff
                    if file_to_add is None and (instrument == "CustomBass"):
                        file_to_add = get_instrument_file(os.path.join(repertoire, TOMS_BASS_STUFF_DIR), strip_characters(song_title.lower()))
                    if file_to_add is None:
                        file_to_add = get_instrument_file(song_dir, "Bass")

                # Main case
                if file_to_add is None:
                    file_to_add = get_instrument_file(song_dir, instrument)
                
                if file_to_add is None and (instrument == "Bass" or instrument == "CustomBass" or instrument == "Keys"):
                    file_to_add = get_instrument_file(song_dir, "chord")
                if file_to_add is None and instrument == "Keys":
                    file_to_add = get_instrument_file(song_dir, "Piano")
                if file_to_add is None and (instrument == "Bass" or instrument == "CustomBass" or instrument == "Keys"):
                    file_to_add = get_instrument_file(song_dir, "rhythm")
                if file_to_add is None and instrument == "Keys":
                    file_to_add = get_instrument_file(song_dir, "Bass")
                if file_to_add is None and instrument == "Drums":
                    file_to_add = get_instrument_file(song_dir, "rhythm")



                # Didn't find any files for given instrument - create place holder
                if file_to_add is None:
                    file_to_add = create_empty_song_page(song_title, instrument)

                if file_to_add is not None:
                    song_pdf =  SongPDF(song_name=song_title, instrument=instrument, file_path=file_to_add)
                    song_pdfs.append(song_pdf)
        if song_title.lower() == "setbreak":
            song_pdfs.append(create_set_break_page())
    return song_pdfs

def strip_characters(song_title):
    """Strip non-alphanumeric characters, including spaces from song title."""
    return re.sub(r'[^a-zA-Z0-9]', '', song_title)

def get_playlist_name(client_id, client_secret, playlist_id):
    auth_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    playlist_name = sp.playlist(playlist_id=playlist_id, fields='name')
    return playlist_name['name']

def get_setlist_from_spotify(client_id, client_secret, playlist_id):
    """Return setlist as list from Spotify playlist link."""
    auth_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    results = sp.playlist_tracks(playlist_id)
    setlist = []

    for item in results['items']:
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
