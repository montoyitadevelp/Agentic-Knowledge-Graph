# Import necessary libraries
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from agent import AgentCaller, hello_agent
from typing import Dict, Any, Optional
from google.adk.agents import Agent

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.CRITICAL)


# Initialize a session service and a session
async def main(agent: Agent, initial_state: Optional[Dict[str, Any]] = {}) -> AgentCaller:
    """Create and return an AgentCaller instance for the given agent."""
    app_name = agent.name + "_app"
    user_id = agent.name + "_user"
    session_id = agent.name + "_session_01"
    
    # Initialize a session service and a session
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state
    )
    
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )
    
    return AgentCaller(agent, runner, user_id, session_id)


if __name__ == "__main__":
    hello_agent_caller = asyncio.run(main(agent=hello_agent))
    
    # Example interaction with the agent
    user_input = "Hi there! My name is Alice."
    asyncio.run(hello_agent_caller.call(user_input))