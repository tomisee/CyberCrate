#!/usr/bin/env python3
import os
import json
import yaml
import zipfile
import hashlib
from pathlib import Path

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_task_file(task_file):
    """Process a task file (YAML or JSON) and return its contents as a list of tasks."""
    task_file = Path(task_file)
    with open(task_file, 'r') as f:
        if task_file.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        elif task_file.suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported task file format: {task_file}")
    # If the data is a dict with a 'tasks' key, extract the list
    if isinstance(data, dict) and 'tasks' in data:
        return data['tasks']
    # If the data is already a list, return as is
    if isinstance(data, list):
        return data
    # Otherwise, wrap in a list
    return [data]

def build_crate(module_dir, output_dir):
    """Build a .crate file from a module directory."""
    module_dir = Path(module_dir)
    output_dir = Path(output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find task files
    task_files = list(module_dir.glob('**/*.yaml')) + list(module_dir.glob('**/*.json'))
    if not task_files:
        raise ValueError(f"No task files found in {module_dir}")
    
    # Process task files
    tasks = []
    module_name = module_dir.name
    for task_file in task_files:
        # Load the raw data to extract the name if present
        with open(task_file, 'r') as f:
            if task_file.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif task_file.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported task file format: {task_file}")
        if isinstance(data, dict) and 'name' in data:
            module_name = data['name']
        # Now extract the tasks as before
        tasks.extend(process_task_file(task_file))
    
    # Create manifest
    manifest = {
        "version": "1.0",
        "name": module_name,
        "hashes": {},
        "tasks": tasks
    }
    
    # Calculate hashes for all files
    for file_path in module_dir.glob('**/*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(module_dir)
            manifest['hashes'][str(rel_path)] = calculate_file_hash(file_path)
    
    # Create crate file
    crate_name = module_dir.name + '.crate'
    crate_path = output_dir / crate_name
    
    with zipfile.ZipFile(crate_path, 'w', zipfile.ZIP_DEFLATED) as crate:
        # Add manifest
        crate.writestr('manifest.json', json.dumps(manifest, indent=2))
        
        # Add all files
        for file_path in module_dir.glob('**/*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(module_dir)
                crate.write(file_path, rel_path)
    
    print(f"Created crate: {crate_path}")
    return crate_path

def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # Set up paths
    modules_dev_dir = project_root / 'modules' / 'dev'
    modules_crates_dir = project_root / 'modules' / 'crates'
    
    # Create output directory if it doesn't exist
    modules_crates_dir.mkdir(parents=True, exist_ok=True)
    
    # Build crates for all module directories
    for module_dir in modules_dev_dir.iterdir():
        if module_dir.is_dir():
            try:
                build_crate(module_dir, modules_crates_dir)
            except Exception as e:
                print(f"Error building crate for {module_dir}: {str(e)}")

if __name__ == '__main__':
    main()
