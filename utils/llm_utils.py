import requests
import json
from config import Config

class OllamaClient:
    def __init__(self, host=None, model=None):
        raw_host = host or Config.OLLAMA_HOST
        # Ensure the protocol is present to avoid "No connection adapters"
        if raw_host and not raw_host.startswith('http'):
            self.host = f"http://{raw_host}"
        else:
            self.host = raw_host
        self.model = model or Config.LLM_MODEL
    
    def generate(self, prompt, system_prompt=None, temperature=0.0):
        """Generate text using Ollama"""
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "system": system_prompt or "You are a helpful YouTube content strategist.",
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=500)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.RequestException as e:
            print(f"Ollama API Error: {e}")
            # Fallback response
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt):
        """Fallback if Ollama is not available"""
        # Simple rule-based fallback
        if "video topic" in prompt.lower():
            return """
            {
                "title": "How AI is Transforming Content Creation",
                "description": "An in-depth look at how artificial intelligence is revolutionizing the way we create and consume digital content.",
                "script_sections": [
                    "Introduction to AI in content creation",
                    "Current applications and tools",
                    "Future possibilities",
                    "How to get started"
                ],
                "target_keywords": ["AI content creation", "artificial intelligence", "digital content", "automation"],
                "estimated_duration": "5-7 minutes"
            }
            """
        return "Unable to generate recommendation at this time."

