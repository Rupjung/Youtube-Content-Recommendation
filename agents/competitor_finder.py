import pandas as pd
from utils.youtube_api import YouTubeAPI
from config import Config

class CompetitorFinder:
    def __init__(self, channel_videos_df):
        self.channel_videos = channel_videos_df
        self.youtube_api = YouTubeAPI()
        self.competitors = []
    
    def find_competitors(self):
        """Find similar/competitor channels"""
        print("Finding competitor channels...")
        
        # Extract keywords from video titles
        keywords = self._extract_keywords()
        
        # Search for channels with similar content
        for keyword in keywords[:5]:  # Use top 5 keywords
            found_channels = self.youtube_api.search_channels(
                keyword, 
                max_results=3
            )
            self.competitors.extend(found_channels)
        
        # Remove duplicates
        self.competitors = self._remove_duplicates(self.competitors)
        
        # Limit to max competitors
        self.competitors = self.competitors[:Config.MAX_COMPETITORS]
        
        print(f"Found {len(self.competitors)} competitor channels")
        return self.competitors
    
    def _extract_keywords(self):
        """Extract common keywords from video titles"""
        from collections import Counter
        import re
        
        # Combine all titles
        all_titles = ' '.join(self.channel_videos['title'].dropna().tolist())
        
        # Remove common words and split
        stop_words = {'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'being'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_titles.lower())
        
        # Filter and count
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)
        
        # Get top keywords
        top_keywords = [word for word, count in word_counts.most_common(10)]
        
        return top_keywords
    
    def _remove_duplicates(self, channels):
        """Remove duplicate channels"""
        seen = set()
        unique_channels = []
        
        for channel in channels:
            if channel['channel_id'] not in seen:
                seen.add(channel['channel_id'])
                unique_channels.append(channel)
        
        return unique_channels
    
    def fetch_competitor_videos(self):
        """Fetch videos from competitor channels"""
        competitor_videos = {}
        
        for competitor in self.competitors:
            channel_id = competitor['channel_id']
            print(f"Fetching videos from competitor: {competitor['title']}")
            
            videos = self.youtube_api.get_channel_videos(
                channel_id,
                max_results=20  # Fewer for competitors
            )
            
            competitor_videos[channel_id] = {
                'info': competitor,
                'videos': videos
            }
        
        return competitor_videos