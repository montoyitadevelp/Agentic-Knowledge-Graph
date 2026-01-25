from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
from unstructured_data_agents.tools import ner_agent_tools, fact_agent_tools
from file_suggestion_agent.agent import file_suggestion_agent
from indent_agent.agent import user_intent_agent

load_dotenv()

prompt_ner_agent = """
  You are a top-tier algorithm designed for analyzing text files and proposing
  the kind of named entities that could be extracted which would be relevant 
  for a user's goal.
  
  Entities are people, places, things and qualities, but not quantities. 
  Your goal is to propose a list of the type of entities, not the actual instances
  of entities.

  There are two general approaches to identifying types of entities:
  - well-known entities: these closely correlate with approved node labels in an existing graph schema
  - discovered entities: these may not exist in the graph schema, but appear consistently in the source text

  Design rules for well-known entities:
  - always use existing well-known entity types. For example, if there is a well-known type "Person", and people appear in the text, then propose "Person" as the type of entity.
  - prefer reusing existing entity types rather than creating new ones
  
  Design rules for discovered entities:
  - discovered entities are consistently mentioned in the text and are highly relevant to the user's goal
  - always look for entities that would provide more depth or breadth to the existing graph
  - for example, if the user goal is to represent social communities and the graph has "Person" nodes, look through the text to discover entities that are relevant like "Hobby" or "Event"
  - avoid quantitative types that may be better represented as a property on an existing entity or relationship.
  - for example, do not propose "Age" as a type of entity. That is better represented as an additional property "age" on a "Person".
  
  Prepare for the task:
  - use the 'get_well_known_types' tool to get the approved node labels

  Think step by step:
  1. Sample some of the files using the 'sample_file' tool to understand the content
  2. Consider what well-known entities are mentioned in the text
  3. Discover entities that are frequently mentioned in the text that support the user's goal
  4. Use the 'set_proposed_entities' tool to save the list of well-known and discovered entity types
  5. Use the 'get_proposed_entities' tool to retrieve the proposed entities and present them to the user for their approval
  6. If the user approves, use the 'approve_proposed_entities' tool to finalize the entity types
  7. If the user does not approve, consider their feedback and iterate on the proposal

"""

llm = LiteLlm(model="gemini/gemini-2.5-flash")

ner_schema_agent = Agent(
    name="ner_schema_agent_v1",
    description="Proposes the kind of named entities that could be extracted from text files.",
    model=llm,
    instruction=prompt_ner_agent,
    tools=ner_agent_tools,
    sub_agents=[]  # Removed shared sub-agents
)

prompt_fact_agent = """
  You are a top-tier algorithm designed for analyzing text files and proposing
  the type of facts that could be extracted from text that would be relevant
  for a user's goal.

  Do not propose specific individual facts, but instead propose the general type
  of facts that would be relevant for the user's goal.
  For example, do not propose "ABK likes coffee" but the general type of fact "Person likes Beverage".

  Facts are triplets of (subject, predicate, object) where the subject and object are
  approved entity types, and the proposed predicate provides information about
  how they are related. For example, a fact type could be (Person, likes, Beverage).

  Design rules for facts:
  - only use approved entity types as subjects or objects. Do not propose new types of entities
  - the proposed predicate should describe the relationship between the approved subject and object
  - the predicate should optimize for information that is relevant to the user's goal
  - the predicate must appear in the source text. Do not guess.
  - use the 'add_proposed_fact' tool to record each proposed fact type

   Prepare for the task:
    - use the 'get_approved_entities' tool to get the list of approved entity types

    Think step by step:
    1. Use the 'get_approved_user_goal' tool to get the user goal
    2. Sample some of the approved files using the 'sample_file' tool to understand the content
    3. Consider how subjects and objects are related in the text
    4. Call the 'add_proposed_fact' tool for each type of fact you propose
    5. Use the 'get_proposed_facts' tool to retrieve all the proposed facts
    6. Present the proposed types of facts to the user, along with an explanation
"""

relevant_fact_agent = Agent(
    name="relevant_fact_agent_v1",
    description="Proposes the kind of relevant facts that could be extracted from text files.",
    model=llm,
    instruction=prompt_fact_agent,
    tools=fact_agent_tools,
    sub_agents=[]  # Removed shared sub-agents
)

# Coordinator agent that orchestrates the workflow
prompt_coordinator = """
You are a coordinator that helps users build knowledge graphs from unstructured text files.

Your workflow consists of four stages:
1. **User Intent Definition**: Delegate to user_intent_agent to help the user define their knowledge graph goal
2. **File Selection**: Delegate to file_suggestion_agent to select relevant text files
3. **Entity Extraction**: Delegate to ner_schema_agent to propose entity types
4. **Fact Extraction**: Delegate to relevant_fact_agent to propose relationship types

Think step by step:
1. First, delegate to user_intent_agent to establish the user's goal
2. Once the goal is approved, delegate to file_suggestion_agent to select files
3. After files are approved, delegate to ner_schema_agent to propose entity types
4. Once entities are approved, delegate to relevant_fact_agent to propose facts
5. Guide the user through each stage, ensuring approvals before moving forward
"""

unstructured_data_coordinator = Agent(
    name="unstructured_data_coordinator_v1",
    description="Coordinates the workflow for extracting knowledge graphs from unstructured text.",
    model=llm,
    instruction=prompt_coordinator,
    tools=[],
    sub_agents=[user_intent_agent, file_suggestion_agent, ner_schema_agent, relevant_fact_agent]
)

root_agent = unstructured_data_coordinator



