from flask import Flask, render_template, request, redirect, url_for, Response, stream_with_context
import os
import subprocess
import time

app = Flask(__name__)

# Define the path to list directories from
BASE_PATH = '/media/videos'

def list_folders(path):
    folders = []
    for entry in os.scandir(path):
        if entry.is_dir():
            subfolders = list_folders(entry.path)
            folders.append({
                'name': entry.name,
                'path': entry.path,
                'subfolders': subfolders
            })
    return folders

@app.route('/', methods=['GET', 'POST'])
def index():
    folders = list_folders(BASE_PATH)
    if request.method == 'POST':
        selected_folders = request.form.getlist('folders')
        return redirect(url_for('stream_output', folders=selected_folders))
    
    return render_template('index.html', folders=folders, command_output="")

@app.route('/stream')
def stream_output():
    selected_folders = request.args.getlist('folders')
    command = ['/app/check_mi.py', '-m', '-r'] + selected_folders

    def generate():
        # Execute the command
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            for line in process.stdout:
                yield f"data: {line}\n\n"
            # Send error messages if any
            for line in process.stderr:
                yield f"data: {line}\n\n"
                
        # Wait for the command to finish
        process.wait()
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
