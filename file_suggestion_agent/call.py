import asyncio
from main_call import make_agent_caller
from file_suggestion.agent import file_suggestion_agent

async def main():
    file_suggestion_caller = await make_agent_caller(file_suggestion_agent, {
        "approved_user_goal": {
            "kind_of_graph": "supply chain analysis",
            "description": "A multi-level bill of materials for manufactured products, useful for root cause analysis.."
        }   
    })
    
    await file_suggestion_caller.call("List available files.")
    
if __name__ == "__main__":
    session_end = asyncio.run(main())
