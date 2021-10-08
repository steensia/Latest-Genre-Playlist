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
    """ Initialize instance variables and SpotifyOAuth class to authenticate requests 
        Create playlists and store their playlist ids in a dictionary
    """  
    def __init__(self):
        self.scope = "playlist-modify-public"
        self.sp = spotipy.Spotify(auth_manager = SpotifyOAuth(scope = self.scope))
        self.user_id = self.sp.me()['id']
        self.genres = self.CreateGenrePlayLists()
    
    # def CreateGenreList(self, genres: list):
    #     self.genres = genres

    """ Create a playlist for each genre in the list 
        and return a dictionary for genre and playlist id pair"""
    def CreateGenrePlayLists(self):
        dictionary = {}
        genres = self.__GetGenreList('data_test.json') 
        test = True

        if not genres: # data_test has an empty genres list, empty will accept all genres
            if test:
                playlistId = self.sp.user_playlist_create(user = self.user_id,
                                    name = "Latest songs playlist",
                                    public = True)
                dictionary['all'] = playlistId['id']
        else:
            for genre in self.genres:
                playlistId = self.sp.user_playlist_create(user = self.user_id,
                                            name = "Latest {} songs playlist".format(genre),
                                            public = True)
            dictionary[genre] = playlistId['id']

        return dictionary
    """ Add new released songs to the playlists"""
    def AddNewReleases(self):
        # Grab album IDs for new released songs
        album_ids = self.SearchNewReleases()
        print("Album ids: {}".format(album_ids))

        # Grab tracks and add them to playlist
        track_ids = self.GetTrackIds(album_ids=album_ids)
        print("Track ids: {}".format(track_ids))

        # Add tracks to playlist
        playlist_id = self.genres['all']
        self.AddTracksToPlaylist(playlist_id, track_ids)

    """ Search for new released songs based on genre and return list of album ids """
    def SearchNewReleases(self):
        # TODO: Add logic to check for date released

        response = self.sp.new_releases(country = "US", limit = 2, offset = 2)
        album_ids = []

        while response:
            albums = response['albums']
            for i, item in enumerate(albums['items'], 1):
                # TODO: Add logic to accept albums
                #if item['album_type'] == "single":
                album_id = item['id']
                album_ids.append(album_id)
            response = None
        
        return album_ids
            # if albums['next']:
            #    response = self.sp.next(albums)
            # else:
            #    response = None
            
            # Keep this to check genre type by grabbing artists and finding their genres
            # if(item['album_type'] == "single"):
            #     artists = item['artists']
            #     names = []
            #     for artist in artists:
            #         names.append(artist['name'])
            #         print(artist['id'])
            #

    # def show_artist(self):
    #     uri = "spotify:artist:3Y7RZ31TRPVadSFVy1o8os"
    #     artist = self.sp.artist(uri)
    #     for genre in artist['genres']:
    #         if genre in self.genres:
    #             print(genre)
    #     pprint(artist)
    
    """ Get each track inside the albums """
    def GetTrackIds(self, album_ids):
        track_ids = []

        for album_id in album_ids:
            album = self.sp.album("spotify:album:{}".format(album_id))
            for track in album['tracks']['items']:
                track_id = track['id'];
                track_ids.append(track_id)

        return track_ids
        
    """ Add list of tracks to playlist"""
    def AddTracksToPlaylist(self, playlist_id, track_ids):
        self.sp.playlist_add_items(playlist_id, track_ids)

    """ Helper function to retrieve list of genres from json file"""
    def __GetGenreList(self, json_file):
        file = open(json_file)
        data = json.load(file)
        return data['genres']


if __name__ == '__main__':
    lgp = LatestGenrePlaylist() 
    lgp.AddNewReleases()







    