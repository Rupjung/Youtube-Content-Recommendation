import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # YouTube API
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    
  
    KAGGLE_WORKER_URL = "https://magniloquent-uninstated-miesha.ngrok-free.dev"  # Your ngrok URL
    
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.getenv('DATA_DIR', os.path.join(BASE_DIR, 'data'))
    RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
    OUTPUT_DIR = os.path.join(DATA_DIR, 'outputs')
    VIDEO_DIR = os.getenv('VIDEO_DIR')
    
    # Ensure directories exist
    for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # LLM Settings
    LLM_MODEL = os.getenv('LLM_MODEL', 'gemma3:270m')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    
    # Video Settings
    VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1280))
    VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 720))
    FPS = int(os.getenv('FPS', 30))

    # Audio settings
    NARRATION_VOLUME = 1.2  # 1.0 = normal, 1.2 = 20% louder
    BG_MUSIC_VOLUME = 0.1   # 0.1 = 10% volume for background music
    BACKGROUND_MUSIC_PATH = None  # Path to your background music file (optional)
    
    # Analysis Settings
    MAX_VIDEOS_TO_ANALYZE = 50
    MAX_COMPETITORS = 5
    COMMENTS_PER_VIDEO = 10
    
    # Video Generation
    SECTION_DURATION = 10  # seconds per script section
    VOICE_LANGUAGE = 'en'
    VOICE_SLOW = False

    #Voice ID
    ELEVENLABS_VOICE_ID = os.getenv('VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default voice ID

    VIDEO_STYLE = "cyberpunk"  # Options: "cyberpunk", "minimalist", "noir", "documentary"
    
    STYLE_CONFIG = {
        "cyberpunk": "Neon-lit streets, high contrast, wet asphalt reflections, purple and cyan color palette, futuristic tech, cinematic anamorphic lens flares.",
        "minimalist": "Clean white backgrounds, soft natural shadows, Scandinavian design, muted earth tones, slow steady camera movements, high-key lighting.",
        "noir": "Black and white, dramatic shadows (chiaroscuro), moody atmospheric fog, 35mm film grain, high contrast, detective aesthetic.",
        "documentary": "Handheld camera feel, natural lighting, realistic textures, raw color grading, sharp focus, 4k detail."
    }

    # Video generation settings (optimized for T4 GPU memory)
    VIDEO_NUM_FRAMES = 14  # Number of frames for SVD (14 frames = ~2 seconds at 7fps)
                           # Don't exceed 14 on free T4 GPU to avoid OOM errors
    VIDEO_FPS = 7          # FPS for generated video clips
    MOTION_BUCKET_ID = 127 # Motion intensity (0-255, higher = more motion)
    NOISE_AUG_STRENGTH = 0.02  # Noise augmentation (0.0-1.0, lower = cleaner)
