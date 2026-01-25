from dotenv import load_dotenv
from neo4j_for_adk import tool_success, tool_error
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import ToolContext
from file_suggestion_agent.tools import approve_suggested_files, sample_file
from indent_agent.tools import approve_perceived_user_goal

load_dotenv()

# tools to propose and approve entity types
PROPOSED_ENTITIES = "proposed_entity_types"
APPROVED_ENTITIES = "approved_entity_types"

def set_proposed_entities(proposed_entity_types: list[str], tool_context:ToolContext) -> dict:
    """Sets the list proposed entity types to extract from unstructured text."""
    tool_context.state[PROPOSED_ENTITIES] = proposed_entity_types
    return tool_success(PROPOSED_ENTITIES, proposed_entity_types)

def get_proposed_entities(tool_context:ToolContext) -> dict:
    """Gets the list of proposed entity types to extract from unstructured text."""
    return tool_context.state.get(PROPOSED_ENTITIES, [])

def approve_proposed_entities(tool_context:ToolContext) -> dict:
    """Upon approval from user, records the proposed entity types as an approved list of entity types 

    Only call this tool if the user has explicitly approved the suggested files.
    """
    if PROPOSED_ENTITIES not in tool_context.state:
        return tool_error("No proposed entity types to approve. Please set proposed entities first, ask for user approval, then call this tool.")
    tool_context.state[APPROVED_ENTITIES] = tool_context.state.get(PROPOSED_ENTITIES)
    return tool_success(APPROVED_ENTITIES, tool_context.state[APPROVED_ENTITIES])

def get_approved_entities(tool_context:ToolContext) -> dict:
    """Get the approved list of entity types to extract from unstructured text."""
    return tool_context.state.get(APPROVED_ENTITIES, [])

def get_well_known_types(tool_context:ToolContext) -> dict:
    """Gets the approved labels that represent well-known entity types in the graph schema."""
    construction_plan = tool_context.state.get("approved_construction_plan", {})
    # approved labels are the keys for each construction plan entry where `construction_type` is "node"
    approved_labels = {entry["label"] for entry in construction_plan.values() if entry["construction_type"] == "node"}
    return tool_success("approved_labels", approved_labels)

PROPOSED_FACTS = "proposed_fact_types"
APPROVED_FACTS = "approved_fact_types"

def add_proposed_fact(approved_subject_label:str,
                      proposed_predicate_label:str,
                      approved_object_label:str,
                      tool_context:ToolContext) -> dict:
    """Add a proposed type of fact that could be extracted from the files.

    A proposed fact type is a tuple of (subject, predicate, object) where
    the subject and object are approved entity types and the predicate 
    is a proposed relationship label.

    Args:
      approved_subject_label: approved label of the subject entity type
      proposed_predicate_label: label of the predicate
      approved_object_label: approved label of the object entity type
    """
    # Guard against invalid labels
    approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
    
    if approved_subject_label not in approved_entities:
        return tool_error(f"Approved subject label {approved_subject_label} not found. Try again.")
    if approved_object_label not in approved_entities:
        return tool_error(f"Approved object label {approved_object_label} not found. Try again.")
    
    current_predicates = tool_context.state.get(PROPOSED_FACTS, {})
    current_predicates[proposed_predicate_label] = {
        "subject_label": approved_subject_label,
        "predicate_label": proposed_predicate_label,
        "object_label": approved_object_label
    }
    tool_context.state[PROPOSED_FACTS] = current_predicates
    return tool_success(PROPOSED_FACTS, current_predicates)
    
def get_proposed_facts(tool_context:ToolContext) -> dict:
    """Get the proposed types of facts that could be extracted from the files."""
    return tool_context.state.get(PROPOSED_FACTS, {})


def approve_proposed_facts(tool_context:ToolContext) -> dict:
    """Upon user approval, records the proposed fact types as approved fact types

    Only call this tool if the user has explicitly approved the proposed fact types.
    """
    if PROPOSED_FACTS not in tool_context.state:
        return tool_error("No proposed fact types to approve. Please set proposed facts first, ask for user approval, then call this tool.")
    tool_context.state[APPROVED_FACTS] = tool_context.state.get(PROPOSED_FACTS)
    return tool_success(APPROVED_FACTS, tool_context.state[APPROVED_FACTS])


ner_agent_tools = [
    approve_perceived_user_goal, approve_suggested_files, sample_file,
    get_well_known_types,
    set_proposed_entities,
    approve_proposed_entities,
    get_proposed_entities
]

fact_agent_tools = [
    approve_perceived_user_goal, approve_suggested_files,
    get_approved_entities,
    sample_file,
    add_proposed_fact,
    get_proposed_facts,
    approve_proposed_facts
]
