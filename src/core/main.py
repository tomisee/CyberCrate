#!/usr/bin/env python3
import os
import sys
import json
import zipfile
import hashlib
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import yaml

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Creates a flask app
app = Flask(__name__, 
           template_folder=str(project_root / 'templates'),
           static_folder=str(project_root / 'static'))

#Key element, this creates a module box object that contains the manifest and content of a module
#The manifest is the metadata of the module, and the content is the files of the module
class ModuleBox:
    def __init__(self, crate_path):
        self.crate_path = crate_path
        self.manifest = None
        self.content_path = None
        self.load_manifest()

    #This function loads the manifest from the crate
    def load_manifest(self):
        print(f"Loading manifest from {self.crate_path}")
        with zipfile.ZipFile(self.crate_path, 'r') as crate:
            manifest_data = crate.read('manifest.json')
            self.manifest = json.loads(manifest_data)
            print(f"Loaded manifest: {json.dumps(self.manifest, indent=2)}")
            
            # Extract content to temporary directory
            temp_dir = project_root / 'data' / 'temp_content'
            temp_dir.mkdir(exist_ok=True)
            crate.extractall(temp_dir)
            self.content_path = temp_dir

    def verify_integrity(self):
        with zipfile.ZipFile(self.crate_path, 'r') as crate:
            for file_info in crate.infolist():
                if file_info.filename in self.manifest['hashes']:
                    data = crate.read(file_info.filename)
                    file_hash = hashlib.sha256(data).hexdigest()
                    if file_hash != self.manifest['hashes'][file_info.filename]:
                        return False
        return True

def load_progress():
    progress_file = project_root / 'data' / 'progress' / 'progress.yaml'
    try:
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                data = yaml.safe_load(f)
                print(f"Loaded progress data: {json.dumps(data, indent=2)}")
                # Ensure the data structure is correct
                if not isinstance(data, dict):
                    data = {'modules': {}}
                if 'modules' not in data:
                    data['modules'] = {}
                return data
    except Exception as e:
        print(f"Error loading progress: {str(e)}")
    return {'modules': {}}

def save_progress(progress):
    try:
        # Ensure the data structure is correct
        if not isinstance(progress, dict):
            progress = {'modules': {}}
        if 'modules' not in progress:
            progress['modules'] = {}
            
        print(f"Saving progress data: {json.dumps(progress, indent=2)}")
        progress_file = project_root / 'data' / 'progress' / 'progress.yaml'
        with open(progress_file, 'w') as f:
            yaml.dump(progress, f, default_flow_style=False)
    except Exception as e:
        print(f"Error saving progress: {str(e)}")
        raise

#This route is used to view the index page
@app.route('/')
def index():
    print("Index route accessed")
    crates_dir = project_root / 'modules' / 'crates'
    crates = []
    for crate_file in crates_dir.glob('*.crate'):
        try:
            with zipfile.ZipFile(crate_file, 'r') as crate:
                manifest_data = crate.read('manifest.json')
                manifest = json.loads(manifest_data)
                display_name = manifest.get('name', crate_file.stem)
                num_tasks = len(manifest.get('tasks', []))
                crates.append({
                    'filename': crate_file.name,
                    'display_name': display_name,
                    'num_tasks': num_tasks
                })
        except Exception as e:
            print(f"Error reading manifest from {crate_file}: {e}")
    print(f"Found crates: {crates}")
    progress = load_progress()
    return render_template('index.html', crates=crates, progress=progress)

#This route is used to view a module
@app.route('/module/<module_name>')
def view_module(module_name):
    print(f"Viewing module: {module_name}")
    crate_path = project_root / 'modules' / 'crates' / f"{module_name}.crate"
    if not crate_path.exists():
        print(f"Crate not found: {crate_path}")
        return "Module not found", 404
    
    #This creates a module box object
    module = ModuleBox(crate_path)
    if not module.verify_integrity():
        print("Module integrity check failed")
        return "Module integrity check failed", 400
    
    # Load progress data
    progress = load_progress()
    print(f"Loaded progress: {json.dumps(progress, indent=2)}")
    
    # Get module progress
    module_progress = progress.get('modules', {}).get(module_name, {}).get('tasks', {})
    print(f"Module progress: {json.dumps(module_progress, indent=2)}")
    
    # Update task status in module data
    for task in module.manifest['tasks']:
        task_id = task['id']
        task['status'] = module_progress.get(task_id, 'pending')
        print(f"Task {task_id} status: {task['status']}")
    
    #This renders the module page
    print(f"Rendering module with data: {json.dumps(module.manifest, indent=2)}")
    return render_template('module.html', 
                         module=module.manifest,
                         content_path=module.content_path,
                         progress=progress)

#This route is used to handle the progress of the module
@app.route('/progress', methods=['GET', 'POST'])
def handle_progress():
    if request.method == 'POST':
        try:
            progress = request.json
            print(f"Received progress update: {json.dumps(progress, indent=2)}")
            
            # Validate the progress data structure
            if not isinstance(progress, dict):
                raise ValueError("Progress data must be a dictionary")
            if 'modules' not in progress:
                progress['modules'] = {}
            
            # Ensure all task statuses are valid
            for module_name, module_data in progress['modules'].items():
                if 'tasks' in module_data:
                    for task_id, status in module_data['tasks'].items():
                        if status not in ['completed', 'pending']:
                            module_data['tasks'][task_id] = 'pending'
            
            save_progress(progress)
            return jsonify({'status': 'success', 'progress': progress})
        except Exception as e:
            print(f"Error saving progress: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    progress = load_progress()
    print(f"Returning progress: {json.dumps(progress, indent=2)}")
    return jsonify(progress)

#This is the main function that runs the web server
def main():
    # Ensure we're running from the correct directory
    if not (project_root / 'templates').exists():
        print("Error: Must run from the CyberCrate project root")
        sys.exit(1)
    #This starts the web server
    app.run(host='127.0.0.1', port=8080, debug=True)

if __name__ == '__main__':
    main()
