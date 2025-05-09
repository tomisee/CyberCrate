import subprocess
import json
import os
import platform
from pathlib import Path
import logging
import re
import sqlite3
import tempfile
import shutil

class NmapWrapper:
    def __init__(self):
        self.tool_dir = Path(__file__).parent
        self.db_file = self.tool_dir / 'config' / 'scan_history.sqlite'
        self.setup_logging()
        self.initialize_database()

    def setup_logging(self):
        log_file = self.tool_dir / 'nmap.log'
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def initialize_database(self):
        if not self.db_file.exists():
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT,
                    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scan_type TEXT,
                    options TEXT,
                    results TEXT,
                    status TEXT
                )
            ''')
            conn.commit()
            conn.close()

    def strip_ansi_codes(self, text):
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def is_nmap_installed(self):
        return shutil.which('nmap') is not None

    def run_scan(self, target, options=None):
        """Run an nmap scan on the target with optional arguments."""
        if not self.is_nmap_installed():
            return {
                'success': False,
                'error': 'Nmap is not installed on this system. Please install nmap and try again.'
            }
        try:
            # Build the nmap command
            cmd = ['nmap']
            if options:
                cmd.extend(options)
            cmd.append(target)
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
            self.store_scan_results(target, options, stdout, stderr, process.returncode)
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

    def store_scan_results(self, target, options, stdout, stderr, return_code):
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
                INSERT INTO scan_history (target, scan_type, options, results, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (target, 'nmap', json.dumps(options), results, status))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to store scan results: {str(e)}")

    def get_scan_history(self, limit=10):
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            cursor.execute('''
                SELECT target, scan_date, scan_type, options, results, status
                FROM scan_history
                ORDER BY scan_date DESC
                LIMIT ?
            ''', (limit,))
            results = cursor.fetchall()
            conn.close()
            return [{
                'target': row[0],
                'scan_date': row[1],
                'scan_type': row[2],
                'options': json.loads(row[3]),
                'results': json.loads(row[4]),
                'status': row[5]
            } for row in results]
        except Exception as e:
            logging.error(f"Failed to retrieve scan history: {str(e)}")
            return []

if __name__ == '__main__':
    wrapper = NmapWrapper()
    result = wrapper.run_scan('scanme.nmap.org', options=['-sV'])
    print(json.dumps(result, indent=2)) 