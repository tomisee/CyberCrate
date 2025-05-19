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
            # Create virtual environment
            if not self.venv_path.exists():
                logging.info("Creating virtual environment...")
                subprocess.run([sys.executable, '-m', 'venv', str(self.venv_path)], check=True)

            # Install requirements
            pip_path = self.venv_path / 'bin' / 'pip' if os.name != 'nt' else self.venv_path / 'Scripts' / 'pip'
            
            logging.info("Installing theHarvester...")
            subprocess.run([str(pip_path), 'install', 'theHarvester'], check=True)

            # Initialize database if it doesn't exist
            self.initialize_database()

            logging.info("Environment setup completed successfully")
            return True
        except Exception as e:
            logging.error(f"Environment setup failed: {str(e)}")
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
            # Ensure environment is set up
            if not self.setup_environment():
                raise Exception("Environment setup failed")

            # Get the Python interpreter from the virtual environment
            python_path = self.venv_path / 'bin' / 'python'
            if os.name == 'nt':
                python_path = self.venv_path / 'Scripts' / 'python'

            # Construct the command
            cmd = [str(python_path), '-m', 'theHarvester', '-d', target]
            
            if sources:
                cmd.extend(['-b', sources])
            
            if options:
                if options.get('limit'):
                    cmd.extend(['-l', str(options['limit'])])
                if options.get('output'):
                    cmd.extend(['-o', options['output']])
                if options.get('verbose'):
                    cmd.append('-v')

            # Run the scan
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            # Strip ANSI codes
            stdout = self.strip_ansi_codes(stdout)
            stderr = self.strip_ansi_codes(stderr)

            # Store results in database
            self.store_scan_results(target, stdout, stderr, process.returncode, sources)

            return {
                'success': process.returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'return_code': process.returncode
            }
        except Exception as e:
            logging.error(f"Scan failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
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