import asyncio
from main_call import make_agent_caller
from structured_data_agents.agent import schema_proposal_coordinator

async def main():
    structured_schema_proposal_caller = await make_agent_caller(schema_proposal_coordinator, {
    "feedback": "",
    "approved_user_goal": {
        "kind_of_graph": "supply chain analysis",
        "description": "A multi-level bill of materials for manufactured products, useful for root cause analysis.."
    },
    "approved_files": [
        'assemblies.csv', 
        'parts.csv', 
        'part_supplier_mapping.csv', 
        'products.csv', 
        'suppliers.csv'
    ]
    })
    
    # Run the Initial Conversation
    await structured_schema_proposal_caller.call("How can these files be imported?")

    session_end = await structured_schema_proposal_caller.get_session()
    print("Session state: ", session_end.state)

    # Agree with the file suggestions
    await structured_schema_proposal_caller.call("Yes, let's do it!", True)

    session_end = await structured_schema_proposal_caller.get_session()

    print("Approved construction plan: ", session_end.state['approved_user_goal'])
        
if __name__ == "__main__":
    asyncio.run(main())