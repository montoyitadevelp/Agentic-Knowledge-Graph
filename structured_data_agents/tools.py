from dotenv import load_dotenv
from neo4j_for_adk import tool_success, tool_error, get_neo4j_import_dir
from google.adk.tools.tool_context import ToolContext
from pathlib import Path
from google.adk.tools import ToolContext
from file_suggestion_agent.tools import approve_suggested_files, sample_file
from indent_agent.tools import approve_perceived_user_goal
from google.adk.agents.callback_context import CallbackContext

load_dotenv()

SEARCH_RESULTS = "search_results"

# A simple grep-like tool for searching text files
def search_file(file_path: str, query: str) -> dict:
    """
    Searches any text file (markdown, csv, txt) for lines containing the given query string.
    Simple grep-like functionality that works with any text file.
    Search is always case insensitive.

    Args:
      file_path: Path to the file, relative to the Neo4j import directory.
      query: The string to search for.

    Returns:
        dict: A dictionary with 'status' ('success' or 'error').
              If 'success', includes 'search_results' containing 'matching_lines'
              (a list of dictionaries with 'line_number' and 'content' keys)
              and basic metadata about the search.
              If 'error', includes an 'error_message'.
    """
    import_dir = Path(get_neo4j_import_dir())
    p = import_dir / file_path

    if not p.exists():
        return tool_error(f"File does not exist: {file_path}")
    if not p.is_file():
        return tool_error(f"Path is not a file: {file_path}")

    # Handle empty query - return no results
    if not query:
        return tool_success(SEARCH_RESULTS, {
            "metadata": {
                "path": file_path,
                "query": query,
                "lines_found": 0
            },
            "matching_lines": []
        })

    matching_lines = []
    search_query = query.lower()
    
    try:
        with open(p, 'r', encoding='utf-8') as file:
            # Process the file line by line
            for i, line in enumerate(file, 1):
                line_to_check = line.lower()
                if search_query in line_to_check:
                    matching_lines.append({
                        "line_number": i,
                        "content": line.strip()  # Remove trailing newlines
                    })
                        
    except Exception as e:
        return tool_error(f"Error reading or searching file {file_path}: {e}")

    # Prepare basic metadata
    metadata = {
        "path": file_path,
        "query": query,
        "lines_found": len(matching_lines)
    }
    
    result_data = {
        "metadata": metadata,
        "matching_lines": matching_lines
    }
    return tool_success(SEARCH_RESULTS, result_data)

#  Tool: Propose Node Construction

PROPOSED_CONSTRUCTION_PLAN = "proposed_construction_plan"
NODE_CONSTRUCTION = "node_construction"

def propose_node_construction(approved_file: str, proposed_label: str, unique_column_name: str, proposed_properties: list[str], tool_context:ToolContext) -> dict:
    """Propose a node construction for an approved file that supports the user goal.

    The construction will be added to the proposed construction plan dictionary under using proposed_label as the key.

    The construction entry will be a dictionary with the following keys:
    - construction_type: "node"
    - source_file: the approved file to propose a node construction for
    - label: the proposed label of the node
    - unique_column_name: the name of the column that will be used to uniquely identify constructed nodes
    - properties: A list of property names for the node, derived from column names in the approved file

    Args:
        approved_file: The approved file to propose a node construction for
        proposed_label: The proposed label for constructed nodes (used as key in the construction plan)
        unique_column_name: The name of the column that will be used to uniquely identify constructed nodes
        proposed_properties: column names that should be imported as node properties

    Returns:
        dict: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a "node_construction" key with the construction plan for the node
                If 'error', includes an 'error_message' key.
                The 'error_message' may have instructions about how to handle the error.
    """
    # quick sanity check -- does the approved file have the unique column?
    search_results = search_file(approved_file, unique_column_name)
    if search_results["status"] == "error":
        return search_results # return the error
    if search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(f"{approved_file} does not have the column {unique_column_name}. Check the file content and try again.")

    # get the current construction plan, or an empty one if none exists
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    node_construction_rule = {
        "construction_type": "node",
        "source_file": approved_file,
        "label": proposed_label,
        "unique_column_name": unique_column_name,
        "properties": proposed_properties
    }   
    construction_plan[proposed_label] = node_construction_rule
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    return tool_success(NODE_CONSTRUCTION, node_construction_rule)

RELATIONSHIP_CONSTRUCTION = "relationship_construction"

