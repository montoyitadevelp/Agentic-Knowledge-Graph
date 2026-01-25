import asyncio
from main_call import make_agent_caller
from indent_agent.agent import user_intent_agent
from indent_agent.tools import PERCEIVED_USER_GOAL

# We need an async function to await for each conversation
async def main():
    user_intent_caller = await make_agent_caller(user_intent_agent)
    
    session_start = await user_intent_caller.get_session()
    
    print(f"Session Start: {session_start.state}") # expect this to be empty
    # start things off by describing your goal
    await user_intent_caller.call("""I'd like a bill of materials graph (BOM graph) which includes all levels from suppliers to finished product, 
    which can support root-cause analysis.""") 

    if PERCEIVED_USER_GOAL not in session_start.state:
        # the LLM may have asked a clarifying question. offer some more details
        await user_intent_caller.call("""I'm concerned about possible manufacturing or supplier issues.""")        

    # Optimistically presume approval.
    await user_intent_caller.call("Approve that goal.", True)
    
    return user_intent_caller


if __name__ == "__main__":
    session_end = asyncio.run(main())
    asyncio.run(session_end.get_session())
    

