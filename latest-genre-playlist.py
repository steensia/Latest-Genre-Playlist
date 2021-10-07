#!/usr/bin/python3
"""
Application Workflow
Step 1: Create list of genres
Step 2: Create playlists for each genre in the list
Step 3: Search for new released song(s) based on list of genres (incorporate albums later)
Step 4: Check if the song(s) were released today otherwise skip
Step 4: Check genre of song(s) based on artists
Step 4: Add new released song(s) to respective genre playlist
Step 5: Repeat steps above in a crontab via AWS Lambda
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from pprint import pprint

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
    
    """ Search for new released songs based on genre and return list of new songs """
    def SearchNewReleases(self):
        response = self.sp.new_releases(country = "US", limit = 1, offset = 3)

        pprint(response)
        # while response:
        #     albums = response['albums']
        #     for i, item in enumerate(albums['items'], 1):
        #         if(item['album_type'] == "single"):
        #             artists = item['artists']
        #             names = []
        #             for artist in artists:
        #                 names.append(artist['name'])
        #                 print(artist['id'])
        #             #print(artists)
        #             name = ", ".join(names)
        #             print("#{}, Artist(s): {} Album Name: {} Album Type: {} Id: {}".format(
        #                     albums['offset'] + i, 
        #                     name,
        #                     item['name'],
        #                     item['album_type'], 
        #                     item['id']))

        #     response = None
            #if albums['next']:
            #    response = self.sp.next(albums)
            #else:
            #    response = None

    def show_artist(self):
        uri = "spotify:artist:3Y7RZ31TRPVadSFVy1o8os"
        artist = self.sp.artist(uri)
        for genre in artist['genres']:
            if genre in self.genres:
                print(genre)
        pprint(artist)
    
    def get_album(self):
        album = self.sp.album('spotify:album:055uuuPMs7soYjnONo02QV')
        pprint(album)

    """ Helper function to retrieve list of genres from json file"""
    def __GetGenreList(self):
        file = open('data.json')
        data = json.load(file)
        return data['genres']

if __name__ == '__main__':
    lgp = LatestGenrePlaylist()
    #lgp.CreateGenrePlayLists()
    #lgp.AddNewReleases()
    #lgp.SearchNewReleases()
    #lgp.show_artist()
    lgp.get_album()









    