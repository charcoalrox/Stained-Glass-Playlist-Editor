#!/usr/bin/env python3
### m3u8 playlist editor that prepares files for transfer to my phone and allows bulk file movement


import sys
import os
import re
import time
from tinytag import TinyTag # Displays and edits song metadata

import find_forgotten_songs
import m3u_cleaner

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, 
    QListWidget, QApplication, QAbstractItemView, QLineEdit, QAbstractItemView, 
    QSlider, QWidgetAction, QApplication, QMainWindow, QMenu, QAction, QCheckBox
    )
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, Qt, QTimer


pathListPath = "C:\\Users\\payto\\OneDrive\\Desktop\\Music Project\\Stained-Glass-Music-Player\\paths.json" # One hard-coded path to avoid many more hard-coded paths
songspath = ""
playlistsPath = ""

mPlayer = QMediaPlayer()


# Search over music by name, artist, or album
class SearchMusicWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setWindowTitle("Search Music")

        # Search bar logic
        self.searchbarWidget = QLineEdit()
        self.searchbarWidget.setPlaceholderText("Search here. use \" || \" between queries to search multiple things at once") # Because if this ever existed anywhere, no one told me >:(
        self.searchbarWidget.textChanged.connect(self.search_call)
        layout.addWidget(self.searchbarWidget)

        # Timer that goes off a set amount of time after the last character was entered into the search bar
        self.searchTimer = QTimer(self)
        self.searchTimer.setSingleShot(True)
        self.searchTimer.timeout.connect(self.music_search)

        self.advancedToggle = QCheckBox()
        self.advancedToggle.stateChanged.connect(self.update_toggle)
        layout.addWidget(self.advancedToggle)

        self.toggleLabel = QLabel("Advanced Search")
        layout.addWidget(self.toggleLabel)

        # Search Results
        self.artistSearchLabel = QLabel("Results by artist name")
        layout.addWidget(self.artistSearchLabel)

        self.artistSearchResults = QListWidget()
        layout.addWidget(self.artistSearchResults)
        self.artistSearchResults.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.albumSearchLabel = QLabel("Results by album name")
        layout.addWidget(self.albumSearchLabel)

        self.albumSearchResults = QListWidget()
        layout.addWidget(self.albumSearchResults)
        self.albumSearchResults.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.basicSearchLabel = QLabel("Title Search Results")
        layout.addWidget(self.basicSearchLabel)

        # search
        self.primarySearchResults = QListWidget()
        layout.addWidget(self.primarySearchResults)
        self.primarySearchResults.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Enable Music editor context menu
        self.setup_context_menu(self.artistSearchResults)
        self.setup_context_menu(self.albumSearchResults)
        self.setup_context_menu(self.primarySearchResults)


        # Hiding advanced search results by default
        self.artistSearchResults.hide()
        self.albumSearchResults.hide()
        self.artistSearchLabel.hide()
        self.albumSearchLabel.hide()

        self.setLayout(layout)

        self.isAdvancedSearch = False

    def update_toggle(self):
        self.isAdvancedSearch = not self.isAdvancedSearch

        if self.isAdvancedSearch:
            self.artistSearchResults.show()
            self.albumSearchResults.show()
            self.artistSearchLabel.show()
            self.albumSearchLabel.show()
            self.music_search() # Fill out advanced search options if the toggle is activated
        else:
            self.artistSearchResults.hide()
            self.albumSearchResults.hide()
            self.artistSearchLabel.hide()
            self.albumSearchLabel.hide()

    # Search only a second or so after the last char was entered into the line editor
    def search_call(self):
        self.searchTimer.start(500) # ~0.5 seconds delay

    # Scan the given music directory and display all files
    def music_search(self):
        self.primarySearchResults.clear()
        self.artistSearchResults.clear()
        self.albumSearchResults.clear()

        #"or" operator support. I name music inconsistently (IE: JoCo vs Jonathan Coulton) so I want to be able to search multiple queries at once
        query = self.searchbarWidget.text().lower().split(" || ")

        for (dirpath, dirnames, filenames) in os.walk(songspath):
            for file in filenames: # obtain all files in the music folder

                for request in query: # Iterate over all keywords searched
                    if request in file.lower():
                        self.primarySearchResults.addItem(file)

                    if self.isAdvancedSearch == True: # Tinytag is slow if you have a lot of music so the advanced toggle should only run if it's on

                        try: # Tiny tag might fail and cause a crash if non-music files are present in the music folder so it must be able to quietly fail
                            tagData = TinyTag.get(songspath + "\\" + file) # Extract metadata from song for advanced search
                            if request in tagData.artist.lower():
                                self.artistSearchResults.addItem(file)

                            if request in tagData.album.lower():
                                self.albumSearchResults.addItem(file)
                        except:
                            pass

    # For setting up the three different context menus for the 3 different QListWidgets on the search page
    def setup_context_menu(self, widget):
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda position: edit_songs_menu(
                self,
                widget.mapTo(self, position),
                widget.selectedItems()
            )
        )


