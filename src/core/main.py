#!/usr/bin/env python3
import os
import sys
import json
import zipfile
import hashlib
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory, abort
import yaml
from tools.portable.h8mail.wrapper import H8mailWrapper
from tools.portable.nmap.wrapper import NmapWrapper

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Creates a flask app
app = Flask(__name__, 
           template_folder=str(project_root / 'templates'),
           static_folder=str(project_root / 'static'))

# Initialize h8mail wrapper
h8mail_wrapper = H8mailWrapper()
nmap_wrapper = NmapWrapper()

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
                url_name = display_name.replace(' ', '_')
                num_tasks = len(manifest.get('tasks', []))
                crates.append({
                    'filename': crate_file.name,
                    'display_name': display_name,
                    'url_name': url_name,
                    'num_tasks': num_tasks
                })
        except Exception as e:
            print(f"Error reading manifest from {crate_file}: {e}")
    print(f"Found crates: {crates}")
    progress = load_progress()
    return render_template('index.html', crates=crates, progress=progress)

#This route is used to view a module
@app.route('/module/<url_name>')
def view_module(url_name):
    print(f"Viewing module: {url_name}")
    crates_dir = project_root / 'modules' / 'crates'
    # Find the crate whose manifest name matches url_name (spaces replaced with underscores)
    for crate_file in crates_dir.glob('*.crate'):
        with zipfile.ZipFile(crate_file, 'r') as crate:
            manifest_data = crate.read('manifest.json')
            manifest = json.loads(manifest_data)
            display_name = manifest.get('name', crate_file.stem)
            if display_name.replace(' ', '_') == url_name:
                # Found the correct crate
                if not ModuleBox(crate_file).verify_integrity():
                    print("Module integrity check failed")
                    return "Module integrity check failed", 400
                module = ModuleBox(crate_file)
                progress = load_progress()
                module_progress = progress.get('modules', {}).get(display_name, {}).get('tasks', {})
                for task in module.manifest['tasks']:
                    task_id = task['id']
                    task['status'] = module_progress.get(task_id, 'pending')
                return render_template('module.html', 
                                      module=module.manifest,
                                      content_path=module.content_path,
                                      progress=progress)
    print(f"Crate not found for url_name: {url_name}")
    return "Module not found", 404

#This route is used to handle the progress of the module
@app.route('/progress', methods=['GET', 'POST'])
def handle_progress():
    if request.method == 'POST':
        try:
            incoming_progress = request.json
            print(f"Received progress update: {json.dumps(incoming_progress, indent=2)}")
            
            # Validate the progress data structure
            if not isinstance(incoming_progress, dict):
                raise ValueError("Progress data must be a dictionary")
            if 'modules' not in incoming_progress:
                incoming_progress['modules'] = {}
            
            # Load existing progress
            existing_progress = load_progress()
            if 'modules' not in existing_progress:
                existing_progress['modules'] = {}
            
            # Merge: update only the modules present in the incoming progress
            for module_name, module_data in incoming_progress['modules'].items():
                existing_progress['modules'][module_name] = module_data
            
            # Ensure all task statuses are valid
            for module_name, module_data in existing_progress['modules'].items():
                if 'tasks' in module_data:
                    for task_id, status in module_data['tasks'].items():
                        if status not in ['completed', 'pending']:
                            module_data['tasks'][task_id] = 'pending'
            
            save_progress(existing_progress)
            return jsonify({'status': 'success', 'progress': existing_progress})
        except Exception as e:
            print(f"Error saving progress: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    progress = load_progress()
    print(f"Returning progress: {json.dumps(progress, indent=2)}")
    return jsonify(progress)

CHEATSHEETS_DIR = project_root / 'cheatsheets'

@app.route('/cheatsheets')
def cheatsheets_list():
    cheatsheets = []
    if CHEATSHEETS_DIR.exists():
        for f in CHEATSHEETS_DIR.glob('*.md'):
            cheatsheets.append(f.stem)
    return render_template('cheatsheets.html', cheatsheets=cheatsheets)

@app.route('/cheatsheet/<name>')
def cheatsheet_view(name):
    cheatsheet_file = CHEATSHEETS_DIR / f'{name}.md'
    if not cheatsheet_file.exists():
        abort(404)
    with open(cheatsheet_file, 'r') as f:
        content = f.read()
    return render_template('cheatsheet_view.html', name=name, content=content)

@app.route('/tools')
def tools_list():
    """List all available tools"""
    return render_template('tools.html')

@app.route('/tool/h8mail')
def h8mail_interface():
    """H8mail tool interface"""
    return render_template('tool_h8mail.html')

@app.route('/tool/h8mail/scan', methods=['POST'])
def h8mail_scan():
    try:
        data = request.json
        target = data.get('target')
        options = data.get('options', {})

        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400

        # Run the scan
        result = h8mail_wrapper.run_scan(target, options=options)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/tool/h8mail/history')
def h8mail_history():
    try:
        history = h8mail_wrapper.get_scan_history()
        return jsonify(history)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/tool/h8mail/results/<target>')
def h8mail_results(target):
    try:
        # Get the most recent scan results for the target
        history = h8mail_wrapper.get_scan_history()
        target_results = next(
            (scan for scan in history if scan['target'] == target),
            None
        )
        
        if not target_results:
            return jsonify({
                'success': False,
                'error': 'No results found for this target'
            }), 404
            
        return jsonify(target_results)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/tool/nmap')
def nmap_interface():
    """Nmap tool interface"""
    return render_template('tool_nmap.html')

@app.route('/tool/nmap/scan', methods=['POST'])
def nmap_scan():
    try:
        data = request.json
        target = data.get('target')
        options = data.get('options', [])
        if not target:
            return jsonify({'success': False, 'error': 'Target is required'}), 400
        result = nmap_wrapper.run_scan(target, options=options)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/tool/nmap/history')
def nmap_history():
    try:
        history = nmap_wrapper.get_scan_history()
        return jsonify(history)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

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
