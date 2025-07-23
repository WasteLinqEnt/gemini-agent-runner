import json
import logging
import subprocess
import threading
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from mangum import Mangum
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory storage for tasks. In a real-world scenario, use Redis or a database.
tasks = {}
LOG_DIR = "/tmp/gemini_logs"
os.makedirs(LOG_DIR, exist_ok=True)

class AnalysisRequest(BaseModel):
    ticket_url: str

class TaskInfo(BaseModel):
    task_id: str
    status: str
    start_time: float

class TaskStatus(TaskInfo):
    logs: list[str]

class FinalResult(TaskInfo):
    result: dict | None


def run_gemini_analysis(task_id: str, ticket_url: str):
    """
    Runs the gemini-cli analysis in a separate process and streams logs.
    """
    log_file = os.path.join(LOG_DIR, f"{task_id}.log")
    tasks[task_id]['status'] = 'RUNNING'
    
    prompt = (
        f"Please perform a full technical root cause analysis of the bug described in this Jira ticket: {ticket_url}. "
        "Follow the workflow outlined in your GEMINI.md file precisely. "
        "When you are finished, output the final analysis as a JSON object enclosed in triple backticks ```json ... ```"
    )

    command = [
        "gemini-cli",
        "--yolo",
        "--debug",
        prompt
    ]

    try:
        with open(log_file, "w") as f:
            process = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        tasks[task_id]['process'] = process
        process.wait() # Wait for the process to complete

        # After completion, parse the result from the log file
        with open(log_file, "r") as f:
            full_log = f.read()
            json_result = parse_result_from_log(full_log)
            tasks[task_id]['result'] = json_result

        tasks[task_id]['status'] = 'COMPLETED' if process.returncode == 0 else 'FAILED'

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        tasks[task_id]['status'] = 'FAILED'
        with open(log_file, "a") as f:
            f.write(f"\n\nERROR: {e}")
    finally:
        logger.info(f"Task {task_id} finished with status: {tasks[task_id]['status']}")


def parse_result_from_log(log_content: str) -> dict | None:
    """
    Parses the final JSON object from the log content.
    """
    try:
        json_block_match = re.search(r"```json\n(.*?)\n```", log_content, re.DOTALL)
        if json_block_match:
            json_string = json_block_match.group(1)
            return json.loads(json_string)
    except Exception as e:
        logger.error(f"Could not parse JSON from log: {e}")
    return None


@app.post("/start-analysis", response_model=TaskInfo)
def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Starts a new analysis task in the background.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'status': 'PENDING',
        'start_time': time.time(),
        'result': None
    }
    
    background_tasks.add_task(run_gemini_analysis, task_id, request.ticket_url)
    
    return TaskInfo(task_id=task_id, status='PENDING', start_time=tasks[task_id]['start_time'])


@app.get("/status/{task_id}", response_model=TaskStatus)
def get_status(task_id: str):
    """
    Polls for the status and logs of a running task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    log_file = os.path.join(LOG_DIR, f"{task_id}.log")
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = f.read().splitlines()
            
    return TaskStatus(
        task_id=task_id,
        status=task['status'],
        start_time=task['start_time'],
        logs=logs
    )


@app.get("/result/{task_id}", response_model=FinalResult)
def get_result(task_id: str):
    """
    Retrieves the final structured result of a completed task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task['status'] not in ['COMPLETED', 'FAILED']:
        raise HTTPException(status_code=400, detail=f"Task is still in progress with status: {task['status']}")
    
    return FinalResult(
        task_id=task_id,
        status=task['status'],
        start_time=task['start_time'],
        result=task.get('result')
    )

# Mangum is an adapter for running ASGI applications in AWS Lambda
handler = Mangum(app)