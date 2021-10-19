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
    """ Initialize instance variables and SpotifyOAuth class to authenticate requests 
        Create playlists and store their playlist ids in a dictionary
    """  
    def __init__(self, event):
        self.scope = "user-library-read playlist-modify-public"

        # Authenticate Spotify
        self.sp = spotipy.Spotify(auth_manager = SpotifyOAuth(scope = self.scope))
        self.user_id = os.environ['SPOTIPY_CLIENT_USERNAME']
        
        # Collection of existing and to be created playlists
        self.genres = self.CreateGenrePlayLists(event)
    
    # def CreateGenreList(self, genres: list):
    #     self.genres = genres

    """ Create a playlist for each genre in the list 
        and return a dictionary for genre and playlist id pair"""
    def CreateGenrePlayLists(self, event):
        # Add 'all' playlist which adds any genre of music to playlist
        genres = event['genres']
        genres.append('all')
        genres.append('recent')

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
                                                            name = "Latest songs playlist",
                                                            public = True)['uri']
                # Insert genre playlist to database
                response = table.put_item(
                    Item = {
                        'genre' : genre,
                        'id' : playlist_id
                    }
                )    
                print(response)
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

        # TODO: Adding one album for now, remove this after testing
        #response = self.sp.new_releases(country="US", limit=1, offset=1)
        response = self.sp.new_releases(country="US", limit=4, offset=0)
        album_ids = []

        while response:
            albums = response['albums']
            for i, item in enumerate(albums['items'], 1):
                # TODO: Add logic to accept albums or singles
                today = datetime.combine(datetime.today(), datetime.min.time())
                past = today - timedelta(days=4)
                album_date = datetime.strptime(item['release_date'], '%Y-%m-%d')
                before_album_date = album_date - timedelta(days=4)

                # TODO: Replace this logic with new releases today (album_date > today)
                if before_album_date <= album_date <= today:
                    print("Added New Release #{}: {} by {} ".format(albums['offset'] + i, item['name'], item['artists'][0]['name']))
                    album_id = item['id']
                    album_ids.append(album_id)

            response = None

        return album_ids

    # def show_artist(self):
    #     uri = "spotify:artist:3Y7RZ31TRPVadSFVy1o8os"
    #     artist = self.sp.artist(uri)
    #     for genre in artist['genres']:
    #         if genre in self.genres:
    #             print(genre)
    #     pprint(artist)
    
    """ Get each track inside the albums and return list of track ids
        Limit of 100 track ids to add to a playlist per request
    """
    def GetTrackIds(self, album_ids):
        track_ids = []
        track_ids_list = []

        for album_id in album_ids:
            album = self.sp.album("spotify:album:{}".format(album_id))
            for track in album['tracks']['items']:
                track_id = track['id'];
                track_ids.append(track_id)

                if(len(track_ids) == 100):                 
                    track_ids_list.append(track_ids)
                    track_ids = []
      
            track_ids_list.append(track_ids)
        print(len(track_ids_list))
        return track_ids_list
        
    """ Add list of tracks to playlist"""
    def AddTracksToPlaylist(self, playlist_id, track_ids_list):
        count = 0
        for list in track_ids_list:
            count += len(list)
            self.sp.playlist_add_items(playlist_id, list)
        print("Added {} tracks".format(count))     

    """ Remove list of tracks in playlist"""
    def RemoveTracksInPlaylist(self, playlist_id, track_ids_list):
        count = 0
        for list in track_ids_list:
            count += len(list)
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, list)
        print("Removed {} tracks".format(count))       

    """ Helper function to retrieve list of genres from json file"""
    def __GetGenreList(self, json_file):
        file = open(json_file)
        data = json.load(file)
        return data['genres']
    
def EventHandler(event, context):
    # For local testing
    if not event:
        json_string = '{ "genres": [] }'
        event = json.loads(json_string)
    lgp = LatestGenrePlaylist(event)
    #print(lgp.genres)
    album_ids = lgp.SearchNewReleases()
    track_ids = lgp.GetTrackIds(album_ids)

    all = lgp.genres['all']

    response = lgp.AddTracksToPlaylist(all, track_ids)
    # TODO: Remove after testing
    if True == True:
        lgp.RemoveTracksInPlaylist(all, track_ids)
    
if __name__ == '__main__':
    EventHandler("","")