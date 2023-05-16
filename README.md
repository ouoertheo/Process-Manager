# App Controller
A very basic web front-end to start and stop apps. It's a bit raw, but sharing in case other's are interested.
Allows to start, stop, and view a stream of stdout in a text box. Handy to start common apps easily from one spot. 

# Configure
1. Create and open `processes.json` file under the `app_controller` directory
2. Populate the json file like follows

```
{
    "friendly_app_name": ["command","arg1","arg2"],
    "friendly_app_name2": ["command"]
}
```
Arguments are optional. A good rule of thumb is that if there's a space in the full command, it's a separate string in the args list.
I tend to point commands to a script, like a Powershell script that performs any extra commands needed to prep and run whatever app I'm running. For example, this is my setup now:
```
{
  "tavern-ai": ["powershell","Start-TavernAI"],
  "tavern-extras": ["powershell","Start-TavernAIExtras"],
  "stable-diffusion": ["powershell","Start-StableDiffusion"],
  "silero-tts": ["powershell","Start-Silero"]
}
```

# Running
`python -m app_controller`.
Runs on 0.0.0.0:5005 by default
```
usage: app_controller [-h] [-o HOST] [-p PORT]

A basic web interface to start, stop, and view stdout of local processes

options:
  -h, --help            show this help message and exit
  -o HOST, --host HOST
  -p PORT, --port PORT
```