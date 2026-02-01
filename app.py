import os
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from orchestrator import AutonomousPipeline
from config import Config
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

templates = Jinja2Templates(directory=TEMPLATES_DIR)



# Global state that the UI polls
pipeline_state = {
    "status": "Idle",
    "last_run": "Never",
    "details": "Ready to launch agents.",
    "stats": {},
    "top_videos": [],
    "recommendations": [], # Ensure this is initialized for the UI
    "analysis_results": None, # This is what triggers the Fast-track skip
    "target_index": None,
    "video_path": None,      # filesystem path
    "video_url": None        # browser-accessible URL
}






def clean_for_json(obj):
    """Recursively convert numpy types to native python types, excluding non-serializable objects."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            # Skip known non-serializable keys (e.g., objects stored for internal use)
            if k in ["recommendation_object"]:  # Add other keys as needed
                continue
            cleaned[k] = clean_for_json(v)
        return cleaned
    elif isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def run_pipeline_worker(channel_id, index=None):
    """
    Unified worker for both initial runs and selected generations.
    Using one worker reduces code duplication and potential bugs.
    """
    global pipeline_state
    try:
        # Store the current index so the UI knows which card to update
        pipeline_state["target_index"] = index
        pipeline_state["video_path"] = None
        pipeline_state["video_url"] = None
        pipeline = AutonomousPipeline(channel_id, state_tracker=pipeline_state)
        # If index is None, it runs discovery + Option 1
        # If index is 1 or 2, it fast-tracks to that specific video
        pipeline.run(generate_video=True, selected_index=index)

        # If video was generated, expose it to UI
        video_path = pipeline_state.get("video_path")
        if video_path and os.path.exists(video_path):
            # Normalize path for URL usage
            video_url = "/" + video_path.replace("\\", "/")
            pipeline_state["video_url"] = video_url
    except Exception as e:
        pipeline_state["status"] = "Error"
        pipeline_state["details"] = f"Pipeline Error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": pipeline_state.get("stats", {}),
        "pipeline": pipeline_state
    })

@app.post("/api/start")
async def start_pipeline(payload: dict, background_tasks: BackgroundTasks):
    if pipeline_state["status"] == "Running":
        return JSONResponse(status_code=400, content={"message": "Pipeline active"})
    
    channel_id = payload.get("channel_id", Config.CHANNEL_ID)
    # Clear old results but keep the structure
    pipeline_state["status"] = "Running"
    pipeline_state["analysis_results"] = None 
    pipeline_state["recommendations"] = []
    pipeline_state["video_path"] = None
    pipeline_state["video_url"] = None
    
    background_tasks.add_task(run_pipeline_worker, channel_id)
    return {"message": "Pipeline initiated"}

@app.post("/api/generate_selected")
async def generate_selected(payload: dict, background_tasks: BackgroundTasks):
    # index will be 0, 1, or 2 from the frontend
    index = payload.get("index")
    
    if index is None:
        return JSONResponse(status_code=400, content={"message": "No index provided"})

    # Check if we have analysis data before trying to fast-track
    if not pipeline_state.get("analysis_results"):
         return JSONResponse(status_code=400, content={"message": "Please run initial analysis first"})

    channel_id = pipeline_state.get("stats", {}).get("channel_id", Config.CHANNEL_ID)
    
    pipeline_state["status"] = "Running"
    pipeline_state["details"] = f"Fast-tracking: Generating video for Option {index + 1}..."
    pipeline_state["video_path"] = None
    pipeline_state["video_url"] = None
    
    # We reuse run_pipeline_worker but pass the index
    background_tasks.add_task(run_pipeline_worker, channel_id, index)
    return {"message": f"Generation for Option {index + 1} started"}

@app.get("/api/status")
async def get_status():
    return clean_for_json(pipeline_state)