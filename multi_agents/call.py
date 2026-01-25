import asyncio
from main_call import make_agent_caller
from multi_agents.agent import root_agent_stateful


async def main():
    root_stateful_caller = await make_agent_caller(root_agent_stateful)

    async def run_stateful_conversation():
        await root_stateful_caller.call("Hello, I'm ABK!")

        await root_stateful_caller.call("Thanks, bye!")

    # Execute the conversation using await
    await run_stateful_conversation()
    
    session = await root_stateful_caller.get_session()
    print("\nFinal session state:", session.state)
    
if __name__ == "__main__":
    asyncio.run(main())