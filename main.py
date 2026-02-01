#!/usr/bin/env python3
"""
Autonomous YouTube Pipeline - Main Entry Point
"""

import argparse
import sys
import os
import json
import numpy as np  # Added for type handling
from datetime import datetime
from orchestrator import AutonomousPipeline
from config import Config

# --- Added Encoder Class ---
class NpEncoder(json.JSONEncoder):
    """Custom encoder to handle NumPy types during JSON serialization"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def main():
    parser = argparse.ArgumentParser(
        description='Autonomous YouTube Content Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --channel UC_x5XG1OV2P6uZZ5FSM9Ttw
  %(prog)s --no-video
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        '--channel',
        type=str,
        default=Config.CHANNEL_ID,
        help='YouTube Channel ID (default: from .env)'
    )
    
    parser.add_argument(
        '--no-video',
        action='store_true',
        help='Skip video generation (analysis only)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Custom output directory'
    )
    
    args = parser.parse_args()
    
    # Validate YouTube API key
    if not Config.YOUTUBE_API_KEY or Config.YOUTUBE_API_KEY == 'your_youtube_api_key_here':
        print("❌ Error: YouTube API key not configured.")
        print("Please set YOUTUBE_API_KEY in .env file")
        print("Get an API key from: https://console.cloud.google.com/")
        sys.exit(1)
    
    # Validate channel ID
    if not args.channel or args.channel == 'your_channel_id_here':
        print("❌ Error: Channel ID not configured.")
        print("Please set CHANNEL_ID in .env file or use --channel argument")
        sys.exit(1)
    
    # Update config if custom output directory
    if args.output_dir:
        Config.OUTPUT_DIR = args.output_dir
        os.makedirs(args.output_dir, exist_ok=True)
    
    print("🚀 Starting Autonomous YouTube Pipeline")
    print(f"📺 Channel: {args.channel}")
    print(f"🎥 Video Generation: {'Disabled' if args.no_video else 'Enabled'}")
    print("-" * 50)
    
    try:
        # Run pipeline
        pipeline = AutonomousPipeline(args.channel)
        results = pipeline.run(generate_video=not args.no_video)
        
        if results:
            print("\n✅ Pipeline completed successfully!")
            
            summary_file = os.path.join(
                Config.OUTPUT_DIR,
                f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Prepare clean summary (remove large data)
            clean_results = {}
            for key, value in results.items():
                if key not in ['channel_videos', 'competitor_videos']:
                    clean_results[key] = value
            
            # --- Updated json.dump to use the NpEncoder ---
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(clean_results, f, indent=2, ensure_ascii=False, cls=NpEncoder)
            
            print(f"📄 Summary saved to: {summary_file}")
            
            sys.exit(0)
        else:
            print("\n❌ Pipeline failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()