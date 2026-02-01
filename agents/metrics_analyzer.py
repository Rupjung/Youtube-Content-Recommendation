import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import os

class MetricsAnalyzer:
    def __init__(self, channel_videos_df, competitor_videos=None):
        self.channel_videos = channel_videos_df
        self.competitor_videos = competitor_videos or {}
        self.analysis_results = {}
    
    def analyze(self):
        """Perform comprehensive analysis"""
        print("Analyzing metrics...")
        
        # Ensure we have engagement_rate column
        self._ensure_metrics_columns()
        
        self.analysis_results = {
            'channel_metrics': self._analyze_channel_metrics(),
            'content_analysis': self._analyze_content(),
            'temporal_analysis': self._analyze_temporal_patterns(),
            'competitor_comparison': self._compare_with_competitors(),
            'recommendations': self._generate_recommendations()
        }
        
        return self.analysis_results
    
    def _ensure_metrics_columns(self):
        """Ensure all required metric columns exist"""
        df = self.channel_videos
        
        # Create engagement_rate if it doesn't exist
        if 'engagement_rate' not in df.columns:
            if 'likes' in df.columns and 'comments_count' in df.columns and 'views' in df.columns:
                df['engagement_rate'] = (df['likes'] + df['comments_count']) / df['views'].replace(0, 1)
            else:
                df['engagement_rate'] = 0
        
        # Ensure other required columns exist
        if 'likes' not in df.columns:
            df['likes'] = 0
        
        if 'comments_count' not in df.columns:
            df['comments_count'] = 0
        
        if 'views' not in df.columns:
            df['views'] = 0
        
        if 'title' not in df.columns:
            df['title'] = ''

    def top_videos_by_engagement(self, top_n=5):
        """Return top N videos ranked by engagement_rate (desc)."""
        self._ensure_metrics_columns()
        df = self.channel_videos

        if 'engagement_rate' not in df.columns or df.empty:
            return []

        sorted_df = df.sort_values(by='engagement_rate', ascending=False)

        return (
            sorted_df
            .head(top_n)[['title', 'engagement_rate']]
            .to_dict(orient='records')
        )

    def recent_engagement(self, top_n=5):
        """Return top N most recent videos with their engagement rates."""
        self._ensure_metrics_columns()
        df = self.channel_videos

        if df.empty:
            return []

        # Check if published_at exists and convert to datetime
        if 'published_at' in df.columns:
            try:
                df = df.copy()
                df['published_at'] = pd.to_datetime(df['published_at'])
                sorted_df = df.sort_values(by='published_at', ascending=False)
            except Exception as e:
                print(f"Error parsing published_at: {e}")
                # Fall back to original order
                sorted_df = df
        else:
            # If no published_at, just take the first N (assuming they are in order)
            sorted_df = df.head(top_n)

        # Get the top N recent videos
        recent_videos = sorted_df.head(top_n)

        # Return titles and engagement rates
        return (
            recent_videos[['title', 'engagement_rate']]
            .to_dict(orient='records')
        )

    
    def _analyze_channel_metrics(self):
        """Calculate key channel metrics"""
        df = self.channel_videos
        
        metrics = {
            'total_videos': len(df),
            'total_views': df['views'].sum() if 'views' in df.columns else 0,
            'avg_views': df['views'].mean() if 'views' in df.columns else 0,
            'avg_likes': df['likes'].mean() if 'likes' in df.columns else 0,
            'avg_comments': df['comments_count'].mean() if 'comments_count' in df.columns else 0,
            'avg_engagement_rate': df['engagement_rate'].mean() if 'engagement_rate' in df.columns else 0,
            'best_video': self._get_best_performing_video(df),
            'worst_video': self._get_worst_performing_video(df),
            'trending_topics': self._extract_trending_topics(df)
        }
        
        return metrics
    
    def _get_best_performing_video(self, df):
        """Identify best performing video"""
        # Use a composite score
        if 'views' in df.columns and 'likes' in df.columns and 'comments_count' in df.columns:
            views_max = df['views'].max() if df['views'].max() > 0 else 1
            likes_max = df['likes'].max() if df['likes'].max() > 0 else 1
            comments_max = df['comments_count'].max() if df['comments_count'].max() > 0 else 1
            
            df['performance_score'] = (
                df['views'] / views_max * 0.4 +
                df['likes'] / likes_max * 0.3 +
                df['comments_count'] / comments_max * 0.3
            )
            
            best_idx = df['performance_score'].idxmax()
            best_video = df.loc[best_idx]
        else:
            # Return default if columns don't exist
            return {
                'title': 'No video data',
                'views': 0,
                'likes': 0,
                'performance_score': 0
            }
        
        return {
            'title': best_video['title'] if 'title' in best_video else 'Unknown',
            'description': best_video['description'] if 'description' in best_video else '',
            'views': int(best_video['views']) if 'views' in best_video else 0,
            'likes': int(best_video['likes']) if 'likes' in best_video else 0,
            'performance_score': best_video['performance_score'] if 'performance_score' in best_video else 0
        }
    
    def _get_worst_performing_video(self, df):
        """Identify worst performing video"""
        # Consider videos with at least some views
        if 'engagement_rate' in df.columns and 'views' in df.columns:
            if len(df) > 0:
                # Filter out videos with very low views
                if df['views'].quantile(0.1) > 0:
                    df_filtered = df[df['views'] > df['views'].quantile(0.1)]
                    if len(df_filtered) > 0:
                        worst_idx = df_filtered['engagement_rate'].idxmin()
                        worst_video = df.loc[worst_idx]
                    else:
                        worst_idx = df['engagement_rate'].idxmin()
                        worst_video = df.loc[worst_idx]
                else:
                    worst_idx = df['engagement_rate'].idxmin()
                    worst_video = df.loc[worst_idx]
            else:
                return {
                    'title': 'No video data',
                    'views': 0,
                    'likes': 0,
                    'engagement_rate': 0
                }
        else:
            return {
                'title': 'No video data',
                'views': 0,
                'likes': 0,
                'engagement_rate': 0
            }
        
        return {
            'title': worst_video['title'] if 'title' in worst_video else 'Unknown',
            'views': int(worst_video['views']) if 'views' in worst_video else 0,
            'likes': int(worst_video['likes']) if 'likes' in worst_video else 0,
            'engagement_rate': worst_video['engagement_rate'] if 'engagement_rate' in worst_video else 0
        }
    
    def _extract_trending_topics(self, df):
        """Extract trending topics from titles"""
        from collections import Counter
        import re
        
        # Check if we have titles
        if 'title' not in df.columns or df['title'].isna().all():
            return []
        
        # Combine recent video titles (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=100)
        
        # Check if published_at exists
        if 'published_at' in df.columns:
            try:
                df['published_at'] = pd.to_datetime(df['published_at'])
                recent_videos = df[df['published_at'] > recent_cutoff]
            except:
                recent_videos = df.nlargest(10, 'published_at') if 'published_at' in df.columns else df
        else:
            recent_videos = df.head(10)
        
        if len(recent_videos) == 0:
            recent_videos = df.head(10)
        
        titles = ' '.join(recent_videos['title'].fillna('').tolist())
        words = re.findall(r'\b[a-zA-Z]{4,}\b', titles.lower())
        
        # Common YouTube stopwords
        stop_words = {
            'video', 'watch', 'youtube', 'channel', 'subscribe',
            'episode', 'part', 'full', 'review', 'react', 'reaction'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(10)]
    
    def _analyze_content(self):
        """Analyze content patterns"""
        df = self.channel_videos
        
        # Title length analysis
        df['title_length'] = df['title'].str.len() if 'title' in df.columns else 0
        avg_title_length = df['title_length'].mean() if 'title_length' in df.columns else 0
        
        # Duration analysis (simplified)
        df['duration_seconds'] = df['duration'].apply(self._parse_duration) if 'duration' in df.columns else 300
        
        # Topic clustering
        topics = self._cluster_topics(df)
        
        return {
            'avg_title_length': avg_title_length,
            'avg_duration_seconds': df['duration_seconds'].mean() if 'duration_seconds' in df.columns else 300,
            'topics': topics
        }
    
    def _parse_duration(self, duration):
        """Parse ISO 8601 duration to seconds"""
        import re
        
        if not isinstance(duration, str):
            return 300  # Default 5 minutes
        
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration)
        
        if not match:
            return 300
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _cluster_topics(self, df):
        """Cluster videos into topics"""
        if len(df) < 3 or 'title' not in df.columns:
            return {}
        
        # Use TF-IDF for title analysis
        vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        try:
            title_vectors = vectorizer.fit_transform(df['title'].fillna(''))
            
            # Perform K-means clustering
            n_clusters = min(5, len(df))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            df['topic_cluster'] = kmeans.fit_predict(title_vectors)
            
            # Extract representative words for each cluster
            clusters = {}
            for cluster_id in range(n_clusters):
                cluster_titles = df[df['topic_cluster'] == cluster_id]['title'].tolist()
                if cluster_titles:
                    clusters[f'topic_{cluster_id}'] = {
                        'count': len(cluster_titles),
                        'sample_titles': cluster_titles[:3]
                    }
            
            return clusters
            
        except Exception as e:
            print(f"Clustering error: {e}")
            return {}
    
    def _analyze_temporal_patterns(self):
        """Analyze time-based patterns"""
        df = self.channel_videos.copy()
        
        # Check if published_at exists
        if 'published_at' not in df.columns:
            return {
                'best_day': None,
                'best_hour': None,
                'day_performance': {},
                'hour_performance': {}
            }
        
        try:
            df['published_at'] = pd.to_datetime(df['published_at'])
            
            # Day of week analysis
            df['day_of_week'] = df['published_at'].dt.day_name()
            day_performance = df.groupby('day_of_week')['engagement_rate'].mean().to_dict()
            
            # Hour of day analysis
            df['hour_of_day'] = df['published_at'].dt.hour
            hour_performance = df.groupby('hour_of_day')['engagement_rate'].mean().to_dict()
            
            # Find best day and hour
            best_day = max(day_performance, key=day_performance.get) if day_performance else None
            best_hour = max(hour_performance, key=hour_performance.get) if hour_performance else None
            
            return {
                'best_day': best_day,
                'best_hour': best_hour,
                'day_performance': day_performance,
                'hour_performance': hour_performance
            }
            
        except Exception as e:
            print(f"Temporal analysis error: {e}")
            return {
                'best_day': None,
                'best_hour': None,
                'day_performance': {},
                'hour_performance': {}
            }
    
    def _compare_with_competitors(self):
        """Compare metrics with competitors"""
        if not self.competitor_videos:
            return {}
        
        comparisons = {}
        
        for channel_id, data in self.competitor_videos.items():
            competitor_videos = data.get('videos', [])
            if not competitor_videos:
                continue
            
            comp_df = pd.DataFrame(competitor_videos)
            
            # Calculate engagement rate for competitor videos
            if 'likes' in comp_df.columns and 'comments_count' in comp_df.columns and 'views' in comp_df.columns:
                comp_df['engagement_rate'] = (comp_df['likes'] + comp_df['comments_count']) / comp_df['views'].replace(0, 1)
            
            comparisons[channel_id] = {
                'channel_title': data.get('info', {}).get('title', 'Unknown'),
                'avg_views': comp_df['views'].mean() if 'views' in comp_df.columns else 0,
                'avg_likes': comp_df['likes'].mean() if 'likes' in comp_df.columns else 0,
                'avg_engagement_rate': comp_df['engagement_rate'].mean() if 'engagement_rate' in comp_df.columns else 0,
                'video_count': len(comp_df),
                'best_video': self._get_best_performing_video(comp_df)
            }
        
        return comparisons
    
    def _generate_recommendations(self):
        """Generate initial recommendations based on analysis"""
        channel_metrics = self._analyze_channel_metrics()
        content_analysis = self._analyze_content()
        temporal_analysis = self._analyze_temporal_patterns()
        competitor_comparison = self._compare_with_competitors()
        
        recommendations = []
        
        # Content recommendations
        if 'topics' in content_analysis:
            topics = content_analysis['topics']
            if topics:
                # Recommend creating content in popular topics
                for topic_id, topic_data in topics.items():
                    if topic_data['count'] > 2:  # If there are multiple videos in this topic
                        recommendations.append(
                            f"Create more content similar to: {topic_data['sample_titles'][0]}"
                        )
        
        # Timing recommendations
        if temporal_analysis['best_day'] and temporal_analysis['best_hour']:
            recommendations.append(
                f"Publish on {temporal_analysis['best_day']} at {temporal_analysis['best_hour']}:00 for better engagement"
            )
        
        # Performance-based recommendations
        best_video = channel_metrics['best_video']
        worst_video = channel_metrics['worst_video']
        
        if best_video['title'] != 'No video data':
            recommendations.append(
                f"Create more videos like '{best_video['title']}' (high performance)"
            )
        
        if worst_video['title'] != 'No video data':
            recommendations.append(
                f"Avoid topics/approaches similar to '{worst_video['title']}' (low engagement)"
            )
        
        # Competitor insights
        if competitor_comparison:
            for comp_id, comp_data in competitor_comparison.items():
                if comp_data['avg_views'] > channel_metrics.get('avg_views', 0):
                    recommendations.append(
                        f"Analyze {comp_data['channel_title']}'s successful content strategies. Its best performing video is {comp_data['best_video']['title']} with description as {comp_data['best_video']['description']}."
                    )
        
        return recommendations
