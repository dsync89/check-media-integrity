from flask import Flask, render_template, request, redirect, url_for, Response, stream_with_context, send_file
import os
import subprocess

app = Flask(__name__)

# Define the paths
BASE_PATH = '/media/videos'
CSV_PATH = '/app/logs'

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

def list_csv_files(path):
    return [entry.name for entry in os.scandir(path) if entry.is_file() and entry.name.endswith('.csv')]

@app.route('/', methods=['GET', 'POST'])
def index():
    folders = list_folders(BASE_PATH)
    csv_files = list_csv_files(CSV_PATH)
    if request.method == 'POST':
        selected_folders = request.form.getlist('folders')
        return redirect(url_for('stream_output', folders=selected_folders))

    return render_template('index.html', folders=folders, csv_files=csv_files, command_output="")

@app.route('/stream')
def stream_output():
    selected_folders = request.args.getlist('folders')
    command = ['/app/check_mi.py', '-m', '-r'] + selected_folders

    def generate():
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            for line in process.stdout:
                yield f"data: {line}\n\n"
            for line in process.stderr:
                yield f"data: {line}\n\n"
        process.wait()
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/csv')
def csv_viewer():
    file_name = request.args.get('file')
    file_path = os.path.join(CSV_PATH, file_name)
    return send_file(file_path)

if __name__ == '__main__':
    app.run(debug=True)
