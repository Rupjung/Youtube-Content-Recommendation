import os
import time
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import *
# import soundfile as sf
# from kokoro_onnx import Kokoro


from config import Config


class VideoGenerator:
    def __init__(self, formatted_script):
        self.script = formatted_script
        self.video_path = None
        self.assets_dir = os.path.join(Config.OUTPUT_DIR, 'temp_assets')
        os.makedirs(self.assets_dir, exist_ok=True)
        self.headers = {
    "ngrok-skip-browser-warning": "69420"
        }

        
        # Kaggle Worker URL (get this from ngrok when you run the Kaggle notebook)
        self.kaggle_worker_url = getattr(Config, 'KAGGLE_WORKER_URL', None)
        if not self.kaggle_worker_url:
            print("WARNING: KAGGLE_WORKER_URL not found in config. "
                  "Please set it to your Kaggle worker's public URL (from ngrok)")


    def _check_kaggle_worker_health(self):
        """Check if Kaggle worker is running and healthy"""
        try:
            response = requests.get(
                f"{self.kaggle_worker_url}/health",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Kaggle Worker Status: {data}")
                return True
            return False
        except Exception as e:
            print(f"❌ Kaggle Worker Health Check Failed: {e}")
            return False

    def _generate_video_assets(self):
        """Generate short video clips using Kaggle GPU worker (SD + SVD)"""
        asset_paths = []

        if not self._check_kaggle_worker_health():
            print("⚠️ Kaggle worker not available, falling back to static images")
            return self._generate_images()

        for i, section in enumerate(self.script['sections']):
            print(f"🎬 Kaggle Worker: Requesting video for section {i+1}...")
            visual_prompt = section.get('visual_prompt', 'Cinematic scenery, high quality, smooth motion')

            try:
                fps = getattr(Config, 'VIDEO_FPS', 7)
                # If we have the audio file, use its duration for the video length
                if 'audio_file' in section:
                    audio_duration = AudioFileClip(section['audio_file']).duration
                    num_frames = int(audio_duration * fps)
                    num_frames = min(num_frames, 25) # Safety cap for Kaggle
                else:
                    num_frames = getattr(Config, 'VIDEO_NUM_FRAMES', 14)

                response = requests.post(
                    f"{self.kaggle_worker_url}/generate-video",
                    json={
                        "prompt": visual_prompt,
                        "num_frames": num_frames,
                        "fps": fps,
                        "motion_bucket_id": getattr(Config, 'MOTION_BUCKET_ID', 127),
                        "noise_aug_strength": getattr(Config, 'NOISE_AUG_STRENGTH', 0.02)
                    },
                    headers=self.headers,
                    timeout=500 
                )

                if response.status_code == 200:
                    result = response.json()
                    video_file = os.path.join(self.assets_dir, f"video_{i}.mp4")
                    full_download_url = f"{self.kaggle_worker_url}{result['download_url']}"
                    
                    self._download_file(full_download_url, video_file)
                    asset_paths.append(video_file)
                    section['asset_type'] = 'video'
                    print(f"   ✅ Video downloaded: {video_file}")
                else:
                    raise Exception(f"Worker Error: {response.text}")

            except Exception as e:
                print(f"⚠️ Kaggle Video Failed: {e}. Falling back to image.")
                image_file = os.path.join(self.assets_dir, f"fallback_{i}.jpg")
                self._generate_placeholder_image(visual_prompt, image_file)
                asset_paths.append(image_file)
                section['asset_type'] = 'image'

        return asset_paths

    def _download_file(self, url, save_path):
        """Download file from URL"""
        try:
            r = requests.get(url, stream=True, timeout=60)
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            print(f"Download failed: {e}")
            raise
    
    def generate(self):
        print("Starting video generation...")
        
        audio_clips = self._generate_audio()
        
        # 2. Generate video clips from Kaggle worker
        asset_paths = self._generate_video_assets() 
        
        # 3. Create video clips using the generated assets
        video_clips = self._create_video_clips(asset_paths, audio_clips)
        
        # 4. Final assembly
        final_video = self._combine_clips(video_clips)
        
        if self._has_background_music():
            final_video = self._add_background_music(final_video)
        
        final_video = self._add_intro_outro_pil(final_video)
        
        self.video_path = self._export_video(final_video)
        self._cleanup()
        
        print(f"Video generated successfully: {self.video_path}")
        return self.video_path
    
    def _create_text_image(self, base_image_path, text, fontsize=50, color='white'):
        """Helper to overlay text on an image using PIL instead of MoviePy TextClip"""
        with Image.open(base_image_path).convert("RGBA") as base:
            txt_layer = Image.new("RGBA", base.size, (0,0,0,0))
            draw = ImageDraw.Draw(txt_layer)
            
            # Use a robust font path for Colab
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", fontsize)
            except:
                font = ImageFont.load_default()

            # Wrap text if it's too long
            import textwrap
            lines = textwrap.wrap(text, width=30)
            
            # Calculate total height for centering
            line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
            total_height = sum(line_heights) + (10 * (len(lines) - 1))
            current_y = (base.height - total_height) // 2

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                x = (base.width - w) // 2
                
                # Draw shadow for readability
                draw.text((x+3, current_y+3), line, font=font, fill=(0,0,0,180))
                # Draw main text
                draw.text((x, current_y), line, font=font, fill=color)
                current_y += bbox[3] + 10

            out = Image.alpha_composite(base, txt_layer)
            # Return as numpy array for MoviePy
            return np.array(out.convert("RGB"))
        
    def _generate_audio(self):
        """Offload Kokoro TTS generation to Kaggle GPU worker"""
        audio_files = []

        if not self._check_kaggle_worker_health():
            print("⚠️ Kaggle worker offline. Audio generation will fail.")

        for i, section in enumerate(self.script['sections']):
            print(f"🎙️ Kaggle Worker: Generating audio for section {i+1}...")
            
            text = section['content']
            audio_file = os.path.join(self.assets_dir, f"audio_{i}.wav")

            try:
                # Request audio from Kaggle
                response = requests.post(
                    f"{self.kaggle_worker_url}/generate-audio",
                    json={
                        "text": text,
                        "voice": getattr(Config, "KOKORO_VOICE", "af_bella"),
                        "speed": getattr(Config, "KOKORO_SPEED", 1.0)
                    },
                    headers=self.headers,
                    timeout=120  # Audio is faster than video but give it 2 mins
                )

                if response.status_code == 200:
                    # Save the raw binary audio data sent by Kaggle
                    with open(audio_file, "wb") as f:
                        f.write(response.content)
                    
                    audio_files.append(audio_file)
                    section['audio_file'] = audio_file
                    print(f"   ✅ Audio received: {audio_file}")
                else:
                    print(f"❌ Failed to get audio: {response.text}")
                    raise Exception(f"Kaggle returned error {response.status_code}")

            except Exception as e:
                print(f"⚠️ Kaggle Audio Failed: {e}. Falling back to silence.")
                self._create_silent_audio(audio_file, section.get('duration', 5))
                audio_files.append(audio_file)

        return audio_files

    
    def _create_silent_audio(self, filepath, duration):
        """Create silent audio as fallback"""
        from moviepy.audio.AudioClip import AudioClip
        import numpy as np

        # Create a clip where every frame is 0 (silence)
        # The lambda takes 't' (time) but returns 0 for all t
        silent_clip = AudioClip(lambda t: [0, 0], duration=duration, fps=22050)
        
        silent_clip.write_audiofile(filepath, fps=22050)
        silent_clip.close()
    
    def _generate_images(self):
        """Generate images for each section (fallback method)"""
        image_files = []
        
        for i, section in enumerate(self.script['sections']):
            print(f"Generating image for section {i+1}...")
            
            image_file = os.path.join(self.assets_dir, f"image_{i}.jpg")
            
            try:
                # Generate placeholder image
                self._generate_placeholder_image(
                    section.get('visual_prompt', 'Abstract background'),
                    image_file
                )
                
            except Exception as e:
                print(f"Error generating image: {e}")
                # Create simple colored background
                self._create_colored_background(image_file)
            
            image_files.append(image_file)
            
            # Update script with actual image file
            section['image_file'] = image_file
        
        return image_files
    
    def _generate_placeholder_image(self, prompt, output_path):
        """Generate a placeholder image with text overlay"""
        # Create a colored background
        colors = [
            (41, 128, 185),  # Blue
            (39, 174, 96),   # Green
            (142, 68, 173),  # Purple
            (230, 126, 34),  # Orange
            (231, 76, 60)    # Red
        ]
        
        color = colors[hash(prompt) % len(colors)]
        
        # Create image
        img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), color=color)
        draw = ImageDraw.Draw(img)
        
        # Add some text (simplified)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Create a text overlay
        words = prompt.split()[:5]
        text = ' '.join(words)
        
        # Center text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (Config.VIDEO_WIDTH - text_width) // 2
        y = (Config.VIDEO_HEIGHT - text_height) // 2
        
        # Draw text with shadow
        shadow_color = (0, 0, 0, 128)
        draw.text((x+2, y+2), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill='white')
        
        # Save image
        img.save(output_path, quality=95)
    
    def _create_colored_background(self, output_path):
        """Create simple colored background"""
        colors = ['#3498db', '#2ecc71', '#9b59b6', '#e67e22', '#e74c3c']
        color = colors[len(output_path) % len(colors)]
        
        img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), color=color)
        img.save(output_path)
    
    def _create_video_clips(self, asset_paths, audio_files):
        """Creates clips and adjusts Narration Volume"""
        video_clips = []
        # Volume level for the narration (1.0 is default, 1.2 is 20% boost)
        NARRATION_VOLUME = getattr(Config, 'NARRATION_VOLUME', 1.2)

        for i, (asset_path, audio_file) in enumerate(zip(asset_paths, audio_files)):
            section = self.script['sections'][i]
            
            # Load audio and apply volume boost
            audio_clip = AudioFileClip(audio_file).volumex(NARRATION_VOLUME)
            
            if asset_path.endswith('.mp4'):
                clip = VideoFileClip(asset_path).subclip(0, audio_clip.duration)
            else:
                frame = self._create_text_image(asset_path, section.get('title', ''))
                clip = ImageClip(frame).set_duration(audio_clip.duration)
            
            clip = clip.set_audio(audio_clip)
            video_clips.append(clip)
        return video_clips
    
    def _combine_clips(self, video_clips):
        """Combine all video clips"""
        if not video_clips:
            # Create empty clip as fallback
            return ColorClip(
                size=(Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT),
                color=(0, 0, 0),
                duration=10
            )
        
        final_video = concatenate_videoclips(video_clips, method="compose")
        return final_video
    
    def _has_background_music(self):
        """Check if background music is available"""
        bg_music_path = getattr(Config, 'BACKGROUND_MUSIC_PATH', None)
        return bg_music_path and os.path.exists(bg_music_path)
    
    def _add_background_music(self, video_clip):
        """Add background music with specific volume level (ducking)"""
        try:
            bg_music_path = getattr(Config, 'BACKGROUND_MUSIC_PATH', None)
            if not bg_music_path or not os.path.exists(bg_music_path):
                return video_clip

            bg_music = AudioFileClip(bg_music_path)
            
            if bg_music.duration < video_clip.duration:
                bg_music = afx.audio_loop(bg_music, duration=video_clip.duration)
            else:
                bg_music = bg_music.subclip(0, video_clip.duration)

            # Lower background music volume (e.g., 0.1 for 10% volume)
            BG_VOLUME = getattr(Config, 'BG_MUSIC_VOLUME', 0.1)
            bg_music = bg_music.volumex(BG_VOLUME)
            
            if video_clip.audio:
                # Combine narration and background music
                combined_audio = CompositeAudioClip([video_clip.audio, bg_music])
                video_clip = video_clip.set_audio(combined_audio)
            else:
                video_clip = video_clip.set_audio(bg_music)
            
        except Exception as e:
            print(f"Error adding background music: {e}")
        
        return video_clip
    
    def _add_intro_outro_pil(self, video_clip):
        """Add simple intro and outro using PIL-rendered frames"""
        try:
            # Intro Frame
            intro_img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), color=(30, 30, 30))
            intro_path = os.path.join(self.assets_dir, "intro_temp.jpg")
            intro_img.save(intro_path)
            
            intro_title = self.script.get('metadata', {}).get('title', 'Your Video')
            intro_frame = self._create_text_image(intro_path, intro_title, fontsize=70)
            intro_clip = ImageClip(intro_frame).set_duration(2)

            # Outro Frame
            outro_img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), color=(30, 30, 30))
            outro_path = os.path.join(self.assets_dir, "outro_temp.jpg")
            outro_img.save(outro_path)
            
            cta = self.script.get('call_to_action', 'Thanks for watching!')
            outro_frame = self._create_text_image(outro_path, cta, fontsize=50)
            outro_clip = ImageClip(outro_frame).set_duration(3)

            return concatenate_videoclips([intro_clip, video_clip, outro_clip], method="compose")
        except Exception as e:
            print(f"Error adding intro/outro: {e}")
            return video_clip
    
    def _export_video(self, video_clip):
        """Export final video"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(Config.VIDEO_DIR, f"generated_video_{timestamp}.mp4")
        
        print(f"Exporting video to: {output_path}")
        
        # Export with reasonable settings for YouTube
        video_clip.write_videofile(
            output_path,
            fps=Config.FPS,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            threads=4,
            preset='medium',
            ffmpeg_params=['-crf', '23']  # Good quality
        )
        
        video_clip.close()
        
        return output_path
    
    def _cleanup(self):
        """Cleanup temporary files"""
        try:
            import shutil
            if os.path.exists(self.assets_dir):
                shutil.rmtree(self.assets_dir)
        except Exception as e:
            print(f"Cleanup error: {e}")