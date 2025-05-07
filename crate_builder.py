#!/usr/bin/env python3
import os
import json
import hashlib
import zipfile
import argparse
from pathlib import Path

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_manifest(content_dir):
    manifest = {
        'version': '1.0',
        'hashes': {},
        'tasks': []
    }
    
    # Walk through content directory
    for root, _, files in os.walk(content_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, content_dir)
            
            # Calculate hash for each file
            manifest['hashes'][rel_path] = calculate_file_hash(file_path)
            
            # If it's a task file, add it to tasks list
            if file.endswith('.yaml') or file.endswith('.json'):
                with open(file_path, 'r') as f:
                    try:
                        task_data = json.load(f)
                        if 'tasks' in task_data:
                            manifest['tasks'].extend(task_data['tasks'])
                            manifest['name'] = task_data.get('name', 'Unnamed Module')
                            manifest['version'] = task_data.get('version', '1.0')
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse {file} as JSON")
    
    return manifest

def create_crate(name, content_dir, output_dir='.'):
    # Create manifest
    manifest = create_manifest(content_dir)
    
    # Create crate file
    crate_path = os.path.join(output_dir, f"{name}.crate")
    with zipfile.ZipFile(crate_path, 'w', zipfile.ZIP_DEFLATED) as crate:
        # Add manifest
        crate.writestr('manifest.json', json.dumps(manifest, indent=2))
        
        # Add content
        for root, _, files in os.walk(content_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, content_dir)
                crate.write(file_path, rel_path)
    
    print(f"Created crate: {crate_path}")

def main():
    parser = argparse.ArgumentParser(description='Create a CyberCrate module')
    parser.add_argument('--name', required=True, help='Name of the module')
    parser.add_argument('--path', required=True, help='Path to content directory')
    parser.add_argument('--output', default='.', help='Output directory')
    
    args = parser.parse_args()
    create_crate(args.name, args.path, args.output)

if __name__ == '__main__':
    main()
