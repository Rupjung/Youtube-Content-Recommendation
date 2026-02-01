import json
from datetime import datetime
from utils.llm_utils import LLMOrchestrator
from config import Config
import os

class LLMRecommender:
    def __init__(self, analysis_data):
        self.analysis_data = analysis_data
        self.llm_orchestrator = LLMOrchestrator()
        self.recommendation = None
        self.script = None
    
    def generate_recommendation(self):
        """Generate video recommendation using LLM"""
        print("Generating video recommendation with LLM...")
        
        # Get recommendation from LLM
        self.recommendation = self.llm_orchestrator.generate_video_recommendation(
            self.analysis_data
        )
        
        print("Recommendation generated successfully")
        return self.recommendation
    
    def generate_script(self, index):
        """Generate script based on recommendation at given index"""
        if self.recommendation is None:
            raise ValueError("Recommendation must be generated first")
        
        print("Generating script based on recommendation...")
        self.script = self.llm_orchestrator.generate_script(self.recommendation[index])
        
        print("Script generated successfully")
        return self.script
    
    def _save_recommendation(self):
        """Save recommendation to file"""
        if self.recommendation is None:
            raise ValueError("Recommendation must be generated first")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rec_file = os.path.join(Config.OUTPUT_DIR, f"recommendation_{timestamp}.json")
        with open(rec_file, 'w', encoding='utf-8') as f:
            json.dump(self.recommendation, f, indent=2, ensure_ascii=False)
        
        print(f"Recommendation saved to: {rec_file}")
        return rec_file
    
    def _save_script(self):
        """Save script to file"""
        if self.script is None:
            raise ValueError("Script must be generated first")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_file = os.path.join(Config.OUTPUT_DIR, f"script_{timestamp}.json")
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(self.script, f, indent=2, ensure_ascii=False)
        
        print(f"Script saved to: {script_file}")
        return script_file