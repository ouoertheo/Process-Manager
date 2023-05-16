import json
import subprocess, psutil, pathlib, os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
import uvicorn

MAX_LOG_LENGTH = 1000

module_path = pathlib.Path(__file__).resolve().parent
os.chdir(module_path)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load the process definitions from a JSON file
with open('processes.json') as f:
    processes = json.load(f)

# Store the running processes in a dictionary
running_processes = {}

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

# Start a process
def start_process(name, command):
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    running_processes[name] = {'process': proc, 'status': 'running', 'logs':[]}


# Stop a process
def stop_process(name):
    proc = running_processes[name]['process']
    kill(proc.pid)
    del running_processes[name]


# Get the status of a process
def get_process_status(name):
    if name in running_processes:
        proc = running_processes[name]['process']
        if proc.poll() is None:
            return 'running'
        else:
            return 'stopped'
    else:
        return 'stopped'


# Get the stdout logs of a process
def start_process_logging(name):
    proc = running_processes[name]['process']
    while True:
        try:
            if proc.poll() is not None :
                break
            outputline = proc.stdout.readline().strip()
            running_processes[name]['logs'].append(outputline)
        except:
            continue

def get_process_logs(name):
    if name in running_processes:
        logs = running_processes[name]['logs'][-MAX_LOG_LENGTH:]
        logs.reverse()
        return logs
    else:
        return []

# Get the list of all processes
def get_all_processes():
    output = []
    for name in processes:
        output.append({
            'name': name,
            'status': get_process_status(name),
            'logs': get_process_logs(name)
        })
    return output


# Define the API endpoints

@app.get('/processes', response_model=list[dict])
def list_processes():
    return get_all_processes()


@app.get('/processes/{name}', response_model=dict)
def get_process(name: str):
    if name in processes:
        return {'name': name, 'status': get_process_status(name)}
    else:
        raise HTTPException(status_code=404, detail='Process not found')


def start_process_background(name: str):
    if name in processes:
        start_process(name, processes[name])


@app.post('/processes/{name}/start', status_code=201)
def start_process_api(name: str, background_tasks: BackgroundTasks):
    start_process_background(name)
    background_tasks.add_task(start_process_logging, name)
    return RedirectResponse(url="/")


def stop_process_background(name: str):
    if name in processes:
        if get_process_status(name) == 'running':
            stop_process(name)


@app.post('/processes/{name}/stop', status_code=204)
def stop_process_api(name: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(stop_process_background, name)
    return RedirectResponse(url="/")


# Define the route for the web UI

@app.get('/', response_class=HTMLResponse)
@app.post('/', response_class=HTMLResponse)
def index(request: Request):
    process_data = get_all_processes()
    return templates.TemplateResponse('index.html', {'request': request, 'processes': process_data})


if __name__ == '__main__':
    uvicorn.run(app, port=5005, host="0.0.0.0")
