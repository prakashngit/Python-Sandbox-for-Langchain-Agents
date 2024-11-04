import requests
from typing import TypedDict, Optional, Dict
import base64
import os

class DockerResponse(TypedDict):
    success: bool
    output: str
    error: Optional[str]
    files: Optional[Dict[str, bytes]]

def run_python_code(code: str) -> str:
    """
    Executes Python code by sending it to a Docker container running a Flask server.
    Also saves any generated files to the current directory.
    Returns the output or error message.
    """
    try:
        response = requests.post(
            'http://localhost:5000/execute',
            json={'code': code},
            timeout=30
        )
        result = response.json()
        
        # Return error message if execution failed
        if not result["success"]:
            return f"Error executing code: {result['error']}"  # Make error visible to LLM
        
        # Convert base64 files back to bytes and save them
        if result.get('files'):
            files = {}
            for filename, b64content in result['files'].items():
                content = base64.b64decode(b64content)
                # Extract just the filename without path
                local_filename = os.path.basename(filename)
                # Save the file to current directory
                with open(local_filename, 'wb') as f:
                    f.write(content)
                files[local_filename] = content
            result['files'] = files
            
        # Return only the code's output
        return result['output'] if result['output'] else ""

    except Exception as e:
        print(f"Error in run_python_code: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test 1: Simple addition
    print("\nTest 1: Simple addition")
    code1 = "print(1 + 1)"
    result1 = run_python_code(code1)
    print(result1)

    # Test 2: QR Code generation
    print("\nTest 2: QR Code generation")
    code2 = """
import qrcode

# Create QR code instance
qr = qrcode.QRCode(version=1, box_size=10, border=5)

# Add data
url = 'https://www.linkedin.com/in/prakash-narayana-moorthy-522021b3/'
qr.add_data(url)
qr.make(fit=True)

# Create an image from the QR Code and save it
img = qr.make_image(fill_color="black", back_color="white")
img.save('/workspace/prakash_linkedin_qr.png')

print(f"QR Code generated successfully for: {url}")
"""
    result2 = run_python_code(code2)
    print(result2)