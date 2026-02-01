import time
import traceback
from datetime import datetime
from agents.data_fetcher import DataFetcher
from agents.competitor_finder import CompetitorFinder
from agents.metrics_analyzer import MetricsAnalyzer
from agents.llm_recommender import LLMRecommender
from agents.script_formatter import ScriptFormatter
from agents.video_generator import VideoGenerator
from config import Config

class AutonomousPipeline:
    def __init__(self, channel_id=None, state_tracker=None):
        self.channel_id = channel_id or Config.CHANNEL_ID
        # Accept the global state dictionary from FastAPI
        self.state_tracker = state_tracker if state_tracker is not None else {}
        self.data = self.state_tracker.get("cached_data", {})
        self.results = {}
        self.top_videos = []
        
    def _update_ui(self, status=None, details=None):
        """Helper to push updates to the web dashboard state"""
        if status: self.state_tracker["status"] = status
        if details: self.state_tracker["details"] = details

    def run(self, generate_video=True, selected_index=None):
        """Run the complete pipeline with Dynamic Workflow"""
        print("=" * 60)
        print("Starting Autonomous YouTube Pipeline")
        print(f"Channel ID: {self.channel_id}")
        print(f"Timestamp: {datetime.now()}")
        print("=" * 60)

        try:
            # --- DYNAMIC WORKFLOW CHECK ---
            can_skip_analysis = (
                self.state_tracker.get("analysis_results") is not None
                and selected_index is not None
            )
            if can_skip_analysis:
                self._update_ui("Running", "Fast-tracking: Using cached analysis data...")
                analysis_results = self.state_tracker["analysis_results"]
            else:
                # Step 1: Fetch channel data
                self._update_ui("Running", "Step 1/6: Fetching channel statistics...")
                data_fetcher = DataFetcher(self.channel_id)
                channel_videos = data_fetcher.fetch_channel_data()

                channel_info = data_fetcher.fetch_channel_stats()
                self.state_tracker["stats"] = {
                    "channel_id": self.channel_id, 
                    "channel_name": channel_info.get("channel_name", "N/A"),
                    "channel_logo": channel_info.get("logo_url", ""),
                    "channel_description": channel_info.get("channel_description", "N/A"),
                    "subscribers": channel_info.get("subscriber_count", "N/A"),
                    "views": channel_info.get("total_views", "N/A"),
                    "videos": channel_info.get("total_videos", "N/A"),
                    "engagement": "Calculating..."
                }

                if channel_videos is None or channel_videos.empty:
                    self._update_ui("Failed", "No videos found for this channel.")
                    return None

                self.data["channel_videos"] = channel_videos

                # Step 2: Find and analyze competitors
                self._update_ui("Running", "Step 2/6: Identifying competitor trends...")
                competitor_finder = CompetitorFinder(channel_videos)
                competitors = competitor_finder.find_competitors()
                competitor_videos = competitor_finder.fetch_competitor_videos()

                self.data["competitors"] = competitors
                self.data["competitor_videos"] = competitor_videos

                # Step 3: Analyze metrics
                self._update_ui("Running", "Step 3/6: Analyzing engagement metrics...")
                metrics_analyzer = MetricsAnalyzer(channel_videos, competitor_videos)
                analysis_results = metrics_analyzer.analyze()

                # Cache results
                self.state_tracker["analysis_results"] = analysis_results
                self.state_tracker["recent_engagement"] = metrics_analyzer.recent_engagement()
                self.state_tracker["top_videos"] = metrics_analyzer.top_videos_by_engagement(5)

                avg_engagement = analysis_results["channel_metrics"].get(
                    "avg_engagement_rate", 0
                )
                self.state_tracker["stats"]["engagement"] = f"{avg_engagement:.2%}"

            # --- END OF DYNAMIC CHECK ---
            self.results["analysis"] = analysis_results

            # Step 4: LLM Recommendation
            self._update_ui("Running", "Step 4/6: LLM Agents generating strategy...")
            script = None
            

            is_fast_track = selected_index is not None
            if not is_fast_track:
                llm_recommender = LLMRecommender(analysis_results)
                self.state_tracker["recommendation_object"] = llm_recommender
                recommendations = llm_recommender.generate_recommendation()
                self.state_tracker["recommendations"] = recommendations
                self.state_tracker["recommendations_saved"] = False
                self._update_ui(
                    "Waiting",
                    "Recommendations ready. Select a video to generate."
                )
                print(recommendations)
            else:
                llm_recommender = self.state_tracker["recommendation_object"]
                recommendations = self.state_tracker["recommendations"]

            # Save recommendation ONLY if it was freshly generated
            if not self.state_tracker.get("recommendations_saved"):
                llm_recommender._save_recommendation()
                self.state_tracker["recommendations_saved"] = True
            self.results["recommendations"] = recommendations
            # ⛔ STOP HERE if no option selected
            if selected_index is None:
                self._update_ui(
                    "Waiting",
                    "Analysis complete. Please select a recommended video to generate."
                )
                self.results["script"] = None
                self.results["video_path"] = None
            if selected_index is not None:
                script = llm_recommender.generate_script(selected_index)
                llm_recommender._save_script()
                self.results["script"] = script

            if script is not None:
                self._update_ui("Running", "Step 5/6: Formatting script for production...")
                script_formatter = ScriptFormatter(script)
                formatted_script = script_formatter.format()
                self.results["formatted_script"] = formatted_script
            else:
                 self.results["formatted_script"] = None

            # Step 6: Generate video
            if generate_video and self.results.get("script"):
                self._update_ui(
                    "GeneratingVideo",
                    f"Step 6/6: Rendering video for Option {selected_index + 1}..."
                )
                video_generator = VideoGenerator(formatted_script)
                video_path = video_generator.generate()
                self.results["video_path"] = video_path
                self.state_tracker["video_path"] = video_path
                print(f"\n✅ Video generated successfully: {video_path}")
            else:
                self._update_ui(details="Skipping video generation...")
                self.results["video_path"] = None

            if selected_index is not None:
                self._update_ui(
                    "Completed",
                    f"Pipeline finished at {datetime.now().strftime('%H:%M:%S')}"
                )
                self._print_summary(selected_index)
                return self.results
            else:
                self._update_ui(
                    "Waiting",
                    "Select a recommendation to generate video."
                )

            self.state_tracker["last_run"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )


        except Exception as e:
            self._update_ui("Error", f"Pipeline failed: {str(e)}")
            traceback.print_exc()
            return None

    
    def _print_summary(self, selected_index):
        """Print pipeline summary to console"""
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE - SUMMARY")
        print("=" * 60)
        
        if 'analysis' in self.results:
            metrics = self.results['analysis'].get('channel_metrics', {})
            print(f"📊 Analyzed {metrics.get('total_videos', 0)} videos")
            print(f"📈 Average views: {metrics.get('avg_views', 0):.0f}")
            print(f"❤️  Average engagement rate: {metrics.get('avg_engagement_rate', 0):.3%}")
        
        if 'recommendations' in self.results and self.results['recommendations']:
            rec = self.results['recommendations'][selected_index]
            print(f"\n🎯 Recommended topic: {rec.get('recommended_topic', 'N/A')}")
            print(f"📝 Title: {rec.get('target_title', 'N/A')}")
        
        print("\n📁 Outputs saved in:", Config.OUTPUT_DIR)
        print("=" * 60)