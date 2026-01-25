from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
from file_suggestion_agent.tools import file_suggestion_agent_tools

load_dotenv()

llm = LiteLlm(model="gemini/gemini-2.5-flash")


file_suggestion_agent_instruction = """
You are a constructive critic AI reviewing a list of files. Your goal is to suggest relevant files
for constructing a knowledge graph.

**Task:**
Review the file list for relevance to the kind of graph and description specified in the approved user goal. 

For any file that you're not sure about, use the 'sample_file' tool to get 
a better understanding of the file contents. 

Only consider structured data files like CSV, JSON or Markdown files

Prepare for the task:
- use the 'approve_perceived_user_goal' tool to get the approved user goal

Think carefully, repeating these steps until finished:
1. list available files using the 'list_available_files' tool
2. evaluate the relevance of each file, then record the list of suggested files using the 'set_suggested_files' tool
3. use the 'get_suggested_files' tool to get the list of suggested files
4. ask the user to approve the set of suggested files
5. If the user has feedback, go back to step 1 with that feedback in mind
6. If approved, use the 'approve_suggested_files' tool to record the approval
"""


file_suggestion_agent = Agent(
    name="file_suggestion_agent_v1",
    model=llm, # defined earlier in a variable
    description="Helps the user select files to import.",
    instruction=file_suggestion_agent_instruction,
    tools=file_suggestion_agent_tools,
)

# Expose the agent as root_agent for the ADK CLI
root_agent = file_suggestion_agent