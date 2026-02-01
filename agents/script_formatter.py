import json
from config import Config
from datetime import datetime
import os

class ScriptFormatter:
    def __init__(self, script_data):
        self.script = script_data
        self.formatted_script = None
    
    def format(self):
        """Format script for video generation"""
        print("Formatting script for video generation...")
        
        # Ensure script has required structure
        if not self.script or 'sections' not in self.script:
            self.script = self._create_default_script()
        
        # Format each section
        formatted_sections = []
        for i, section in enumerate(self.script['sections']):
            formatted_section = self._format_section(section, i)
            formatted_sections.append(formatted_section)
        
        self.formatted_script = {
            'metadata': {
                'title': self.script.get('video_title', 'Generated Video'),
                'total_duration': self.script.get('total_duration_seconds', 300),
                'created_at': datetime.now().isoformat()
            },
            'sections': formatted_sections,
            'call_to_action': self.script.get('call_to_action', ''),
            'hashtags': self.script.get('hashtags', [])
        }
        
        # Save formatted script
        self._save_formatted_script()
        
        return self.formatted_script
    
    def _format_section(self, section, index):
        """Format a single script section"""
        return {
            'section_number': index + 1,
            'title': section.get('section_title', f'Section {index + 1}'),
            'content': section.get('content', ''),
            'duration': section.get('duration_seconds', Config.SECTION_DURATION),
            'visual_prompt': section.get('visual_prompt', 'Relevant background image'),
            'speaking_style': section.get('speaking_style', 'conversational'),
            'audio_file': f"section_{index + 1}.mp3",
            'image_file': f"section_{index + 1}.jpg"
        }
    
    def _create_default_script(self):
        """Create default script if none provided"""
        return {
            'video_title': 'AI Generated Video',
            'sections': [
                {
                    'section_title': 'Introduction',
                    'content': 'Welcome to this AI-generated video. Today we explore amazing topics.',
                    'duration_seconds': 30,
                    'visual_prompt': 'Abstract technology background',
                    'speaking_style': 'energetic'
                },
                {
                    'section_title': 'Main Content',
                    'content': 'Here are the key points you need to know about this fascinating subject.',
                    'duration_seconds': 180,
                    'visual_prompt': 'Infographics and text overlays',
                    'speaking_style': 'authoritative'
                },
                {
                    'section_title': 'Conclusion',
                    'content': 'Thank you for watching. Remember to apply what you learned today!',
                    'duration_seconds': 30,
                    'visual_prompt': 'Clean modern background',
                    'speaking_style': 'friendly'
                }
            ],
            'total_duration_seconds': 240,
            'call_to_action': 'Like and subscribe for more!',
            'hashtags': ['#AI', '#Content', '#Education']
        }
    
    def _save_formatted_script(self):
        """Save formatted script to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(Config.OUTPUT_DIR, f"formatted_script_{timestamp}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.formatted_script, f, indent=2, ensure_ascii=False)
        
        print(f"Formatted script saved to: {filepath}")