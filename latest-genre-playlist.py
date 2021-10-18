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

        # Keep track of playlist genre and spotify id
        dictionary = {}

        # Initailize DB and set up table to query
        dynamodb = boto3.resource("dynamodb", region_name='us-west-2')
        table = dynamodb.Table('Playlists')

        # Check JSON for what genres are of interest        
        for genre in genres:
            playlist = table.query(
                KeyConditionExpression=Key('genre').eq(genre)
            )

            playlist_genre = playlist['genre']
            playlist_id = playlist['id']

            # Create playlist and add to database if doesn't exist
            if not playlist['Items']:
                playlist_id = self.sp.user_playlist_create(user = self.user_id,
                name = "Latest songs playlist",
                public = True)
                
                # Insert genre playlist to database
                response = table.put_item(
                    Item = {
                        'genre' : 'all',
                        'id' : playlist_id
                    }
                )    
                print(response)
                dictionary['all'] = playlist_id

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
        playlist_id = self.sp.playlist_add_items(playlist_id, track_ids)
        print("Playlist id: {}".format(playlist_id))

    """ Helper function to retrieve list of genres from json file"""
    def __GetGenreList(self, json_file):
        file = open(json_file)
        data = json.load(file)
        return data['genres']

def DatabaseDemo():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

    #response = table.scan()

    table = dynamodb.Table('Playlists')
    playlists = table.query(
        KeyConditionExpression=Key('genre').eq('all')
    )

    if not playlists['Items']:
        print("Empty")
    else:
        for playlist in playlists['Items']:
            print(playlist['genre'], ":", playlist['id'])

def DatabaseDemo2(event):
    print(event['genres'])

    dynamodb = boto3.resource("dynamodb", region_name='us-west-2')
    table = dynamodb.Table("Playlists")
    playlists = table.scan()['Items']
    
    genres = []
    for playlist in playlists:
        genre = playlist['genre']
        genres.append(genre)
        print(genre)


def DatabaseDemo3(event):
    scope = "user-library-read playlist-modify-public"

    # Authenticate Spotify
    sp = spotipy.Spotify(auth_manager = SpotifyOAuth(scope = scope))
    user_id = os.environ['SPOTIPY_CLIENT_USERNAME']

    dynamodb = boto3.resource("dynamodb", region_name='us-west-2')

    if not event['genres']: 
        table = dynamodb.Table('Playlists')
        playlists = table.query(
            KeyConditionExpression=Key('genre').eq('all')
        )

    if not playlists['Items']:
        playlistId = sp.user_playlist_create(user = user_id,
                        name = "Latest songs playlist",
                        public = True)

        response = table.get_item(
            Key = {
                'all' : playlistId
            }
        )    

        print(response)

def DatabaseDemo4(event):
    dynamodb = boto3.resource("dynamodb", region_name='us-west-2')
    table = dynamodb.Table('Playlists')

    # Insert genre playlist to database
    # response = table.put_item(
    #     Item = {
    #         'genre' : 'all',
    #         'id' : 'spotify:playlist:2fLku8TI4bjuJAzGH8NBjD'
    #     }
    # )

    response = table.get_item(
        Key = {
            'genre' : 'all',
            'id': 'spotify:playlist:2fLku8TI4bjuJAzGH8NBjD'
        }
    )     

    print(response)

def DatabaseDemo5(event):
    dynamodb = boto3.resource("dynamodb", region_name='us-west-2')
    table = dynamodb.Table('Playlists')
    playlists = table.scan()['Items']

    event['genres'].append('test')
    print(event['genres'])

    # if not event['genres']:
    #     for playlist, c in playlists:
    #         if playlist['genre'] == 'all':
    #             print(playlist['id'])
    # else:
    #     for genre, base in event['genres'], "all2":
    #         print("{} {}".format(genre, base))

def SpotifyExample():
    CLIENT_USERNAME = os.environ['SPOTIPY_CLIENT_USERNAME']
    PLAYLIST_ID = os.environ['RECENT_LIKES_PLAYLIST_ID']
    PLAYLIST_LEN = int(os.environ['RECENT_LIKES_PLAYLIST_LEN'])
    
    print("Authenticating to Spotify")
    scope = "user-library-read playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    print("Authenticated to Spotify")
    
    print("Getting playlist tracks.")
    results = sp.user_playlist_tracks(user=CLIENT_USERNAME, playlist_id=PLAYLIST_ID)
    current_tracks = []
    for track in results['items']:
        current_tracks.append(track['track']['uri'])
    
    print("Clearing playlist.")
    sp.user_playlist_remove_all_occurrences_of_tracks(user=CLIENT_USERNAME, playlist_id=PLAYLIST_ID, tracks=current_tracks)
    
    print("Get liked tracks.")
    results = sp.current_user_saved_tracks(limit=PLAYLIST_LEN)
    recent_likes = []
    for idx, item in enumerate(results['items']):
        track = item['track']
        print(idx, track['artists'][0]['name'], " – ", track['name'])
        recent_likes.append(track['uri'])
    
    print("Add liked tracks.")
    sp.user_playlist_add_tracks(user=CLIENT_USERNAME, playlist_id=PLAYLIST_ID, tracks=recent_likes)
    
def EventHandler(event, context):
    print("Test handler")
    #Remove this after deploying, we will be getting event as constant JSON in AWS rule
    #json_string = '{ "genres": ["all"] }'
    #event = json.loads(json_string)
    #DatabaseDemo4(event)
    SpotifyExample()
    
if __name__ == '__main__':
    EventHandler("","")