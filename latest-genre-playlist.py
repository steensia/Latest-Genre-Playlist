#!/usr/bin/python3
"""
Application Workflow
Step 1: Create list of genres
Step 2: Create playlists for each genre in the list
Step 3: Search for new released song(s) based on list of genres
Step 4: Add new released song(s) to respective playlist
Step 5: Repeat steps above in a crontab via AWS Lambda
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

class LatestGenrePlaylist:
    """ Initialize instance variables and SpotifyOAuth class to authenticate requests """  
    def __init__(self):
        self.genres = self.__GetGenreList()
        self.scope = "playlist-modify-public"
        self.sp = spotipy.Spotify(auth_manager = SpotifyOAuth(scope = self.scope))
        self.user_id = self.sp.me()['id']
    
    # def CreateGenreList(self, genres: list):
    #     self.genres = genres

    """ Create a playlist for each genre in the list """
    def CreateGenrePlayLists(self):
        for genre in self.genres:
            playlistId = self.sp.user_playlist_create(user = self.user_id,
                                         name = genre + " playlist",
                                         public = True)
            print(playlistId)

    """ Helper function to retrieve list of genres from json file"""
    def __GetGenreList(self):
        file = open('data.json')
        data = json.load(file)
        return data['genres']

if __name__ == '__main__':
    lgp = LatestGenrePlaylist()
    lgp.CreateGenrePlayLists()
    #lgp.AddNewReleases()


    