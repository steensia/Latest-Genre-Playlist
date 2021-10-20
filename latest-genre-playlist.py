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
from typing import final
import spotipy
from spotipy import SpotifyOAuth
import boto3
from botocore.exceptions import ClientError
from boto3 import resource
from boto3.dynamodb.conditions import Key
import json
from pprint import pprint
import os
from datetime import date, datetime, timedelta

class LatestGenrePlaylist:
    """ 
        Initialize instance variables and SpotifyOAuth class to authenticate requests 
        Create playlists and store their playlist ids in a dictionary
    """  
    def __init__(self, event):
        # Authenticate Spotify
        self.scope = "user-library-read playlist-modify-public"
        self.sp = spotipy.Spotify(auth_manager = SpotifyOAuth(scope = self.scope))
        self.user_id = os.environ['SPOTIPY_CLIENT_USERNAME']
        
        # Collection of existing and to be created playlists
        self.genres = self.CreateGenrePlayLists(event)

    """ 
        Create a playlist for each genre in the list 
        and return a dictionary for genre and playlist id pair
    """
    def CreateGenrePlayLists(self, event):
        # Add 'all' playlist which adds any genre of music to playlist
        genres = event['genres']
        genres.append('all')

        # Keep track of playlist genre and spotify id
        dictionary = {}

        # Initailize DB and set up table to query
        dynamodb = boto3.resource("dynamodb", region_name='us-west-2')
        table = dynamodb.Table('Playlists')

        # Check JSON for what genres are of interest        
        for genre in genres:
            playlist = table.query(
                KeyConditionExpression=Key('genre').eq(genre)
            )['Items']

            #Create playlist and add to database if doesn't exist
            if not playlist:
                playlist_id = self.sp.user_playlist_create(user = self.user_id,
                                        name = "Latest {} songs playlist".format(genre),
                                        public = True)['uri']
                # Insert genre playlist to database
                response = table.put_item(
                    Item = {
                        'genre' : genre,
                        'id' : playlist_id
                    }
                )    

                # Add playlist genre and id
                dictionary[genre] = playlist_id
            else:
                # Grab the first and only element
                playlist = playlist[0]
                playlist_genre = playlist['genre']
                playlist_id = playlist['id']

                # Add playlist genre and id
                dictionary[playlist_genre] = playlist_id

        return dictionary
        
    """ Add new released songs to the playlists """
    def AddNewReleases(self):
        # Grab album IDs for new released songs
        album_ids = self.SearchNewReleases()

        # Grab tracks from each album
        track_ids = self.GetTrackIds(album_ids)

        # Add tracks to playlist(s)
        for genre in self.genres:
            self.AddTracksToPlaylist(genre, track_ids)
            #self.__RemoveTracksInPlaylist(genre, track_ids)

    """ Search for new released songs based on genre and return list of album ids """
    def SearchNewReleases(self):
        response = self.sp.new_releases(country="US", limit=5, offset=0)
        album_ids = []

        albums = response['albums']
        for i, item in enumerate(albums['items'], 1):
            today = datetime.combine(datetime.today(), datetime.min.time())
            album_date = datetime.strptime(item['release_date'], '%Y-%m-%d')

            if album_date >= today:
                print("Found New Release #{} with {} track(s) released on {}: {} by {} ".format(
                    albums['offset'] + i, item['total_tracks'], album_date, item['name'], item['artists'][0]['name']))
                album_id = item['id']
                album_ids.append(album_id)

        return album_ids

    """ Get the album's genre based on the artist and return it """
    def GetTrackGenre(self, artist_id):
        return self.sp.artist(artist_id)['genres'] 
 
    """ 
        Get each track inside the albums and return list of track ids
        Separated as a list of tracks per album
    """
    def GetTrackIds(self, album_ids):
        track_ids_list = []

        for album_id in album_ids:
            track_ids = []
            album = self.sp.album("spotify:album:{}".format(album_id))

            for track in album['tracks']['items']:
                track_id = track['uri'];
                track_ids.append(track_id)    

            track_ids_list.append(track_ids)
        return track_ids_list

    """ Get current playlist and return tracks """
    def GetPlaylistTracks(self, playlist_id):
        response = self.sp.playlist(playlist_id)

        track_ids = []
        for track in response['tracks']['items']:
            track_uri = track['track']['uri']
            track_ids.append(track_uri)
            
        return track_ids
        
    """ Add list of tracks to playlist """
    def AddTracksToPlaylist(self, genre, track_ids_list):
        # Get existing tracks from playlist
        playlist_id = self.genres[genre]
        prev_list = self.GetPlaylistTracks(playlist_id)

        for curr_list in track_ids_list:
            count = 0
            new_list = [id for id in curr_list if id not in prev_list]
        
            # Get first track of album to identify artist's genre
            if new_list:
                count += len(new_list)

                # Add track to genre specific playlist
                track = self.sp.track(track_id=new_list[0])               
                trackGenres = self.GetTrackGenre(artist_id=track['artists'][0]['uri'])
                if genre in trackGenres:
                    self.sp.playlist_add_items(playlist_id, new_list)
                    print("Added {} tracks to 'Latest {} songs playlist'".format(count, genre))
                else:
                    if genre == 'all':
                        self.sp.playlist_add_items(playlist_id, new_list)
                        print("Added {} tracks to 'Latest songs playlist'".format(count, genre))            

    """ Helper function to remove existing tracks in playlist """
    def __RemoveTracksInPlaylist(self, genre, track_ids_list):
        playlist_id = self.genres[genre]

        count = 0
        for list in track_ids_list:
            count += len(list)
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, list)  

def EventHandler(event, context):
    lgp = LatestGenrePlaylist(event)
    lgp.AddNewReleases()

if __name__ == '__main__':
    EventHandler("","")
