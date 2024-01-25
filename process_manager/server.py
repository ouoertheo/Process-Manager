import sys

sys.path.insert(0, "./")
import pathlib, os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
import uvicorn

from process_manager.manager import ProcessManager
from process_manager.process_model import (
    ProcessDefinitionList,
    Process,
)

module_path = pathlib.Path(__file__).resolve().parent
os.chdir(module_path)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
process_manager = ProcessManager()


@app.get(
    "/static/{filename}",
    response_class=FileResponse,
    status_code=200,
)
def static_files(filename: str):
    if filename.endswith(".js"):
        return FileResponse(
            f"static/{filename}", headers={"Content-Type": "application/javascript"}
        )
    if filename.endswith(".css"):
        return FileResponse(f"static/{filename}", headers={"Content-Type": "text/css"})
    if filename.endswith(".ico"):
        return FileResponse(
            f"static/{filename}", headers={"Content-Type": "image/x-icon"}
        )
    return FileResponse(f"static/{filename}")


# Define the API endpoints
@app.get("/processes")
def list_processes() -> list[Process]:
    processes = process_manager.list_processes()
    return processes


@app.get("/processes/{name}", response_model=Process)
def get_process(name: str):
    try:
        return process_manager.get_process(name=name)
    except:
        raise HTTPException(status_code=404, detail="Process not found")


@app.post("/processes/{name}/start", status_code=202)
def start_process_api(name: str, background_tasks: BackgroundTasks) -> Process:
    try:
        process = process_manager.get_process(name=name)
        process_manager.start_process(process=process)
        background_tasks.add_task(process_manager.poll_process, process)
        result = process_manager.get_process(name)
        return result
    except Exception as e:
        return HTTPException(
            status_code=400, detail=f"Start process failed with error: {str(e)}"
        )


def stop_process_background(name: str):
    process = process_manager.get_process(name=name)
    if process.status == "running":
        process_manager.stop_process(process)


@app.post("/processes/{name}/stop", status_code=202)
def stop_process_api(name: str, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(stop_process_background, name)
        result = process_manager.get_process(name)
        return JSONResponse({"result": result})
    except Exception as e:
        return HTTPException(
            status_code=400, detail=f"Stop process failed with error: {str(e)}"
        )


# Define the route for the web UI
@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "processes": process_manager.processes}
    )


# Reload the config files
@app.post("/processes/reload", status_code=200)
def reload_processes() -> ProcessDefinitionList:
    return process_manager.load_process_defs()


# Accept an updated processes JSON
@app.post("/processes/update", status_code=200)
def update_processes(
    process_definitions: ProcessDefinitionList,
) -> ProcessDefinitionList:
    try:
        process_manager.dump_process_defs(process_definitions)
        process_manager.load_process_defs()
        process_manager.init_processeses()
        return process_manager.process_defs
    except Exception as e:
        return HTTPException(400, f"Failed to parse JSON: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, port=5005, host="0.0.0.0")
