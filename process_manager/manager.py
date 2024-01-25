import json
import subprocess, psutil
from loguru import logger
from process_manager.process_model import (
    ProcessDefinitionList,
    Process,
)

logger.add("app.log", filter=__name__)


class ProcesNotFoundException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ProcessManager:
    def __init__(self) -> None:
        self.MAX_LOG_LENGTH = 1000
        self.pid_popen_map: dict[int, subprocess.Popen] = {}
        self.processes: list[Process] = []
        self.process_defs = self.load_process_defs()
        self.init_processeses()

    def init_processeses(self):
        for name, definition in self.process_defs.definitions.items():
            # Keep the process information if it exists so we have a reference to any Popen objects.
            process = self.get_process(name)
            if process:
                # Check if process was removed from definitions
                if process.name not in self.process_defs.definitions:
                    self.remove_process(process)
                    return
                process.definition = definition
                logger.info(f"Updated existing managed process {process.name}")
            else:
                process = Process(name=name, process=None, definition=definition)
                self.processes.append(process)
                logger.info(f"Managing new process {process.name}")

    def remove_process(self, process: Process):
        """
        Stops the process if running then removes it.
        """
        if process.status == "running":
            self.stop_process(process)
        del self.processes[process]
        logger.warning(f"Removed process {process.name}.")

    def list_processes(self):
        return self.processes

    def get_process(self, name):
        for process in self.processes:
            if process.name == name:
                return process
        return None

    # Start a process
    def start_process(self, process: Process):
        if process.status == "running":
            raise Exception(f"{process.name} is already running")
        proc = subprocess.Popen(
            process.definition.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=process.definition.path,
        )
        self.pid_popen_map[proc.pid] = proc
        process.pid = proc.pid
        process.status = "running"
        logger.info(f"Started process {process.name} with pid {process.pid}")
        status = self.check_process_status(process)
        if status == "stopped":
            logs = self.get_process_logs(process)
            raise Exception(
                f"Process {process.name} stopped immediately after running. Logs: {logs}"
            )

    # Stop a process
    def stop_process(self, process: Process):
        if not process.pid:
            raise Exception(f"Process not running.")
        main_proc = psutil.Process(process.pid)
        for child_proc in main_proc.children(recursive=True):
            child_proc.terminate()

        main_proc.terminate()

        logger.info(f"Stopped process {process.name} with pid {process.pid}")
        process.status = "stopped"

        del self.pid_popen_map[process.pid]
        process.pid = None

    def check_process_status(self, process: Process):
        process_popen = self.pid_popen_map[process.pid]
        if process_popen.poll() is not None:
            logger.warning(
                f"Detected process {process.name} with pid {process.pid} is not running, cleaning up process."
            )
            if process.pid in self.pid_popen_map:
                del self.pid_popen_map[process.pid]
            if process.pid:
                process.pid = None
            process.status = "stopped"
        return process.status

    def get_process_logs(self, process: Process):
        process_popen = self.pid_popen_map[process.pid]
        outputline = process_popen.stdout.readline().strip()
        process.logs.appendleft(outputline)
        process.new_log_count += len(outputline)
        return process.logs

    # Poll process and grab stdout for logging
    def poll_process(self, process: Process):
        while True:
            try:
                self.get_process_logs(process)
                status = self.check_process_status(process)
                if status == "stopped":
                    return
            except:
                continue

    def dump_process_defs(self, process_defs: ProcessDefinitionList):
        with open("processes.json", "w") as f:
            f.write(process_defs.model_dump_json(indent=2))
            logger.info(f"{len(process_defs.definitions)} process definitions saved.")

    def load_process_defs(self):
        with open("processes.json") as fh:
            self.process_defs = ProcessDefinitionList(**json.load(fh))
            logger.info(
                f"{len(self.process_defs.definitions)} process definitions loaded."
            )
        return self.process_defs
