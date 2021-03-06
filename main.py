#!/usr/bin/env python3
"""Author: Alexander Ortenburger
"""

import os
import sys
import subprocess
import MusicBricksIDMTTranscriberXMLConverter
import spotipy
import spotipy.util as util
import json
import math

SCOPE = 'user-library-read'
SPOTIPY_CLIENT_ID = 'aa67b8fd03c04aec8a316df60e0b6932'
SPOTIPY_CLIENT_SECRET = 'b8c24dbe78764ce3ae0cdd9bbe3942b5'
SPOTIPY_REDIRECT_URI = 'http://mio.com'
CACHE = '.spotipyoauthcache'
PORT_NUMBER = 8080

sp = spotipy.Spotify()
converter = MusicBricksIDMTTranscriberXMLConverter.MusicBricksIDMTTranscriberXMLConverter()
sp_oauth = spotipy.oauth2.SpotifyOAuth( SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET,SPOTIPY_REDIRECT_URI,scope=SCOPE,cache_path=CACHE )

os.environ['SPOTIPY_CLIENT_ID'] = SPOTIPY_CLIENT_ID
os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIPY_CLIENT_SECRET
os.environ['SPOTIPY_REDIRECT_URI'] = SPOTIPY_REDIRECT_URI

def get_mp3list(directory):
	mp3List = []
	for file in [f for f in os.listdir(directory) if f.endswith('.mp3')]:
		mp3List.append(file)
	return(mp3List)
	
def get_musicinfo(filename):
	subprocess.run(["./MusicBricksIDMTTranscriber -i " + filename + " -o " + filename +" --bass --xml"], shell=True,)

def get_playlist_tracks(username, playlist_id):
	results = sp.user_playlist_tracks(username, playlist_id)
	tracks = results['items']
	while results['next']:
		results = sp.next(results)
		tracks.extend(results['items'])
	return tracks
	
def get_bpm_field(musicinfoxml):
	""" Creates a field of 4/4 and checks the bpm """
	print(musicinfoxml)
	musicinfo = converter.readXML(musicinfoxml)
	beatfield = musicinfo["beats"] 
	bpmfield = {}
	concat_beatfield={}
	i=0
	last_bpm=0
	startpos=0
	endpos=0
	while i < math.floor(len(beatfield)/4):
		current_bpm = round(60/(beatfield[(i)*4+3]["onset"] - beatfield[i*4]["onset"])*4)
		if i > 0 and abs(last_bpm - current_bpm) > 5:
			concat_beatfield[last_bpm] = str(startpos) + " - " + str(beatfield[i*4-1]["onset"])
			startpos = beatfield[i*4]["onset"]
		last_bpm=current_bpm
		endpos = beatfield[(i)*4+3]["onset"]
		i = i+1
	concat_beatfield[last_bpm] = str(startpos) + " - " + str(endpos)
	print(concat_beatfield)
	return concat_beatfield


if __name__ == '__main__':
	with open('foo.json') as data_file:    
		data = json.load(data_file)

	i = 0  #playlist number
	while i <= len(data)-1:
		outdata = {"product": "sportify",  "version": 0.1,}
		outdata["playlist"]=data[i]["name"]
		j = 0 #track number
		tracks = []
		#while j <= 1: #for devel only
		while j <= len(data[i]["tracks"])-1:
			track = {	"id": j, 
						"uri": data[i]["tracks"][j]["track"]["uri"],
						"artist": data[i]["tracks"][j]["track"]["artists"][0]["name"],
						"name": data[i]["tracks"][j]["track"]["name"],
						"bpm-positions": {},
						"mood-position": {}
					}
			subprocess.run(["wget " + data[i]["tracks"][j]["track"]["preview_url"] + " -O download/%s.mp3" %j], shell=True)
			get_musicinfo("download/%s.mp3" %j)
			
			track["bpm-positions"] = get_bpm_field("download/%s.mp3.xml" %j)
			tracks.append(track)
			j = j+1
		outdata["songs"] = tracks
		with open('playlist%s.json' %i, 'w') as outfile:
			json.dump(outdata, outfile)
		i=i+1
