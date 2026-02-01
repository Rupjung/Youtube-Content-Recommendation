import os
import json
import pandas as pd
from datetime import datetime
from utils.youtube_api import YouTubeAPI
from config import Config

class DataFetcher:
    def __init__(self, channel_id=None):
        self.channel_id = channel_id or Config.CHANNEL_ID
        self.youtube_api = YouTubeAPI()
        
    def fetch_channel_data(self):
        """Main method to fetch all channel data"""
        print(f"Fetching data for channel: {self.channel_id}")
        
        # Fetch videos
        videos = self.youtube_api.get_channel_videos(
            self.channel_id, 
            max_results=Config.MAX_VIDEOS_TO_ANALYZE
        )
        
        if not videos:
            print("No videos found or error fetching data")
            return None
        
        # Save raw data
        self._save_raw_data(videos)
        
        # Convert to DataFrame and process
        df = self._process_data(videos)
        
        print(f"Successfully fetched {len(videos)} videos")
        return df
    
    def _save_raw_data(self, videos):
        """Save raw video data as JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"videos_raw_{timestamp}.json"
        filepath = os.path.join(Config.RAW_DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        
        print(f"Raw data saved to: {filepath}")

    def fetch_channel_stats(self):
        """
        Fetches channel name, description, and key metrics.
        """
        print(f"Fetching metadata for channel: {self.channel_id}")
        
        # This now points to the method we just added above
        channel_data = self.youtube_api.get_channel_info(self.channel_id)
        
        if not channel_data:
            print("Could not retrieve channel statistics.")
            return None

        # Extract data from the nested API response
        snippet = channel_data.get("snippet", {})
        stats = channel_data.get("statistics", {})

        # Get the logo URL (High res is usually 800x800)
        thumbnails = snippet.get("thumbnails", {})
        logo_url = thumbnails.get("high", {}).get("url") or thumbnails.get("default", {}).get("url")

        return {
            "channel_id": self.channel_id,
            "channel_name": snippet.get("title"),
            "logo_url": logo_url,
            "channel_description": snippet.get("description"),
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "total_videos": int(stats.get("videoCount", 0))
        }
    
    def _process_data(self, videos):
        """Process and save cleaned data"""
        # Convert to DataFrame
        df = pd.DataFrame(videos)
        
        # Clean the data
        df_clean = df.copy()
        
        # Convert published_at to datetime
        df_clean['published_at'] = pd.to_datetime(df_clean['published_at'])
        
        # Calculate additional metrics
        df_clean['engagement_rate'] = (df_clean['likes'] + df_clean['comments_count']) / df_clean['views'].replace(0, 1)
        
        # Calculate additional metrics for analysis
        df_clean['likes_per_view'] = df_clean['likes'] / df_clean['views'].replace(0, 1)
        df_clean['comments_per_view'] = df_clean['comments_count'] / df_clean['views'].replace(0, 1)
        
        # Save processed data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(Config.PROCESSED_DATA_DIR, f"videos_processed_{timestamp}.csv")
        df_clean.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"Processed data saved to: {csv_path}")
        
        return df_clean