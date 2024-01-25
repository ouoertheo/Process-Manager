# App Controller
A very basic web front-end to start and stop apps. Handy to start common apps easily from one spot.
Allows to start, stop, and view a logs.

# Install
1. Install Python
2. Install `poetry` package: `pip install poetry`
3. Run `poetry install` in the project root.

# Configure
1. Create and open `processes.json` file under the `process_manager` directory
2. Populate the json file like follows (example json provided at project root)

```
{
  definitions": 
    {
        "friendly_app_name": {
          "path":"working_directory",
          "command": ["command","arg1","arg2"]
        },
        "friendly_app_name2": {"path":"working_directory",
        "command": ["command"]}
    }
}
```
Command must be in a list format. Arguments are optional. No spaces are allowed, so separate them as separate entries. 

# Running
`poetry run python -m process_manager`.
Runs on 0.0.0.0:5005 by default
```
usage: app_controller [-h] [-o HOST] [-p PORT]

A basic web interface to start, stop, and view stdout of local processes

options:
  -h, --help            show this help message and exit
  -o HOST, --host HOST
  -p PORT, --port PORT
```