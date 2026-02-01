import requests
import json
from config import Config

class OllamaClient:
    def __init__(self, host=None, model=None):
        raw_host = host or getattr(Config, 'OLLAMA_HOST', 'http://localhost:11434')
        
        # Ensure the protocol is present to avoid "No connection adapters"
        if raw_host and not raw_host.startswith('http'):
            self.host = f"http://{raw_host}"
        else:
            self.host = raw_host
            
        # Remove trailing slash if present
        self.host = self.host.rstrip('/')
        
        self.model = model or getattr(Config, 'LLM_MODEL', 'llama3.2:3b')
        
        print(f"🤖 OllamaClient initialized")
        print(f"   Host: {self.host}")
        print(f"   Model: {self.model}")
    
    def check_connection(self):
        """Check if Ollama server is accessible"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Connected to Ollama server")
                models = response.json().get('models', [])
                print(f"   Available models: {len(models)}")
                return True
            else:
                print(f"⚠️ Ollama server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Ollama server: {e}")
            print(f"   Make sure Kaggle Ollama notebook is running")
            return False
    
    def generate(self, prompt, system_prompt=None, temperature=0.7, format="json"):
        """Generate text using Ollama"""
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are a helpful YouTube content strategist.",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2048  # Max tokens to generate
            }
        }
        
        # Add format only if requested (some models don't support it)
        if format:
            payload["format"] = format
        
        try:
            print(f"🔄 Generating response from {self.model}...")
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('response', '')
            
            # Log stats
            if 'total_duration' in result:
                duration_sec = result['total_duration'] / 1e9  # nanoseconds to seconds
                print(f"✅ Generated in {duration_sec:.2f}s")
            
            return generated_text
            
        except requests.exceptions.Timeout:
            print(f"⏱️ Request timed out after 120s")
            return self._fallback_response(prompt)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama API Error: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt):
        """Fallback if Ollama is not available"""
        print("⚠️ Using fallback response")
        
        # Simple rule-based fallback
        if "video topic" in prompt.lower() or "recommendation" in prompt.lower():
            return """
            {
                "recommendations": [
                    {
                        "recommended_topic": "How AI is Transforming Content Creation",
                        "rationale": "AI and automation are trending topics with high engagement potential based on your channel's educational focus.",
                        "target_title": "AI Content Creation: Complete Guide 2024",
                        "title_variations": [
                            "How AI Changed Content Creation Forever",
                            "AI Tools Every Creator Needs in 2024",
                            "The Future of Content: AI Revolution"
                        ],
                        "description_template": "In this comprehensive guide, we explore how artificial intelligence is revolutionizing content creation. From automated editing to AI-generated scripts, discover the tools and techniques that will transform your workflow.",
                        "keywords": ["AI content creation", "artificial intelligence", "content automation", "creator tools"],
                        "content_structure": [
                            "Hook: Show amazing AI result (0-15s)",
                            "Introduction to AI in content (15-60s)",
                            "Top 5 AI tools breakdown (1-4 min)",
                            "Real examples and results (4-6 min)",
                            "How to get started (6-7 min)",
                            "Call to action (7-8 min)"
                        ],
                        "estimated_duration": "7-8 minutes",
                        "thumbnail_ideas": [
                            "Split screen: human vs AI creation",
                            "Futuristic AI brain with 'MIND BLOWN' text"
                        ],
                        "estimated_engagement": {
                            "Expected views": "10k-25k",
                            "Engagement rate": "5-8%"
                        }
                    }
                ]
            }
            """
        elif "script" in prompt.lower():
            return """
            {
                "video_title": "Amazing AI Video",
                "sections": [
                    {
                        "section_title": "Hook",
                        "content": "What if I told you that AI could completely transform the way you create content? In the next few minutes, I'm going to show you exactly how.",
                        "duration_seconds": 15,
                        "visual_prompt": "Futuristic AI graphics, fast cuts, energetic music",
                        "speaking_style": "energetic"
                    },
                    {
                        "section_title": "Introduction",
                        "content": "Welcome back to the channel! Today we're diving deep into the world of AI-powered content creation. Whether you're a beginner or a seasoned creator, these tools will save you hours of work.",
                        "duration_seconds": 30,
                        "visual_prompt": "Host speaking to camera, friendly environment",
                        "speaking_style": "conversational"
                    },
                    {
                        "section_title": "Main Content",
                        "content": "Let's break this down into three major areas. First, AI for video editing - tools like Descript and Runway ML. Second, AI for scriptwriting and ideation. And third, AI for thumbnail creation and optimization.",
                        "duration_seconds": 180,
                        "visual_prompt": "Screen recordings of tools, before/after comparisons",
                        "speaking_style": "authoritative"
                    },
                    {
                        "section_title": "Conclusion",
                        "content": "So there you have it - the complete guide to AI content creation. Remember, these tools are here to enhance your creativity, not replace it. Start with one tool, master it, then expand.",
                        "duration_seconds": 45,
                        "visual_prompt": "Host summarizing, key points on screen",
                        "speaking_style": "conversational"
                    },
                    {
                        "section_title": "Call to Action",
                        "content": "If you found this helpful, smash that like button and subscribe for more AI tutorials. Drop a comment below telling me which tool you're most excited to try!",
                        "duration_seconds": 20,
                        "visual_prompt": "Animated subscribe button, end screen",
                        "speaking_style": "energetic"
                    }
                ],
                "total_duration_seconds": 290,
                "call_to_action": "Like, subscribe, and comment!",
                "hashtags": ["#AI", "#ContentCreation", "#CreatorTips"]
            }
            """
        
        return '{"error": "Unable to generate response. Please check Ollama server connection."}'


class LLMOrchestrator:
    def __init__(self):
        self.client = OllamaClient()
        
        # Check connection on init
        if not self.client.check_connection():
            print("⚠️ Warning: Ollama server not accessible. Will use fallback responses.")
    
    def generate_video_recommendation(self, analysis_data):
        """Generate video recommendation based on analysis"""
        system_prompt = """You are an expert YouTube content strategist with 10+ years of experience.
