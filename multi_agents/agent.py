
from google.adk.agents import Agent
from multi_agents.tools import say_hello_stateful, say_goodbye_stateful
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

load_dotenv()

llm = LiteLlm(model="gemini/gemini-2.5-flash")

# define a stateful greeting agent. the only difference is that this agent will use the stateful say_hello_stateful tool
greeting_agent_stateful = Agent(
    model=llm,
    name="greeting_agent_stateful_v1",
    instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. Do nothing else.",
    description="Handles simple greetings and hellos using the 'say_hello_stateful' tool.",
    tools=[say_hello_stateful],
)

# define a stateful farewell agent. the only difference is that this agent will use the stateful say_goodbye_stateful tool
farewell_agent_stateful = Agent(
    model=llm,
    name="farewell_agent_stateful_v1",
    instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye_stateful' tool. Do not perform any other actions.",
    description="Handles simple farewells and goodbyes using the 'say_goodbye_stateful' tool.",
    tools=[say_goodbye_stateful],
)

# define the root agent that uses the stateful sub-agents
root_agent_stateful = Agent(
    name="friendly_team_stateful", # New version name
    model=llm,
    description="The main coordinator agent. Delegates greetings/farewells to specialists.",
    instruction="""You are the main Agent coordinating a team. Your primary responsibility is to be friendly.

                You have specialized sub-agents:
                1. 'greeting_agent_stateful': Handles simple greetings like 'Hi', 'Hello'. Delegate to it for these.
                2. 'farewell_agent_stateful': Handles simple farewells like 'Bye', 'See you'. Delegate to it for these.

                Analyze the user's query. If it's a greeting, delegate to 'greeting_agent_stateful'. If it's a farewell, delegate to 'farewell_agent_stateful'.

                For anything else, respond appropriately or state you cannot handle it.
                """,
        tools=[], # Still no tools for root
        sub_agents=[greeting_agent_stateful, farewell_agent_stateful], # Include sub-agents
    )

# Expose the agent as root_agent for the ADK CLI
root_agent = root_agent_stateful