def propose_relationship_construction(approved_file: str, proposed_relationship_type: str, 
    from_node_label: str,from_node_column: str, to_node_label:str, to_node_column: str, 
    proposed_properties: list[str], 
    tool_context:ToolContext) -> dict:
    """Propose a relationship construction for an approved file that supports the user goal.

    The construction will be added to the proposed construction plan dictionary under using proposed_relationship_type as the key.

    Args:
        approved_file: The approved file to propose a node construction for
        proposed_relationship_type: The proposed label for constructed relationships
        from_node_label: The label of the source node
        from_node_column: The name of the column within the approved file that will be used to uniquely identify source nodes
        to_node_label: The label of the target node
        to_node_column: The name of the column within the approved file that will be used to uniquely identify target nodes
        unique_column_name: The name of the column that will be used to uniquely identify target nodes

    Returns:
        dict: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a "relationship_construction" key with the construction plan for the node
                If 'error', includes an 'error_message' key.
                The 'error_message' may have instructions about how to handle the error.
    """
    # quick sanity check -- does the approved file have the from_node_column?
    search_results = search_file(approved_file, from_node_column)
    if search_results["status"] == "error": 
        return search_results  # return the error if there is one
    if search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(f"{approved_file} does not have the from node column {from_node_column}. Check the content of the file and reconsider the relationship.")

    # quick sanity check -- does the approved file have the to_node_column?
    search_results = search_file(approved_file, to_node_column)
    if search_results["status"] == "error" or search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(f"{approved_file} does not have the to node column {to_node_column}. Check the content of the file and reconsider the relationship.")

    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    relationship_construction_rule = {
        "construction_type": "relationship",
        "source_file": approved_file,
        "relationship_type": proposed_relationship_type,
        "from_node_label": from_node_label,
        "from_node_column": from_node_column,
        "to_node_label": to_node_label,
        "to_node_column": to_node_column,
        "properties": proposed_properties
    }   
    construction_plan[proposed_relationship_type] = relationship_construction_rule
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    return tool_success(RELATIONSHIP_CONSTRUCTION, relationship_construction_rule)

# Tool: Remove Node Construction
def remove_node_construction(node_label: str, tool_context:ToolContext) -> dict:
    """Remove a node construction from the proposed construction plan based on label.

    Args:
        node_label: The label of the node construction to remove
        tool_context: The tool context

    Returns:
        dict: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a 'node_construction_removed' key with the label of the removed node construction
                If 'error', includes an 'error_message' key.
                The 'error_message' may have instructions about how to handle the error.
    """
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    if node_label not in construction_plan:
        return tool_success("node construction rule not found. removal not needed.")

    del construction_plan[node_label]

    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    return tool_success("node_construction_removed", node_label)

# Tool: Remove Relationship Construction
def remove_relationship_construction(relationship_type: str, tool_context:ToolContext) -> dict:
    """Remove a relationship construction from the proposed construction plan based on type.

    Args:
        relationship_type: The type of the relationship construction to remove
        tool_context: The tool context

    Returns:
        dict: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a 'relationship_construction_removed' key with the type of the removed relationship construction
                If 'error', includes an 'error_message' key.
                The 'error_message' may have instructions about how to handle the error.
    """
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})

    if relationship_type not in construction_plan:
        return tool_success("relationship construction rule not found. removal not needed.")
    
    construction_plan.pop(relationship_type)
    
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    return tool_success("relationship_construction_removed", relationship_type) 

# Tool: Get Proposed construction Plan
def get_proposed_construction_plan(tool_context:ToolContext) -> dict:
    """Get the proposed construction plan, a dictionary of construction rules."""
    return tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})

# Tool: Approve the proposed construction plan
APPROVED_CONSTRUCTION_PLAN = "approved_construction_plan"

def approve_proposed_construction_plan(tool_context:ToolContext) -> dict:
    """Approve the proposed construction plan, if there is one."""
    if not PROPOSED_CONSTRUCTION_PLAN in tool_context.state:
        return tool_error("No proposed construction plan found. Propose a plan first.")
    
    tool_context.state[APPROVED_CONSTRUCTION_PLAN] = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN)
    return tool_success(APPROVED_CONSTRUCTION_PLAN, tool_context.state[APPROVED_CONSTRUCTION_PLAN])

def get_proposed_schema(tool_context:ToolContext) -> dict:
    """Get the proposed schema, derived from the proposed construction plan."""
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    
    if not construction_plan:
        return tool_error("No proposed construction plan found. Propose a plan first.")
    
    schema = {
        "nodes": [],
        "relationships": []
    }
    
    for rule in construction_plan.values():
        if rule["construction_type"] == "node":
            schema["nodes"].append({
                "label": rule["label"],
                "unique_column_name": rule["unique_column_name"],
                "properties": rule["properties"]
            })
        elif rule["construction_type"] == "relationship":
            schema["relationships"].append({
                "relationship_type": rule["relationship_type"],
                "from_node_label": rule["from_node_label"],
                "from_node_column": rule["from_node_column"],
                "to_node_label": rule["to_node_label"],
                "to_node_column": rule["to_node_column"],
                "properties": rule["properties"]
            })
            
    return tool_success("proposed_schema", schema)

# initialize context with blank feedback, which may get filled later by the schema_critic_agent
def initialize_feedback(callback_context: CallbackContext) -> None:
    callback_context.state["feedback"] = ""

# List of tools for the structured schema proposal agent
structured_schema_proposal_agent_tools = [
    approve_perceived_user_goal, approve_suggested_files,
    get_proposed_construction_plan,
    sample_file, search_file,
    propose_node_construction, propose_relationship_construction, 
    remove_node_construction, remove_relationship_construction
]

schema_critic_agent_tools = [
    approve_perceived_user_goal, approve_suggested_files,
    get_proposed_construction_plan,
    sample_file, search_file
]