class LLMOrchestrator:
    def __init__(self):
        self.client = OllamaClient()
    
    def generate_video_recommendation(self, analysis_data):
        """Generate video recommendation based on analysis"""
        system_prompt = """You are an expert YouTube content strategist with 10+ years of experience.
        Your task is to analyze YouTube channel data and recommend the TOP 5 video topics that will maximize views and engagement.
        Provide your response in valid JSON format with the following structure:
        {
            "recommendations": [
                {
                    "recommended_topic": "Specific video topic",
                    "rationale": "Detailed explanation of why this topic will perform well",
                    "target_title": "Click-worthy title (under 60 characters)",
                    "title_variations": ["Title 1", "Title 2", "Title 3"],
                    "description_template": "Full video description with placeholders",
                    "keywords": ["keyword1", "keyword2", "keyword3"],
                    "content_structure": ["Hook (0-30s)", "Main point 1", "Main point 2", "Main point 3", "Conclusion/Call to action"],
                    "estimated_duration": "X-Y minutes",
                    "thumbnail_ideas": ["Idea 1", "Idea 2"],
                    "estimated_engagement": {"Expected views": 10k-20k, "Engagement rate": 5-8%}
                }
            ]
        }
        """
        
        analysis_summary = self._format_analysis_for_llm(analysis_data)
        
        prompt = f"""Based on the following YouTube channel analysis, recommend the TOP 5 video topics:

{analysis_summary}

Consider:
1. What has performed well historically
2. What competitors are doing
3. Current trends in the niche
4. Content gaps in the channel
5. Engagement patterns

For each recommendation, provide estimated engagement metrics based on similar content performance.

Provide your recommendations in the specified JSON format."""

        response = self.client.generate(prompt, system_prompt)
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            result = json.loads(json_str)
            recommendations = result.get('recommendations', [])
            return recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse LLM response as JSON")
            # Return structured fallback
            fallback_rec = {
                "recommended_topic": "Industry Trends Analysis",
                "rationale": "Based on your channel's performance with educational content",
                "target_title": "Top Trends You Need to Know",
                "title_variations": ["Industry Secrets Revealed", "What Nobody Tells You"],
                "description_template": "In this video, we explore...",
                "keywords": ["trends", "analysis", "industry"],
                "content_structure": ["Introduction", "Trend 1", "Trend 2", "Trend 3", "Conclusion"],
                "estimated_duration": "8-10 minutes",
                "thumbnail_ideas": ["Eye-catching graphic with text overlay"],
                "estimated_engagement": "Expected views: 5k-10k, Engagement rate: 3-5%"
            }
            return [fallback_rec]
    
    def _format_analysis_for_llm(self, analysis_data):
        """Format analysis data for LLM consumption"""
        summary = []
        
        if 'channel_metrics' in analysis_data:
            metrics = analysis_data['channel_metrics']
            summary.append(f"Channel Metrics:")
            summary.append(f"- Total Videos: {metrics.get('total_videos', 0)}")
            summary.append(f"- Average Views: {metrics.get('avg_views', 0):.0f}")
            summary.append(f"- Average Engagement Rate: {metrics.get('avg_engagement_rate', 0):.3f}")
            summary.append(f"- Best Performing Video: {metrics.get('best_video', {}).get('title', 'N/A')}")
            summary.append(f"- Trending Topics: {', '.join(metrics.get('trending_topics', []))}")
        
        if 'content_analysis' in analysis_data:
            content = analysis_data['content_analysis']
            summary.append(f"\nContent Analysis:")
            summary.append(f"- Average Video Duration: {content.get('avg_duration_seconds', 0)/60:.1f} minutes")
        
        if 'temporal_analysis' in analysis_data:
            temporal = analysis_data['temporal_analysis']
            summary.append(f"\nTemporal Analysis:")
            summary.append(f"- Best Day to Post: {temporal.get('best_day', 'N/A')}")
            summary.append(f"- Best Hour to Post: {temporal.get('best_hour', 'N/A')}")
        
        if 'competitor_comparison' in analysis_data:
            competitors = analysis_data['competitor_comparison']
            summary.append(f"\nCompetitor Analysis:")
            for comp_id, comp_data in competitors.items():
                summary.append(f"- {comp_data.get('channel_title', 'Competitor')}: Avg {comp_data.get('avg_views', 0):.0f} views")
        
        if 'recommendations' in analysis_data:
            recs = analysis_data['recommendations']
            summary.append(f"\nInitial Recommendations:")
            for i, rec in enumerate(recs, 1):
                summary.append(f"{i}. {rec}")
        
        return '\n'.join(summary)
    
    def generate_script(self, recommendation):
        """Generate detailed video script from recommendation"""
        system_prompt = """You are a professional video scriptwriter. Create engaging, conversational scripts for YouTube videos.
        Format the script with clear sections and timing markers. Each section should be 1-2 paragraphs.
        Output in JSON format:
        {
            "video_title": "Final chosen title",
            "sections": [
                {
                    "section_title": "Hook/Introduction",
                    "content": "Full script text for this section",
                    "duration_seconds": 30,
                    "visual_prompt": "Description of what should be shown visually",
                    "speaking_style": "energetic, curious, authoritative, etc."
                }
            ],
            "total_duration_seconds": 600,
            "call_to_action": "Subscribe and like the video",
            "hashtags": ["#hashtag1", "#hashtag2"]
        }
        """
        
        prompt = f"""Create a complete video script based on this recommendation:

Topic: {recommendation.get('recommended_topic', 'General topic')}
Title: {recommendation.get('target_title', 'Video title')}
Structure: {recommendation.get('content_structure', [])}
Duration: {recommendation.get('estimated_duration', '5-7 minutes')}

Create a script that is engaging, informative, and suitable for YouTube. Include hooks, main content, and a call to action."""

        response = self.client.generate(prompt, system_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            script = json.loads(json_str)
            return script
            
        except json.JSONDecodeError:
            print("Failed to parse script as JSON")
            return self._create_fallback_script(recommendation)
    
    def _create_fallback_script(self, recommendation):
        """Create fallback script"""
        return {
            "video_title": recommendation.get('target_title', 'Amazing Video Title'),
            "sections": [
                {
                    "section_title": "Introduction",
                    "content": "Welcome everyone! In today's video, we're diving deep into an exciting topic that's been trending lately.",
                    "duration_seconds": 30,
                    "visual_prompt": "Host speaking to camera with engaging background",
                    "speaking_style": "energetic"
                },
                {
                    "section_title": "Main Content",
                    "content": "Let's break this down into three key points. First, the foundation. Second, the current applications. Third, future implications.",
                    "duration_seconds": 180,
                    "visual_prompt": "Text overlays, graphics, and relevant footage",
                    "speaking_style": "authoritative"
                },
                {
                    "section_title": "Conclusion",
                    "content": "To wrap up, remember these key takeaways. Implement what you've learned and share your results in the comments!",
                    "duration_seconds": 60,
                    "visual_prompt": "Host summarizing with key points on screen",
                    "speaking_style": "conversational"
                }
            ],
            "total_duration_seconds": 270,
            "call_to_action": "If you enjoyed this video, please like and subscribe for more content!",
            "hashtags": ["#education", "#learning", "#content"]
        }