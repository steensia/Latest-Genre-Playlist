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
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from secrets import client_id, client_secret

import argparse
import logging

# scope = "playlist-modify-public"
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret,redirect_uri="", scope=scope))
# user_id = sp.me()['id']
# sp.user_playlist_create(user_id, args.playlist)

class LatestGenrePlaylist:
    def __init__(self):
        self.genres = []
        # self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, 
        #                                                                 client_secret=client_secret))
        # self.user = self.sp.me()['id']
    
    def CreateGenreList(self, genres: list):
        self.genres = genres

    def CreateGenrePlayLists(self):
        for genre in self.genres:
            sp.user_playlist_create(user=user_id,
                                         name= genre + " playlist",
                                         public=True)

def main():
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id,
                                                           client_secret=client_secret))

    results = sp.search(q='weezer', limit=20)
    for idx, track in enumerate(results['tracks']['items']):
        print(idx, track['name'])

    user_id = sp.me()['id']
    sp.user_playlist_create(user_id, "test playlist")

def get_args():
    parser = argparse.ArgumentParser(description='Creates a playlist for user')
    parser.add_argument('-p', '--playlist', required=True,
                        help='Name of Playlist')
    parser.add_argument('-d', '--description', required=False, default='',
                        help='Description of Playlist')
    return parser.parse_args()

def main2():
    args = get_args()
    scope = "playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    user_id = sp.me()['id']
    sp.user_playlist_create(user_id, args.playlist)
        
if __name__ == '__main__':
    # lgp = LatestGenrePlaylist()
    # lgp.CreateGenreList(["rap", "hip-hop", "r-n-b", "pop"])

    # for genre in lgp.genres:
    #     print(genre)
    
    # lgp.CreateGenreList()
    #main()
    main2()


    