# server.py
from flask import Flask, request, jsonify
import base64
import os
import subprocess
import tempfile
from typing import Dict, Any
import traceback

app = Flask(__name__)

def execute_in_fresh_python(code: str) -> dict:
    """Execute code in a fresh Python process"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
        # Write the code to a temp file
        f.write(code)
        f.flush()
        
        try:
            # Run in fresh Python interpreter
            result = subprocess.run(
                ['python', f.name],
                capture_output=True,
                text=True,
                timeout=30  # Timeout after 30 seconds
            )
            
            # Collect any files created in /workspace
            files = {}
            if os.path.exists('/workspace'):
                for filename in os.listdir('/workspace'):
                    filepath = os.path.join('/workspace', filename)
                    if os.path.isfile(filepath):
                        with open(filepath, 'rb') as f:
                            files[filename] = base64.b64encode(f.read()).decode('utf-8')
                        # Clean up the file
                        os.remove(filepath)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "files": files
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Execution timed out",
                "files": None
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": traceback.format_exc(),
                "files": None
            }

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({"success": False, "error": "No code provided"})
        
        # Execute in fresh Python process
        result = execute_in_fresh_python(code)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "output": "",
            "files": None,
            "error": traceback.format_exc()
        })

if __name__ == '__main__':
    # Ensure workspace directory exists
    os.makedirs('/workspace', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)