Your task is to analyze YouTube channel data and recommend the TOP 5 video topics that will maximize views and engagement.

IMPORTANT: Respond with ONLY valid JSON, no markdown formatting, no code blocks, no extra text.

Provide your response in this exact JSON structure:
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
            "estimated_engagement": {"Expected views": "10k-20k", "Engagement rate": "5-8%"}
        }
    ]
}"""
        
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

Respond with ONLY the JSON structure, nothing else."""

        response = self.client.generate(
            prompt, 
            system_prompt,
            temperature=0.7,
            format="json"
        )
        
        try:
            # Try to parse the response as JSON
            # Handle potential markdown code blocks
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])  # Remove first and last line
            
            # Find JSON boundaries
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                recommendations = result.get('recommendations', [])
                
                if recommendations:
                    print(f"✅ Generated {len(recommendations)} recommendations")
                    return recommendations
                else:
                    print("⚠️ No recommendations in response, using fallback")
                    return self._get_fallback_recommendations()
            else:
                print("⚠️ No valid JSON found in response")
                return self._get_fallback_recommendations()
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM response as JSON: {e}")
            print(f"   Response preview: {response[:200]}...")
            return self._get_fallback_recommendations()
    
    def _get_fallback_recommendations(self):
        """Return structured fallback recommendations"""
        fallback_recs = [
            {
                "recommended_topic": "Industry Trends Analysis",
                "rationale": "Based on your channel's performance with educational content, trend analysis videos typically generate 30% higher engagement",
                "target_title": "Top 5 Trends You Need to Know in 2024",
                "title_variations": [
                    "Industry Secrets Nobody Talks About",
                    "What Nobody Tells You About [Industry]",
                    "The Future of [Industry]: Trends to Watch"
                ],
                "description_template": "In this video, we explore the top trends shaping [industry] in 2024. From emerging technologies to shifting market dynamics, discover what you need to know to stay ahead.",
                "keywords": ["trends", "analysis", "industry", "2024"],
                "content_structure": [
                    "Hook: Surprising trend reveal (0-15s)",
                    "Introduction (15-60s)",
                    "Trend #1 breakdown (1-2 min)",
                    "Trend #2 breakdown (2-4 min)",
                    "Trend #3 breakdown (4-6 min)",
                    "Conclusion & predictions (6-7 min)",
                    "Call to action (7-8 min)"
                ],
                "estimated_duration": "7-8 minutes",
                "thumbnail_ideas": [
                    "Eye-catching graphic with \"TOP 5\" and trend icons",
                    "Split screen showing past vs future"
                ],
                "estimated_engagement": {
                    "Expected views": "5k-15k",
                    "Engagement rate": "4-6%"
                }
            }
        ]
        return fallback_recs
    
    def _format_analysis_for_llm(self, analysis_data):
        """Format analysis data for LLM consumption"""
        summary = []
        
        if 'channel_metrics' in analysis_data:
            metrics = analysis_data['channel_metrics']
            summary.append("Channel Metrics:")
            summary.append(f"- Total Videos: {metrics.get('total_videos', 0)}")
            summary.append(f"- Average Views: {metrics.get('avg_views', 0):.0f}")
            summary.append(f"- Average Engagement Rate: {metrics.get('avg_engagement_rate', 0):.3f}")
            
            best_video = metrics.get('best_video', {})
            if best_video:
                summary.append(f"- Best Performing Video: {best_video.get('title', 'N/A')} ({best_video.get('views', 0)} views)")
            
            trending = metrics.get('trending_topics', [])
            if trending:
                summary.append(f"- Trending Topics: {', '.join(trending)}")
        
        if 'content_analysis' in analysis_data:
            content = analysis_data['content_analysis']
            avg_duration = content.get('avg_duration_seconds', 0)
            if avg_duration:
                summary.append(f"\nContent Analysis:")
                summary.append(f"- Average Video Duration: {avg_duration/60:.1f} minutes")
        
        if 'temporal_analysis' in analysis_data:
            temporal = analysis_data['temporal_analysis']
            summary.append(f"\nTemporal Analysis:")
            summary.append(f"- Best Day to Post: {temporal.get('best_day', 'N/A')}")
            summary.append(f"- Best Hour to Post: {temporal.get('best_hour', 'N/A')}")
        
        if 'competitor_comparison' in analysis_data:
            competitors = analysis_data['competitor_comparison']
            summary.append(f"\nCompetitor Analysis:")
            for comp_id, comp_data in competitors.items():
                channel_title = comp_data.get('channel_title', 'Competitor')
                avg_views = comp_data.get('avg_views', 0)
                summary.append(f"- {channel_title}: Avg {avg_views:.0f} views")
        
        if 'recommendations' in analysis_data:
            recs = analysis_data['recommendations']
            summary.append(f"\nInitial Recommendations:")
            for i, rec in enumerate(recs[:3], 1):  # Top 3 only
                summary.append(f"{i}. {rec}")
        
        return '\n'.join(summary)
    
    def generate_script(self, recommendation):
        """Generate detailed video script from recommendation"""
        system_prompt = """You are a professional video scriptwriter for YouTube. 
Create engaging, conversational scripts that hook viewers and keep them watching.

IMPORTANT: Respond with ONLY valid JSON, no markdown formatting, no code blocks, no extra text.

Format the script with clear sections and timing markers. Each section should be detailed and engaging.
Output in this exact JSON format:
{
    "video_title": "Final chosen title",
    "sections": [
        {
            "section_title": "Hook/Introduction",
            "content": "Full script text for this section (2-3 paragraphs)",
            "duration_seconds": 30,
            "visual_prompt": "Description of what should be shown visually",
            "speaking_style": "energetic, curious, authoritative, etc."
        }
    ],
    "total_duration_seconds": 600,
    "call_to_action": "Subscribe and like the video",
    "hashtags": ["#hashtag1", "#hashtag2"]
}"""
        
        topic = recommendation.get('recommended_topic', 'General topic')
        title = recommendation.get('target_title', 'Video title')
        structure = recommendation.get('content_structure', [])
        duration = recommendation.get('estimated_duration', '5-7 minutes')
        
        prompt = f"""Create a complete, engaging video script for YouTube based on this recommendation:

Topic: {topic}
Title: {title}
Structure: {', '.join(structure)}
Target Duration: {duration}

Requirements:
1. Start with a STRONG hook in the first 15 seconds
2. Use conversational, engaging language
3. Include natural transitions between sections
4. Add specific examples and actionable advice
5. End with a clear call to action

Respond with ONLY the JSON structure, nothing else."""

        response = self.client.generate(
            prompt,
            system_prompt,
            temperature=0.8,  # More creative for scripts
            format="json"
        )
        
        try:
            # Clean up response
            response = response.strip()
            
            # Remove markdown code blocks
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            
            # Extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                script = json.loads(json_str)
                
                print(f"✅ Generated script with {len(script.get('sections', []))} sections")
                return script
            else:
                print("⚠️ No valid JSON in script response, using fallback")
                return self._create_fallback_script(recommendation)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse script as JSON: {e}")
            return self._create_fallback_script(recommendation)
    
    def _create_fallback_script(self, recommendation):
        """Create fallback script"""
        topic = recommendation.get('recommended_topic', 'Amazing Video Topic')
        title = recommendation.get('target_title', 'Amazing Video Title')
        
        return {
            "video_title": title,
            "sections": [
                {
                    "section_title": "Hook",
                    "content": f"What if I told you that {topic.lower()} could completely change everything you know? In the next few minutes, I'm going to reveal something that will blow your mind. Stay tuned!",
                    "duration_seconds": 15,
                    "visual_prompt": "Fast cuts, energetic visuals, dramatic music",
                    "speaking_style": "energetic"
                },
                {
                    "section_title": "Introduction",
                    "content": f"Welcome back to the channel! Today we're diving deep into {topic}. Whether you're a complete beginner or already familiar with this, I guarantee you'll learn something new that you can apply right away.",
                    "duration_seconds": 30,
                    "visual_prompt": "Host speaking to camera with engaging background",
                    "speaking_style": "conversational"
                },
                {
                    "section_title": "Main Content - Part 1",
                    "content": f"Let's start with the fundamentals. When it comes to {topic}, there are three critical things you need to understand. First, the foundation. This is where most people get it wrong, and I'm going to show you exactly how to do it right.",
                    "duration_seconds": 90,
                    "visual_prompt": "Relevant footage, graphics explaining concepts",
                    "speaking_style": "authoritative"
                },
                {
                    "section_title": "Main Content - Part 2",
                    "content": "Second, let's talk about practical application. I've tested this extensively, and here's what actually works. I'm going to share real examples and show you step-by-step how to implement this yourself.",
                    "duration_seconds": 120,
                    "visual_prompt": "Screen recordings, demonstrations, examples",
                    "speaking_style": "instructional"
                },
                {
                    "section_title": "Main Content - Part 3",
                    "content": "Third, and this is crucial - the common mistakes to avoid. I've made these myself, and I've seen countless others fall into the same traps. Save yourself the headache and watch out for these pitfalls.",
                    "duration_seconds": 90,
                    "visual_prompt": "Warning graphics, examples of mistakes",
                    "speaking_style": "advisory"
                },
                {
                    "section_title": "Conclusion",
                    "content": f"So there you have it - everything you need to know about {topic}. Remember, the key is to start small, be consistent, and don't be afraid to experiment. You've got this!",
                    "duration_seconds": 45,
                    "visual_prompt": "Host summarizing with key points displayed",
                    "speaking_style": "conversational"
                },
                {
                    "section_title": "Call to Action",
                    "content": "If you found this helpful, make sure to hit that like button - it really helps the channel grow. Subscribe for more content like this, and drop a comment below telling me what you want to see next. I read every single one!",
                    "duration_seconds": 20,
                    "visual_prompt": "Animated subscribe button, end screen elements",
                    "speaking_style": "energetic"
                }
            ],
            "total_duration_seconds": 410,
            "call_to_action": "Like, subscribe, and comment below!",
            "hashtags": ["#Tutorial", "#HowTo", "#Educational"]
        }