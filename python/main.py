
from dotenv import load_dotenv
load_dotenv()

from langchain import hub
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from tools.docker_python_sandbox.client import run_python_code

    
def main():
    instructions = """You are an agent designed to write and execute python code to answer questions.
You have access to a python code interpreter tool, which you can use to execute python code. 
You might know the answer without running the code, but you need to run the code
to verify. If you get an error, debug your code and try again. Only use the output of the code to answer
the question. If it seems that you cannot write the code to answer the question, say "I don't know the answer" and explain why."""
    
    react_prompt_template = hub.pull("langchain-ai/react-agent-template")
    react_prompt = react_prompt_template.partial(instructions=instructions)

    
    tools_for_agent = [
        Tool(
            name = "python_code_interpreter",
            func=run_python_code,
            description="""A Python shell. Use this to execute python commands. 
            Input should be a valid python command. 
            If you want to see the output of a value, you should print it out with `print(...)`.
            Always save files to '/workspace/' directory."""
        )
    ]

    llm_openai = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    agent = create_react_agent(llm_openai, tools_for_agent, prompt=react_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools_for_agent, verbose=True, handle_parsing_errors=True)

    # this should succeed
    agent_executor.invoke({"input": """ Create and save in the current working directory 3 qrcodoes that point to https://www.linkedin.com/in/prakash-narayana-moorthy-522021b3/?, you have qrcode library installed."""})

    
    # this should fail initially because pandas is not installed, but then the llm might try a workaround
    agent_executor.invoke({"input": """Create a simple DataFrame using pandas with columns 'Name' and 'Age', 
    add a few rows of data, and print it. Save this as test.py in the current working directory."""})

    # this should fail because matplotlib is not installed
    agent_executor.invoke({
    "input": """Create a simple line plot using matplotlib showing points (1,2), (2,4), (3,6). 
    Save it as plot.png in the current working directory."""
    })
    
    # this should ideally fail because the user does not have permission to create a file in /etc
    # but sometimes the llm gets too smart and realizes that it doesnot have the permissions without even
    # attempting to run the code, and instead creates the file in the current working directory
    agent_executor.invoke({
    "input": """Create a text file at /etc/test.txt containing 'hello world'."""
    })


if __name__ == "__main__":
    main()

