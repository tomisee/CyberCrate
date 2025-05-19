import os
import sys
import json
import sqlite3
import subprocess
from pathlib import Path
import platform
import logging
import tempfile
import shutil
import re

class TheHarvesterWrapper:
    def __init__(self):
        self.tool_dir = Path(__file__).parent
        self.config_file = self.tool_dir / 'config' / 'settings.json'
        self.db_file = self.tool_dir / 'config' / 'database.sqlite'
        self.venv_path = self.tool_dir / 'venv'
        self.setup_logging()

    def setup_logging(self):
        """Set up logging for the wrapper"""
        log_file = self.tool_dir / 'theharvester.log'
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_environment(self):
        """Set up the complete environment for theHarvester"""
        try:
            print(f"Setting up environment in {self.venv_path}")
            # Create virtual environment
            if not self.venv_path.exists():
                print("Creating virtual environment...")
                # Use the system Python to create venv
                subprocess.run(['python3', '-m', 'venv', str(self.venv_path)], check=True)

            # Install requirements using the system pip
            print("Installing theHarvester...")
            # First uninstall any existing version
            subprocess.run(['pip3', 'uninstall', '-y', 'theHarvester'], check=True)
            # Install from GitHub
            subprocess.run(['pip3', 'install', 'git+https://github.com/laramies/theHarvester.git'], check=True)

            # Initialize database if it doesn't exist
            self.initialize_database()

            print("Environment setup completed successfully")
            return True
        except Exception as e:
            print(f"Environment setup failed with error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

    def initialize_database(self):
        """Initialize the SQLite database with required tables"""
        if not self.db_file.exists():
            logging.info("Initializing database...")
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # Create necessary tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT,
                    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    results TEXT,
                    status TEXT,
                    scan_type TEXT,
                    sources TEXT
                )
            ''')
            
            conn.commit()
            conn.close()

    def strip_ansi_codes(self, text):
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def run_scan(self, target, sources=None, options=None):
        """Run a scan with theHarvester"""
        try:
            print(f"[DEBUG] Raw target: {repr(target)}")
            print(f"[DEBUG] Raw sources: {repr(sources)}")
            print(f"[DEBUG] Raw options: {repr(options)}")
            # Ensure environment is set up
            if not self.setup_environment():
                raise Exception("Environment setup failed")

            # Construct the command using system Python
            cmd = ['theHarvester']
            
            # Add required arguments
            cmd.extend(['-d', str(target)])
            
            # Add sources if specified
            if sources and sources != 'all':
                cmd.extend(['-b', str(sources)])
            
            # Add optional arguments
            if options:
                if options.get('limit'):
                    cmd.extend(['-l', str(options['limit'])])
                if options.get('verbose'):
                    cmd.append('-v')
                if options.get('output'):
                    cmd.extend(['-o', str(options['output'])])

            print(f"[DEBUG] Final command list: {cmd}")
            print(f"Running command: {' '.join(cmd)}")
            
            # Run the scan
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.tool_dir)  # Set working directory to tool directory
            )
            stdout, stderr = process.communicate()

            # Strip ANSI codes
            stdout = self.strip_ansi_codes(stdout)
            stderr = self.strip_ansi_codes(stderr)

            print(f"Scan completed with return code: {process.returncode}")
            print(f"Output: {stdout[:200]}...")  # Print first 200 chars of output
            if stderr:
                print(f"Error output: {stderr}")

            # Store results in database
            self.store_scan_results(target, stdout, stderr, process.returncode, sources)

            # Return both stdout and stderr in the response
            return {
                'success': process.returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'return_code': process.returncode,
                'command': ' '.join(cmd)  # Include the command that was run
            }
        except Exception as e:
            print(f"Scan failed with error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    def store_scan_results(self, target, stdout, stderr, return_code, sources):
        """Store scan results in the database"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            status = 'success' if return_code == 0 else 'failed'
            results = json.dumps({
                'stdout': stdout,
                'stderr': stderr,
                'return_code': return_code
            })
            
            cursor.execute('''
                INSERT INTO scan_history (target, results, status, sources)
                VALUES (?, ?, ?, ?)
            ''', (target, results, status, sources))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to store scan results: {str(e)}")

    def get_scan_history(self, limit=10):
        """Retrieve recent scan history"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT target, scan_date, status, sources, results
                FROM scan_history
                ORDER BY scan_date DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [{
                'target': row[0],
                'scan_date': row[1],
                'status': row[2],
                'sources': row[3],
                'results': json.loads(row[4])
            } for row in results]
        except Exception as e:
            logging.error(f"Failed to retrieve scan history: {str(e)}")
            return []

if __name__ == '__main__':
    # Example usage
    wrapper = TheHarvesterWrapper()
    result = wrapper.run_scan('example.com', sources='google,bing', options={'limit': 100})
    print(json.dumps(result, indent=2)) 