# Lists songs not yet put into a playlist. Popup Window (disabled by default)
class ForgottenSongsWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setWindowTitle("Songs not in playlists")

        # Define list of songs not currently in a playlist
        self.songsListWidget = QListWidget()
        layout.addWidget(self.songsListWidget)
        self.songsListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection) # Enables multi-item list selections

        self.button = QPushButton("Refresh")
        self.button.clicked.connect(self.refresh_list)
        layout.addWidget(self.button)

        # Enable custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda position: edit_songs_menu(self, position, self.songsListWidget.selectedItems())
        ) 

        # Run these functions once automatically while setting up with window
        self.setLayout(layout)
        self.refresh_list()

    # Scan through all playlists/songs. Find songs not currently available
    def refresh_list(self):
        self.songsListWidget.clear()
        self.songsListWidget.addItems(find_forgotten_songs.songSearch(playlistsPath, songspath))


# Lists contents of a single playlist in own window
class PlaylistViewerWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setWindowTitle("Playlist view")

        self.playlistDescription = QLabel()
        self.playlistDescription.setText(" ")
        layout.addWidget(self.playlistDescription)

        self.songsListWidget = QListWidget()
        layout.addWidget(self.songsListWidget)
        self.songsListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection) # Enables multi-item list selections

        self.button = QPushButton("Refresh")
        self.button.clicked.connect(self.prep_window)
        layout.addWidget(self.button)

        # Enable custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda position: edit_songs_menu(self, position, self.songsListWidget.selectedItems(), self.selectedPlaylist)
        )

        self.setLayout(layout)

        self.selectedPlaylist = None # Playlist passed from main window when this is opened
        self.mDSongsWindow = None # Holder variable for the Meta Data Song editor window

    def prep_window(self):
        self.setWindowTitle(self.selectedPlaylist[:-5])
        self.songsListWidget.clear()

        fileName = (playlistsPath + "//" + self.selectedPlaylist)
        with open(fileName, "r", encoding='utf-8', errors='ignore') as f:
            for x in f: 
                if x[0] == '#' and x[1] == '#' and x[2] == '#': # Set playlist description if present
                    self.playlistDescription.setText(x[3:])
                elif x[0] == '#' or x[0] == '\n': # ignore blank lines and comments
                    pass
                else: # Display remaining files that contain a file extension
                    self.songsListWidget.addItem(x[3:].strip())
        f.close()


# change/create playlist name and description
class playlistEditorWindow(QWidget): 
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setWindowTitle("Edit Playlist Data")

        self.nameTitle = QLabel()
        self.nameTitle.setText("Playlist Name: ")
        self.newName = QLineEdit()
        layout.addWidget(self.nameTitle)
        layout.addWidget(self.newName)

        self.DescTitle = QLabel()
        self.DescTitle.setText("Playlist Description: ")
        self.newDesc = QLineEdit()
        layout.addWidget(self.DescTitle)
        layout.addWidget(self.newDesc)

        self.button = QPushButton("Submit")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.create_playlist)

        self.setLayout(layout)

        self.parent_window = None
        self.selectedPlaylist = None # Song selected when this window is open
        self.playlistToDelete = None

    def create_playlist(self):
        title_text = self.newName.text().strip() # .strip makes sure blank spaces alone don't count as a title
        desc_text = self.newDesc.text().strip().replace("\r", "").replace("\n", "")
        filePath = f"{playlistsPath}//{title_text}.m3u8"
        if self.playlistToDelete is not None: filePath = f"{playlistsPath}//{self.playlistToDelete.text()}"
        file_data = ""

        # create a file if the title is valid
        if title_text:

            # Check if file is real, Copy data if yes
            if os.path.exists(filePath):
                with open(filePath, "r", encoding="utf-8") as f:
                    file_data = f.read()

            if self.playlistToDelete is not None and self.playlistToDelete.text() != f"{title_text}.m3u8" and os.path.exists(f"{playlistsPath}//{self.playlistToDelete.text()}"):
                self.parent_window.delete_playlist(self.playlistToDelete)

            # Write file with provided data from LineEdit elems
            with open(f"{playlistsPath}//{title_text}.m3u8", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"#{title_text}\n")

                if desc_text:
                    f.write(f"###{desc_text} \n")

                if file_data != "":
                    for line in file_data.splitlines():
                        if not line.startswith('#'):
                            f.write(line + '\n')

            # Automatically close window after editing (if editing existing playlist). Solves issues with path errors after initial edit finishes
            if self.playlistToDelete is not None:
                self.close()

            self.parent_window.display_playlists()

        else: 
            print("ERROR: Need an input title")


