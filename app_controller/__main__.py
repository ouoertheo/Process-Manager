from app_controller.app_controller import app
import uvicorn

import argparse

parser = argparse.ArgumentParser(
                    prog='app_controller',
                    description='A basic web interface to start, stop, and view stdout of local processes')
parser.add_argument('-o','--host', action='store', dest='host', default='0.0.0.0')
parser.add_argument('-p','--port', action='store', dest='port', type=int, default=5005)

args = parser.parse_args()

if help not in args:
    uvicorn.run(app, host=args.host, port=args.port)