from flask import Flask
from flask import send_from_directory
import argparse

parser = argparse.ArgumentParser(description='')
parser.add_argument('-d', dest='directory', default='', help='service directory')
parser.add_argument('-p', dest='port', type=int, default=80, help='service port')
args = parser.parse_args()

if args.directory == '' or args.port is None:
	parser.print_help()
	exit(1)

#########################################################
static_path = args.directory
app = Flask(__name__, static_folder=static_path)	


@app.route('/')
def hello_world():
	return 'This server for Sample'

@app.route('/<path:filename>', methods=['GET'])
def download_service(filename):
	return send_from_directory(static_path, filename, as_attachment=True)

app.run(port=args.port)