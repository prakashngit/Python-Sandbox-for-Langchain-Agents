""" This module is a simplified version of the terrarium example client 
found at https://github.com/cohere-ai/cohere-terrarium/blob/main/example-clients/python/terrarium_client.py
that is sufficient to interact with a locally running terrarium server.
The challenge with using terrarium is that installing new pip packages seems to be difficult.
Terrarium is built on  of Pyodide & pyodide includes micropip, so one would imagine this should work,
but I couldn't get it to work. Also, even if I could, the second challenge is that if the goaal is to use terrarium
as a local PythonREPL tool for executing llm generated code, then the llm should be prompted very carefully to 
use micropip to install any additional packages (assuming we use terrarium as is) before importing and using them. Similar prompting challenges would  exist when the llm python code would need to save a file. So overall the my observation is that using terrarium  as a local PythonREPL tool for executing llm generated code needs significant additional work. In this project, we'll just use  docker based sanbodixng for a standard python interpreter. 
"""

import requests
import json
from typing import TypedDict, Optional, List, Dict, Any

class B64_FileData(TypedDict):
    b64_data: str
    filename: str

class TerrariumError(TypedDict):
    type: str
    message: str

class TerrariumResponse(TypedDict):
    success: bool
    output_files: List[Dict[str, str]]
    final_expression: Optional[Any]
    std_out: str
    std_err: str
    code_runtime: int
    error: Optional[TerrariumError]

def run_terrarium(server_url: str, code: str, file_data: Optional[List[B64_FileData]] = None) -> TerrariumResponse:
    """
    Executes Python code in the terrarium environment.
    
    Args:
        server_url: The URL of the terrarium server
        code: The Python code to execute
        file_data: Optional list of files with base64-encoded content
        
    Returns:
        TerrariumResponse containing execution results and final expression
    """
    headers = {"Content-Type": "application/json"}
    
    data = {"code": code}
    if file_data is not None:
        data["files"] = file_data
    
    result = requests.post(server_url, headers=headers, json=data, stream=True)
    
    if result.status_code != 200:
        return {
            "success": False,
            "output_files": [],
            "final_expression": None,
            "std_out": "",
            "std_err": "",
            "code_runtime": 0,
            "error": {
                "type": "HTTPError",
                "message": f"Error: {result.status_code} - {result.text}"
            }
        }

    res_string = ""
    try:
        for c in result.iter_content(decode_unicode=True):
            if c == "\n":
                break
            res_string += c
        return json.loads(res_string)
    except json.decoder.JSONDecodeError as e:
        raise RuntimeError(f"Error when parsing: {res_string}", e)

if __name__ == "__main__":
    # Simple test
    code = "1 + 1"  
    result = run_terrarium("http://localhost:8080", code)
    print(json.dumps(result, indent=2))

    