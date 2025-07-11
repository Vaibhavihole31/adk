import os
import datetime
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import openai


def get_current_time() -> str:
    current_time = datetime.datetime.now()
    return f"The current time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}"


def perform_task(task: str) -> str:
    return f"I have performed the task: {task}"


def setup_openai_key():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # If key isn't in environment variables, prompt user
    if not openai_api_key:
        openai_api_key = input("Please enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
    # Validate the key format (basic check)
    if not openai_api_key.startswith(("sk-")):
        print("Warning: The API key format doesn't look like a standard OpenAI key.")
        proceed = input("Do you want to proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting program. Please set a valid OpenAI API key.")
            exit(1)
    
    return openai_api_key


def main():
    # Set up OpenAI API key
    openai_api_key = setup_openai_key()
    
    # Set OpenAI API key in environment variable
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Define the greeter agent
    greeter = LlmAgent(
        name="greeter",
        model="gpt-3.5-turbo", 
        description="I specialize in greeting users and making them feel welcome."
    )

    # Define the task executor agent
    task_executor = LlmAgent(
        name="task_executor", 
        model="gpt-3.5-turbo",
        description="I specialize in executing tasks and getting things done.",
        tools=[
            FunctionTool(perform_task),
            FunctionTool(get_current_time)
        ]
    )
    
    # Create coordinator agent and assign children via sub_agents
    coordinator = LlmAgent(
        name="Coordinator",
        model="gpt-3.5-turbo", 
        description="I coordinate greetings and tasks.",
        sub_agents=[ 
            greeter,
            task_executor
        ]
    )
    
    print("\n=== Coordinator Agent System with Google ADK ===")
    print("Type 'exit' or 'quit' to end the program")
    print("\nExamples:")
    print("- 'Hello, how are you?'")
    print("- 'Can you tell me the current time?'")
    print("- 'Please organize my files'")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        try:
            response = coordinator.generate(user_input)
            
            # Print the agent's response
            print(f"Agent: {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()