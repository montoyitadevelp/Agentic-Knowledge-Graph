from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
from structured_data_agents.tools import structured_schema_proposal_agent_tools, schema_critic_agent_tools, get_proposed_construction_plan, approve_proposed_construction_plan, initialize_feedback, get_proposed_schema
from structured_data_agents.loop import CheckStatusAndEscalate
from google.adk.agents.loop_agent import LoopAgent
from google.adk.tools import agent_tool

load_dotenv()

proposal_agent_prompt = """
    You are an expert at knowledge graph modeling with property graphs. Propose an appropriate
    schema by specifying construction rules which transform approved files into nodes or relationships.
    The resulting schema should describe a knowledge graph based on the user goal.
    
    Consider feedback if it is available: 
    <feedback>
    {feedback}
    </feedback> 
    
     Every file in the approved files list will become either a node or a relationship.
    Determining whether a file likely represents a node or a relationship is based
    on a hint from the filename (is it a single thing or two things) and the
    identifiers found within the file.

    Because unique identifiers are so important for determining the structure of the graph,
    always verify the uniqueness of suspected unique identifiers using the 'search_file' tool.

    General guidance for identifying a node or a relationship:
    - If the file name is singular and has only 1 unique identifier it is likely a node
    - If the file name is a combination of two things, it is likely a full relationship
    - If the file name sounds like a node, but there are multiple unique identifiers, that is likely a node with reference relationships

    Design rules for nodes:
    - Nodes will have unique identifiers. 
    - Nodes _may_ have identifiers that are used as reference relationships.

    Design rules for relationships:
    - Relationships appear in two ways: full relationships and reference relationships.

    Full relationships:
    - Full relationships appear in dedicated relationship files, often having a filename that references two entities
    - Full relationships typically have references to a source and destination node.
    - Full relationships _do not have_ unique identifiers, but instead have references to the primary keys of the source and destination nodes.
    - The absence of a single, unique identifier is a strong indicator that a file is a full relationship.
    
    Reference relationships:
    - Reference relationships appear as foreign key references in node files
    - Reference relationship foreign key column names often hint at the destination node and relationship type
    - References may be hierarchical container relationships, with terminology revealing parent-child, "has", "contains", membership, or similar relationship
    - References may be peer relationships, that is often a self-reference to a similar class of nodes. For example, "knows" or "see also"

    The resulting schema should be a connected graph, with no isolated components.
    
    Prepare for the task:
    - get the user goal using the 'approve_perceived_user_goal' tool
    - get the list of approved files using the 'approve_suggested_files' tool
    - get the current construction plan using the 'get_proposed_construction_plan' tool

    Think carefully, using tools to perform actions and reconsidering your actions when a tool returns an error:
    1. For each approved file, consider whether it represents a node or relationship. Check the content for potential unique identifiers using the 'sample_file' tool.
    2. For each identifier, verify that it is unique by using the 'search_file' tool.
    3. Use the node vs relationship guidance for deciding whether the file represents a node or a relationship.
    4. For a node file, propose a node construction using the 'propose_node_construction' tool. 
    5. If the node contains a reference relationship, use the 'propose_relationship_construction' tool to propose a relationship construction. 
    6. For a relationship file, propose a relationship construction using the 'propose_relationship_construction' tool
    7. If you need to remove a construction, use the 'remove_node_construction' or 'remove_relationship_construction' tool
    8. When you are done with construction proposals, use the 'get_proposed_construction_plan' tool to present the plan to the user
"""

llm = LiteLlm(model="gemini/gemini-2.5-flash")

# a helper function to log the agent name during execution
def log_agent(callback_context: CallbackContext) -> None:
    print(f"\n### Entering Agent: {callback_context.agent_name}")
    
schema_proposal_agent = LlmAgent(
    name="schema_proposal_agent_v1",
    description="Proposes a knowledge graph schema based on the user goal and approved file list",
    model=llm,
    instruction=proposal_agent_prompt,
    tools=structured_schema_proposal_agent_tools,
    before_agent_callback=log_agent
)

critic_agent_prompt = """
    You are an expert at knowledge graph modeling with property graphs. 
    Criticize the proposed schema for relevance to the user goal and approved files
    
    Criticize the proposed schema for relevance and correctness:
    - Are unique identifiers actually unique? Use the 'search_file' tool to validate. Composite identifier are not acceptable.
    - Could any nodes be relationships instead? Double-check that unique identifiers are unique and not references to other nodes. Use the 'search_file' tool to validate
    - Can you manually trace through the source data to find the necessary information for anwering a hypothetical question?
    - Is every node in the schema connected? What relationships could be missing? Every node should connect to at least one other node.
    - Are hierarchical container relationships missing? 
    - Are any relationships redundant? A relationship between two nodes is redundant if it is semantically equivalent to or the inverse of another relationship between those two nodes.
    
    Prepare for the task:
    - get the user goal using the 'approve_perceived_user_goal' tool
    - get the list of approved files using the 'approve_suggested_files' tool
    - get the construction plan using the 'get_proposed_construction_plan' tool
    - use the 'sample_file' and 'search_file' tools to validate the schema design

    Think carefully, using tools to perform actions and reconsidering your actions when a tool returns an error:
    1. Analyze each construction rule in the proposed construction plan.
    2. Use tools to validate the construction rules for relevance and correctness.
    3. If the schema looks good, respond with a one word reply: 'valid'.
    4. If the schema has problems, respond with 'retry' and provide feedback as a concise bullet list of problems.
"""

schema_critic_agent = LlmAgent(
    name="schema_critic_agent_v1",
    description="Criticizes the proposed schema for relevance to the user goal and approved files.",
    model=llm,
    instruction=critic_agent_prompt,
    tools=schema_critic_agent_tools, 
    output_key="feedback", # specify the context state key which will contain the result of calling the critic,
    before_agent_callback=log_agent
)

schema_refinement_loop = LoopAgent(
    name="schema_refinement_loop",
    description="Analyzes approved files to propose a schema based on user intent and feedback",
    max_iterations=3,
    sub_agents=[schema_proposal_agent, schema_critic_agent, CheckStatusAndEscalate(name="StopChecker")],
    before_agent_callback=log_agent
)

schema_proposal_coordinator_instruction = """
    You are a coordinator for the schema proposal process. Use tools to propose a schema to the user.
    If the user disapproves, use the tools to refine the schema and ask the user to approve again.
    If the user approves, use the 'approve_proposed_schema' tool to record the approval.
    When the schema approval has been recorded, use the 'finished' tool.

    Guidance for tool use:
    - Use the 'schema_refinement_loop' tool to produce or update a proposed schema with construction rules. 
    - Use the 'get_proposed_schema' tool to get the proposed schema
    - Use the 'get_proposed_construction_plan' tool to get the construction rules for transforming approved files into the schema
    - Present the proposed schema and construction rules to the user for approval
    - If they disapprove, consider their feedback and go back to step 1
    - If the user approves, use the 'approve_proposed_schema' tool and the 'approve_proposed_construction_plan' tool to record the approval
"""

refinement_loop_as_tool = agent_tool.AgentTool(schema_refinement_loop)

schema_proposal_coordinator = LlmAgent(
    name="schema_proposal_coordinator",
    model=llm,
    instruction=schema_proposal_coordinator_instruction,
    tools=[
        refinement_loop_as_tool, 
        get_proposed_construction_plan, 
        approve_proposed_construction_plan,
        get_proposed_schema
    ], 
    before_agent_callback=initialize_feedback
)

root_agent = schema_proposal_coordinator

