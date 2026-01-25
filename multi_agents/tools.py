from neo4j_for_adk import graphdb
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext

load_dotenv()


def say_hello_stateful(user_name:str, tool_context:ToolContext):
    """Says hello to the user, recording their name into state.
    
    Args:
        user_name (str): The name of the user.
    """
    tool_context.state["user_name"] = user_name
    print("\ntool_context.state['user_name']:", tool_context.state["user_name"])
    return graphdb.send_query(
        f"RETURN 'Hello to you, ' + $user_name + '.' AS reply",
    {
        "user_name": user_name
    })
    
def say_goodbye_stateful(tool_context: ToolContext) -> dict:
    """Says goodbye to the user, reading their name from state."""
    user_name = tool_context.state.get("user_name", "stranger")
    print("\ntool_context.state['user_name']:", user_name)
    return graphdb.send_query("RETURN 'Goodbye, ' + $user_name + ', nice to chat with you!' AS reply",
    {
        "user_name": user_name
    })