from fastapi import FastAPI, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid
import re

app = FastAPI()

DOWNLOAD_DIR = "/app/downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

TASKS = {}

def sanitize_filename(name: str) -> str:
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name)
    return " ".join(clean_name.split())

def download_task(task_id: str, url: str):
    output_path = os.path.join(DOWNLOAD_DIR, f"{task_id}.mp4")
    
    # LIMITATION 1080p ICI
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Video')
            channel_name = info_dict.get('uploader', 'Channel')
            
        safe_title = sanitize_filename(video_title)
        safe_channel = sanitize_filename(channel_name)
        final_filename = f"{safe_title} - {safe_channel}.mp4"
        
        TASKS[task_id] = {
            "status": "done",
            "filepath": output_path,
            "filename": final_filename
        }
        
    except Exception as e:
        TASKS[task_id] = {
            "status": "error",
            "error_msg": str(e)
        }

def cleanup_file(filepath: str, task_id: str):
    if os.path.exists(filepath):
        os.remove(filepath)
    if task_id in TASKS:
        del TASKS[task_id]

@app.post("/start")
async def start_download(url: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"status": "pending"}
    background_tasks.add_task(download_task, task_id, url)
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return {"status": TASKS[task_id]["status"]}

@app.get("/file/{task_id}")
async def get_file(task_id: str, background_tasks: BackgroundTasks = BackgroundTasks()):
    if task_id not in TASKS or TASKS[task_id]["status"] != "done":
        raise HTTPException(status_code=400, detail="Le fichier n'est pas encore prêt")
        
    file_info = TASKS[task_id]
    
    # Nettoyage après l'envoi
    background_tasks.add_task(cleanup_file, file_info["filepath"], task_id)
    
    return FileResponse(
        path=file_info["filepath"], 
        media_type='video/mp4', 
        filename=file_info["filename"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)