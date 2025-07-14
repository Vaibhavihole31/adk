import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set (optional for testing)
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_api_key)
        USE_OPENAI = True
    except ImportError:
        USE_OPENAI = False
        print("Warning: OpenAI library not installed. Using simulated responses.")
else:
    USE_OPENAI = False
    openai_client = None
    print("Warning: OPENAI_API_KEY not set. Using simulated responses.")

# Initialize Flask app
app = Flask(__name__)


def get_current_time() -> str:
    """Return the current time as a formatted string."""
    current_time = datetime.now()
    return f"The current time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

def perform_task(task: str) -> str:
    """Simulate performing a task."""
    return f"Task completed: {task}. Status: Success at {datetime.now().strftime('%H:%M:%S')}"

# Agent class to simulate the behavior you wanted
class SimpleAgent:
    def __init__(self, name, description, tools=None, sub_agents=None):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.sub_agents = sub_agents or []
    
    def run_live(self, query):
        """Process a query and return a response."""
        if USE_OPENAI and openai_client:
            return self._get_openai_response(query)
        else:
            return self._get_simulated_response(query)
    
    def _get_openai_response(self, query):
        """Get response from OpenAI API."""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are {self.name}. {self.description}"},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI API Error: {str(e)}"
    
    def _get_simulated_response(self, query):
        """Generate simulated responses based on agent type."""
        query_lower = query.lower()
        
        if self.name == "greeter":
            if any(word in query_lower for word in ["hello", "hi", "hey", "greet"]):
                return f"Hello! Welcome! I'm {self.name} and I'm here to make you feel welcome. How can I assist you today?"
            else:
                return f"Greetings! I'm {self.name}. {self.description}"
                
        elif self.name == "task_executor":
            # Check if query involves time
            if any(word in query_lower for word in ["time", "clock", "when"]):
                return get_current_time()
            # Check if query involves task execution
            elif any(word in query_lower for word in ["task", "do", "execute", "perform", "run"]):
                task = query.replace("perform", "").replace("task", "").replace("execute", "").strip()
                if not task:
                    task = "general task"
                return perform_task(task)
            else:
                return f"I'm {self.name}. I can help you execute tasks and get the current time. What would you like me to do?"
                
        elif self.name == "coordinator":
            if "greet" in query_lower or "hello" in query_lower:
                greeter_response = self.sub_agents[0].run_live(query) if self.sub_agents else "Hello from coordinator!"
                return f"[Coordinator] Routing to greeter: {greeter_response}"
            elif any(word in query_lower for word in ["task", "time", "execute", "perform"]):
                executor_response = self.sub_agents[1].run_live(query) if len(self.sub_agents) > 1 else perform_task(query)
                return f"[Coordinator] Routing to task executor: {executor_response}"
            else:
                return f"I'm the coordinator. I can route your requests to specialized agents: greeter for welcomes, task_executor for tasks and time. What do you need?"
        
        return f"I'm {self.name}. {self.description}"

# Initialize agents
greeter = SimpleAgent(
    name="greeter",
    description="I specialize in greeting users and making them feel welcome."
)

task_executor = SimpleAgent(
    name="task_executor", 
    description="I specialize in executing tasks and getting things done.",
    tools=["perform_task", "get_current_time"]
)

coordinator = SimpleAgent(
    name="coordinator",
    description="I coordinate greetings and tasks.",
    sub_agents=[greeter, task_executor]
)

# Create a dictionary to easily access agents by name
agents = {
    "greeter": greeter,
    "task_executor": task_executor,
    "coordinator": coordinator
}

@app.route('/', methods=['GET'])
def home():
    """Home endpoint to confirm API is running."""
    return jsonify({
        "status": "active",
        "message": "Simple Agent API is running",
        "available_agents": list(agents.keys()),
        "openai_enabled": USE_OPENAI,
        "endpoints": {
            "GET /": "This endpoint - API status",
            "POST /ask": "Ask an agent a question"
        },
        "example_request": {
            "agent": "coordinator",
            "query": "Hello, can you help me?"
        }
    })

@app.route('/ask', methods=['POST'])
def ask():
    """
    Simple endpoint to ask any agent a question.
    Send a POST request with JSON body: 
    {
        "agent": "agent_name",
        "query": "your question here"
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    agent_name = data.get("agent", "coordinator")  
    query = data.get("query")
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    if agent_name not in agents:
        return jsonify({
            "error": f"Agent '{agent_name}' not found",
            "available_agents": list(agents.keys())
        }), 404
    
    try:
        # Get response from the selected agent
        response = agents[agent_name].run_live(query)
        
        return jsonify({
            "agent": agent_name,
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "openai_used": USE_OPENAI
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/agents', methods=['GET'])
def list_agents():
    """List all available agents and their descriptions."""
    agent_info = {}
    for name, agent in agents.items():
        
        agent_info[name] = {
            "description": agent.description,
            "tools": getattr(agent, 'tools', []),
            "has_sub_agents": len(getattr(agent, 'sub_agents', [])) > 0
        }
    
    return jsonify({
        "agents": agent_info,
        "total_agents": len(agents)
    })

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("APP_PORT", "8080"))
    
    print(f"Starting Simple Agent API on http://0.0.0.0:{port}")
    print(f"Available agents: {', '.join(agents.keys())}")
    print("OpenAI integration:", "Enabled" if USE_OPENAI else "Disabled (using simulated responses)")
    print("\nEndpoints:")
    print("  GET  / - API status and info")
    print("  GET  /agents - List all agents")
    print("  POST /ask - Ask an agent a question")
    print("\nExample Postman request:")
    print("  URL: http://localhost:8080/ask")
    print("  Method: POST")
    print("  Body (JSON): {\"agent\": \"coordinator\", \"query\": \"Hello!\"}")
    
    app.run(host="0.0.0.0", port=port, debug=True)