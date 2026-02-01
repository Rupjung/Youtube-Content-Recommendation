import os
import json
import time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import yt_dlp
import pandas as pd
from config import Config

class YouTubeAPI:
    def __init__(self):
        self.api_key = Config.YOUTUBE_API_KEY
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def get_channel_videos(self, channel_id, max_results=50):
        """Fetch videos from a channel"""
        videos = []
        
        try:
            # First, get the uploads playlist ID
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                print(f"Channel {channel_id} not found")
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            next_page_token = None
            video_count = 0
            
            while video_count < max_results:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - video_count),
                    pageToken=next_page_token
                ).execute()
                
                for item in playlist_response['items']:
                    video_id = item['snippet']['resourceId']['videoId']
                    video_details = self.get_video_details(video_id)
                    if video_details:
                        videos.append(video_details)
                        video_count += 1
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token or video_count >= max_results:
                    break
            
            return videos
            
        except HttpError as e:
            print(f"YouTube API Error: {e}")
            return []
    
    def get_video_details(self, video_id):
        """Get detailed statistics for a video"""
        try:
            video_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                return None
            
            video_data = video_response['items'][0]
            
            # Get comments (limited)
            comments = self.get_video_comments(video_id, max_results=Config.COMMENTS_PER_VIDEO)
            
            # Safely get statistics with defaults
            statistics = video_data.get('statistics', {})
            snippet = video_data.get('snippet', {})
            content_details = video_data.get('contentDetails', {})
            
            video_details = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'published_at': snippet.get('publishedAt', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'duration': content_details.get('duration', ''),
                'views': int(statistics.get('viewCount', 0)),
                'likes': int(statistics.get('likeCount', 0)),
                'comments_count': int(statistics.get('commentCount', 0)),
                'comments': comments,
                'fetched_at': datetime.now().isoformat()
            }
            
            # Ensure all required fields have values
            for key in ['views', 'likes', 'comments_count']:
                if video_details[key] < 0:
                    video_details[key] = 0
            
            return video_details
            
        except HttpError as e:
            print(f"Error fetching video {video_id}: {e}")
            # Return minimal data structure
            return {
                'video_id': video_id,
                'title': 'Error fetching video',
                'description': '',
                'published_at': datetime.now().isoformat(),
                'views': 0,
                'likes': 0,
                'comments_count': 0,
                'comments': [],
                'fetched_at': datetime.now().isoformat()
            }
    
    def get_video_comments(self, video_id, max_results=10):
        """Fetch top comments for a video"""
        comments = []
        
        try:
            comments_response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                order='relevance'
            ).execute()
            
            for item in comments_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment.get('authorDisplayName', ''),
                    'text': comment.get('textDisplay', ''),
                    'likes': comment.get('likeCount', 0),
                    'published_at': comment.get('publishedAt', '')
                })
            
        except HttpError as e:
            # Comments might be disabled
            pass
        
        return comments
    
    def search_channels(self, query, max_results=10):
        """Search for channels based on query"""
        channels = []
        
        try:
            search_response = self.youtube.search().list(
                part='snippet',
                q=query,
                type='channel',
                maxResults=max_results
            ).execute()
            
            for item in search_response['items']:
                channel_id = item['snippet']['channelId']
                channels.append({
                    'channel_id': channel_id,
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description']
                })
            
        except HttpError as e:
            print(f"Search error: {e}")
        
        return channels

    def get_channel_info(self, channel_id, part="snippet,statistics"):
        """
        Calls the YouTube API 'channels' endpoint to get metadata and stats.
        """
        try:
            request = self.youtube.channels().list(
                part=part,
                id=channel_id
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]
            return None
        except Exception as e:
            print(f"Error fetching channel info: {e}")
            return None