# Default window. Displays all playlists and allows opening of other windows
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Playlist Editor")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Display all playlists in list
        self.playlistList = QListWidget()
        self.playlistList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.playlistList.itemSelectionChanged.connect(self.selection_changed)
        self.display_playlists()
        layout.addWidget(self.playlistList)

        self.nowPlayingText = QLabel("Currently Playing: Nothing")
        layout.addWidget(self.nowPlayingText)
        mPlayer.currentMediaChanged.connect(self.update_now_playing_label)

        # Progress bar for position in song
        mPlayer.positionChanged.connect(self.update_slider_position) # Slider stays in position with correct point in song
        self.bar = QSlider(Qt.Horizontal)
        self.bar.setRange(0, 100)
        self.bar.sliderReleased.connect(self.update_song_time)
        layout.addWidget(self.bar)

        # Play/Pause whatever songs are currently playing
        self.button = QPushButton("Play/Pause Song")
        self.button.clicked.connect(self.play_or_pause_song)
        layout.addWidget(self.button)

        # Access unsued songs window
        self.button = QPushButton("Find Forgotten Songs")
        self.button.clicked.connect(self.window_unused_songs)
        layout.addWidget(self.button)

        # Modify playlists into a generalized .m3u8 format
        self.button = QPushButton("Playlist Scrubber")
        self.button.clicked.connect(self.m3u_repair)
        layout.addWidget(self.button)

        self.button = QPushButton("Search Music")
        self.button.clicked.connect(self.search_window_activate)
        layout.addWidget(self.button)

        # Enable custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.main_context_menu) # Real one will edit playlist names and descriptions

        # Holder vars for child windows of main
        self.searchMusicWindow = None
        self.fFSongsWindow = None
        self.pCSongsWindow = None
        self.playListEditorWindow = None
        self.selectedPlaylist = None

    # separate window opener funcs

    def search_window_activate(self):
        self.searchMusicWindow = SearchMusicWindow()
        self.searchMusicWindow.show()

    # display all songs not inside of a playlist
    def window_unused_songs(self, checked):
        self.fFSongsWindow = ForgottenSongsWindow()
        self.fFSongsWindow.show()

    # display all songs inside of playlist
    def window_playlist_contents(self):

        if self.selectedPlaylist is not None:
            self.pCSongsWindow = PlaylistViewerWindow()
            self.pCSongsWindow.selectedPlaylist = self.selectedPlaylist.text()
            self.pCSongsWindow.prep_window()
            self.pCSongsWindow.show()
        else:
            print("ERROR: Please select a playlist to proceed")

    # Funcs that don't open windows

    # Set progress bar to accurate song time
    def update_slider_position(self, position):
        duration = mPlayer.duration()

        if duration > 0 and not self.bar.isSliderDown(): # Make sure a song is playing and that the user isn't already trying to update time
            percent = (position / duration) * 100 # Convert position to number out of 100 so I don't have to update the slider values per song (which would break current update_song_time() implementation)
            self.bar.setValue(int(percent))

            if percent >= 100:
                self.nowPlayingText.setText("Currently Playing: Nothing")

    # Get currently playing media from player and convert URL into readable format
    def update_now_playing_label(self):
        songPath = mPlayer.currentMedia().canonicalUrl()
        splitPath = str(songPath).split("//")
        songTitle = splitPath[len(splitPath) - 1][:-2]

        self.nowPlayingText.setText("Currently Playing: " + songTitle)

    # Set song time to position on slider
    def update_song_time(self):
        if mPlayer.isSeekable():
            mPlayer.newPosition = int((mPlayer.duration()/100) * self.bar.value()) # Convert song time to percent value out of 100 and then add the percent value from the current progress of the slider (ugly but works great!)
            mPlayer.setPosition(mPlayer.newPosition)

    def play_or_pause_song(self):
        mPlayer.play() if mPlayer.state() == QMediaPlayer.PausedState else mPlayer.pause()

    # Store current playlistList selection into a variable for later use
    def selection_changed(self):
        self.selectedPlaylist = self.playlistList.currentItem()

    # m3u repair script
    def m3u_repair(self):
        m3u_cleaner.cleanFiles(playlistsPath)
        self.display_playlists()

    # Refresh central playlist list
    def display_playlists(self):
        self.playlistList.clear()

        for file in os.listdir(playlistsPath):
            if file.endswith(".m3u8") or file.endswith(".m3u"):
                self.playlistList.addItem(file)

    def delete_playlist(self, playlistToDelete):
        targetPath = f"{playlistsPath}//{playlistToDelete.text()}"

        if os.path.exists(targetPath):
            os.remove(targetPath)
            self.display_playlists() # refresh playlists when done
            self.selection_changed()


    # Playlist modification options for main window
    def main_context_menu(self, position):
        context = QMenu(self)

        open_playlist = QAction("Open playlist", self)
        open_playlist.triggered.connect(self.window_playlist_contents)
        context.addAction(open_playlist)


        edit_playlist = QAction("Edit playlist", self)
        edit_playlist.triggered.connect(lambda: self.create_new_playlist(True, self.playlistList.selectedItems()[0]))
        context.addAction(edit_playlist)


        create_playlist = QAction("Create playlist", self)
        create_playlist.triggered.connect(self.create_new_playlist)
        context.addAction(create_playlist)

        delete_playlist = QAction("Delete playlist", self)
        delete_playlist.triggered.connect(lambda: self.delete_playlist(self.playlistList.selectedItems()[0]))
        context.addAction(delete_playlist)

        context.addSeparator()

        # Description of selected playlist (if applicable)
        text_action = QWidgetAction(context)
        text_description = QLabel(" ")
        text_description.setWordWrap(True)
        text_action.setDefaultWidget(text_description)
        context.addAction(text_action)

        # Disable options that require a specific playlist to be selected if no playlist is selected
        if not self.playlistList.selectedItems():
            open_playlist.setEnabled(False)
            edit_playlist.setEnabled(False)
            delete_playlist.setEnabled(False)
        else: # If a playlist is selected, search for a playlist description to add to menu
            playlist_url = playlistsPath + "\\" + str(self.playlistList.selectedItems()[0].text())
            with open(playlist_url, "r", encoding="utf-8") as f:
                for lines in f:
                    if lines.startswith("###"):
                        text_description.setText(lines[3:])
                        break
                    if not lines.startswith("#"):
                        break
                f.close()

        context.exec(self.mapToGlobal(position))

    def create_new_playlist(self, overwrite = False, selectedPlaylist = None):

        # Summon Playlist Editor Window so user may input new data
        self.playListEditorWindow = playlistEditorWindow()
        self.playListEditorWindow.selectedPlaylist = self.selectedPlaylist
        if overwrite: self.playListEditorWindow.playlistToDelete = self.selectedPlaylist
        self.playListEditorWindow.parent_window = self
        self.playListEditorWindow.show()

        if self.selectedPlaylist is not None and overwrite == True:
            self.playListEditorWindow.newName.setText(self.selectedPlaylist.text()[:-5])
            with open(f"{playlistsPath}//{self.selectedPlaylist.text()}", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("###"):
                        self.playListEditorWindow.newDesc.setText(line[3:])

    # Closes all pages when the top-level page is closed
    def close_event(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()


# Initialize file paths before running software
def scan_file_paths():
    with open(pathListPath, "r", encoding="utf-8") as f:
        global songspath
        global playlistsPath

        for lines in f:
            if lines.startswith("songs"):
                matches = re.findall(r'"([^"]*)"', lines) # Regex to capture the filepath in quotations
                songspath = matches[0]
            if lines.startswith("playlists"):
                matches = re.findall(r'"([^"]*)"', lines)
                playlistsPath = matches[0]
    f.close()


# context menu for right clicking on songs
def edit_songs_menu(self, position, selected_items, input_playlist = None):
    context_menu = QMenu(self)

    # Optionally, play selected song
    action_play_music = QAction("Play Song")
    action_play_music.triggered.connect(lambda: play_song(self, selected_items[0].text()))
    context_menu.addAction(action_play_music)
    if not selected_items: # You may only play a song if it's selected
        action_play_music.setEnabled(False)

    # Move songs to a new playlist without modifying an existing playlist
    action_one = QMenu("Copy song(s) to new playlist")
    for file in os.listdir(playlistsPath):
        if file.endswith(".m3u8") or file.endswith(".m3u"):
            action = action_one.addAction(file)

            # Connect the action to a function
            action.triggered.connect(
                lambda checked=False, playlist=file:
                    copy_songs_to_playlist(self, selected_items, None, playlist)
            )

    context_menu.addMenu(action_one)

    if input_playlist is not None: # You can only edit the contents of the opened playlist if you're inside of an opened playlist
        # Move songs to a new playlist and remove them from the existing playlist
        action_two = QMenu("Move song(s) to new playlist")
        for file in os.listdir(playlistsPath):
            if file.endswith(".m3u8") or file.endswith(".m3u"):
                action = action_two.addAction(file)

                action.triggered.connect(
                    lambda checked = False, playlist = file:
                        copy_songs_to_playlist(self, selected_items, input_playlist, playlist)
                )

        # remove songs from existing playlist. Do not move them anywhere
        action_three = QAction("Remove song(s) from playlist")
        action_three.triggered.connect(lambda: copy_songs_to_playlist(self, selected_items, input_playlist))

        context_menu.addMenu(action_two)
        context_menu.addAction(action_three)


    global_position = self.mapToGlobal(position)
    context_menu.exec_(global_position)


# copies all songs to a new playlist. Optionally deletes them from current playlist
def copy_songs_to_playlist(self, songs, input_playlist = None, output_playlist = None):

    if output_playlist is not None: # output_playlist may be "none" if songs are just being deleted from current playlist instead of moved
        fileName = (playlistsPath + "//" + output_playlist)

        with open(fileName, "rb+") as f:
            # Go to the end of the file
            f.seek(0, os.SEEK_END)
            pos = f.tell()

            # step backwards over windows newline char returns
            while pos > 0:
                pos -= 1
                f.seek(pos)

                c = f.read(1)
                if c not in (b"\r", b"\n"):
                    break
            f.truncate(pos + 1)

            # Make sure we're at the EOF and add all selected songs
            f.seek(0, os.SEEK_END)

            for song in songs:
                # print("Writing songs")
                f.write(f"\n..\\{song.text()}".encode("utf-8"))

            f.write(b"\n") # Making sure playlists end uniformly w/ a newline character
    
    # optionally, remove selected songs from the currently opened playlist
    if input_playlist is not None:

        # Variables we only need if there's a valid input playlist
        file_data = ""
        fileName = (playlistsPath + "//" + input_playlist)
        songs_to_remove = {f"..\\{song.text()}" for song in songs}

        # Save the data of the current file
        with open(fileName, "r", encoding="utf-8") as f:
            file_data = f.read()

        with open(fileName, "w", encoding="utf-8") as f:
            for line in file_data.splitlines():
                if line.startswith("#") or line not in songs_to_remove:
                    f.write(line + "\n")


# Empty music queue and play currently selected song from any window
def play_song(self, inputSong):

    mPlayer.stop()
    url = QUrl.fromLocalFile(str(songspath + "//" + inputSong))
    mPlayer.setMedia(QMediaContent(url))

    # If song isn't muted when it starts, some songs will make a high-pitched chirping sound
    mPlayer.setMuted(True)
    mPlayer.play()
    time.sleep(0.2)
    mPlayer.setMuted(False)


if __name__ == "__main__":
    scan_file_paths()

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()