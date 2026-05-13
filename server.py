from fastapi import FastAPI, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List
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
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            eta = d.get('_eta_str', '').strip()
            
            # Update existing entry if it exists
            if task_id in TASKS:
                TASKS[task_id].update({
                    "status": "downloading",
                    "percent": re.sub(r'\x1b\[[0-9;]*m', '', percent), # Remove ANSI colors
                    "eta": re.sub(r'\x1b\[[0-9;]*m', '', eta)
                })
                # Capture title 
                if d.get('info_dict') and 'title' in d['info_dict']:
                    TASKS[task_id]["title"] = d['info_dict']['title']
    
    # LIMITATION 1080p
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Video')
            channel_name = info_dict.get('uploader', 'Channel')
            
        safe_title = sanitize_filename(video_title)
        safe_channel = sanitize_filename(channel_name)
        final_filename = f"{safe_title} - {safe_channel}.mp4"
        
        TASKS[task_id].update({
            "status": "done",
            "filepath": output_path,
            "filename": final_filename
        })
        
    except Exception as e:
        TASKS[task_id].update({
            "status": "error",
            "error_msg": str(e)
        })

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
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]

class TaskList(BaseModel):
    task_ids: List[str]

@app.post("/status/batch")
async def get_batch_status(tasks: TaskList):
    result = []
    for tid in tasks.task_ids:
        if tid in TASKS:
            task_info = dict(TASKS[tid])
            task_info["id"] = tid
            result.append(task_info)
        else:
            result.append({"id": tid, "status": "not_found"})
    return {"tasks": result}

@app.get("/file/{task_id}")
async def get_file(task_id: str, background_tasks: BackgroundTasks = BackgroundTasks()):
    if task_id not in TASKS or TASKS[task_id]["status"] != "done":
        raise HTTPException(status_code=400, detail="File is not ready yet")
        
    file_info = TASKS[task_id]
    
    # Cleanup after sending
    background_tasks.add_task(cleanup_file, file_info["filepath"], task_id)
    
    return FileResponse(
        path=file_info["filepath"], 
        media_type='video/mp4', 
        filename=file_info["filename"]
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Downloads</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                padding: 20px; 
                background: #1c1c1e; /* Dark background iOS */
                color: #f2f2f7; 
                margin: 0;
            }
            h2 { font-size: 28px; margin-bottom: 20px; font-weight: 700; }
            .task { 
                background: #2c2c2e; 
                margin-bottom: 15px; 
                padding: 16px; 
                border-radius: 14px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            .title { font-weight: 600; margin-bottom: 8px; font-size: 16px; line-height: 1.3; }
            .status { font-size: 14px; color: #8e8e93; font-weight: 500; }
            .progress-bar { 
                background: #3a3a3c; 
                border-radius: 6px; 
                height: 8px; 
                margin-top: 12px; 
                overflow: hidden; 
            }
            .progress-fill { 
                background: #0a84ff; /* Apple Blue */
                height: 100%; 
                width: 0%; 
                transition: width 0.4s ease-out; 
            }
        </style>
    </head>
    <body>
        <h2>YT DL iOS Shortcut Dashboard📡</h2>
        <div id="tasks">Fetching data...</div>

        <script>
            // Get URLs from URL (?ids=uuid1,uuid2)
            const urlParams = new URLSearchParams(window.location.search);
            const idsParam = urlParams.get('ids');
            const taskIds = idsParam ? idsParam.split(',').filter(id => id.trim() !== '') : [];
            
            const tasksDiv = document.getElementById('tasks');
            let autoRedirected = false; // Safety to redirect only once

            async function fetchStatus() {
                if (taskIds.length === 0) {
                    tasksDiv.innerHTML = "<div class='task'><div class='title'>No downloads in queue.</div></div>";
                    return;
                }
                
                try {
                    const response = await fetch('/status/batch', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task_ids: taskIds })
                    });
                    const data = await response.json();
                    
                    let html = '';
                    let isEverythingFinished = true; // Assume everything is finished by default
                    let hasAtLeastOneDone = false;
                    
                    data.tasks.forEach(task => {
                        let title = task.title || "Fetching video info...";
                        let statusText = "";
                        let progressHtml = "";
                        
                        if (task.status === 'done') {
                            statusText = "✅ Done and ready!";
                            hasAtLeastOneDone = true;
                        } else if (task.status === 'downloading') {
                            statusText = `⏳ Downloading: ${task.percent} (Remaining: ${task.eta})`;
                            let percentNum = parseFloat(task.percent) || 0;
                            progressHtml = `<div class="progress-bar"><div class="progress-fill" style="width: ${percentNum}%;"></div></div>`;
                            isEverythingFinished = false; // Still active
                        } else if (task.status === 'pending') {
                            statusText = "🕒 Starting...";
                            isEverythingFinished = false; // Still active
                        } else if (task.status === 'error') {
                            statusText = `❌ Error: ${task.error_msg}`;
                        } else {
                            statusText = "Ticket expired or not found";
                        }
                        
                        html += `
                        <div class="task">
                            <div class="title">${title}</div>
                            <div class="status">${statusText}</div>
                            ${progressHtml}
                        </div>`;
                    });
                    
                    tasksDiv.innerHTML = html;
                    
                    // --- AUTOMATIC REDIRECTION ---
                    if (hasAtLeastOneDone && isEverythingFinished && !autoRedirected) {
                        autoRedirected = true; // Prevents multiple redirections
                        
                        // Display visual indicator
                        tasksDiv.innerHTML += `
                        <div style="text-align:center; margin-top: 25px; color: #34c759; font-weight: 600; font-size: 17px; animation: pulse 1.5s infinite;">
                            📥 Opening automatically...
                        </div>
                        <style>@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }</style>
                        `;
                        
                        // Silent launch of iOS shortcut after brief delay (800ms)
                        setTimeout(() => {
                            window.location.href = "shortcuts://run-shortcut?name=Get%20downloaded%20videos";
                        }, 800);
                    }
                    
                } catch (e) {
                    console.error("Server connection error", e);
                }
            }

            // Immediate launch then every 1.5 seconds
            fetchStatus();
            setInterval(fetchStatus, 1500);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)