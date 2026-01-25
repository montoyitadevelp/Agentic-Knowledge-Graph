from dotenv import load_dotenv
from neo4j_for_adk import tool_success, tool_error, get_neo4j_import_dir
from google.adk.tools.tool_context import ToolContext
from pathlib import Path
from typing import List, Dict, Any
from itertools import islice
from google.adk.tools import ToolContext
from indent_agent.tools import approve_perceived_user_goal

load_dotenv()

# Tool: List Import Files

# this constant will be used as the key for storing the file list in the tool context state
ALL_AVAILABLE_FILES = "all_available_files"

def list_available_files(tool_context:ToolContext) -> dict:
    f"""Lists files available for knowledge graph construction.
    All files are relative to the import directory.

    Returns:
        dict: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a {ALL_AVAILABLE_FILES} key with list of file names.
                If 'error', includes an 'error_message' key.
                The 'error_message' may have instructions about how to handle the error.
    """
    # get the import dir using the helper function
    import_dir = Path(get_neo4j_import_dir())

    # get a list of relative file names, so files must be rooted at the import dir
    file_names = [str(x.relative_to(import_dir)) 
                 for x in import_dir.rglob("*") 
                 if x.is_file()]

    # save the list to state so we can inspect it later
    tool_context.state[ALL_AVAILABLE_FILES] = file_names

    return tool_success(ALL_AVAILABLE_FILES, file_names)

# Tool: Sample File
# This is a simple file reading tool that only works on files from the import directory
def sample_file(file_path: str, tool_context: ToolContext) -> dict:
    """Samples a file by reading its content as text.
    
    Treats any file as text and reads up to a maximum of 100 lines.
    
    Args:
      file_path: file to sample, relative to the import directory
      
    Returns:
        dict: A dictionary containing metadata about the content,
            along with a sampling of the file.
            Includes a 'status' key ('success' or 'error').
            If 'success', includes a 'content' key with textual file content.
            If 'error', includes an 'error_message' key.
            The 'error_message' may have instructions about how to handle the error.
    """
    # Trust, but verify. The agent may invent absolute file paths. 
    if Path(file_path).is_absolute():
        return tool_error("File path must be relative to the import directory. Make sure the file is from the list of available files.")
    
    import_dir = Path(get_neo4j_import_dir())

    # create the full path by extending from the import_dir
    full_path_to_file = import_dir / file_path
    
    # of course, _that_ may not exist
    if not full_path_to_file.exists():
        return tool_error(f"File does not exist in import directory. Make sure {file_path} is from the list of available files.")
    
    try:
        # Treat all files as text
        with open(full_path_to_file, 'r', encoding='utf-8') as file:
            # Read up to 100 lines
            lines = list(islice(file, 100))
            content = ''.join(lines)
            return tool_success("content", content)
    
    except Exception as e:
        return tool_error(f"Error reading or processing file {file_path}: {e}")
    
    # Tool: Set/Get suggested files
SUGGESTED_FILES = "suggested_files"

def set_suggested_files(suggest_files:List[str], tool_context:ToolContext) -> Dict[str, Any]:
    """Set the suggested files to be used for data import.

    Args:
        suggest_files (List[str]): List of file paths to suggest

    Returns:
        Dict[str, Any]: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a {SUGGESTED_FILES} key with list of file names.
                If 'error', includes an 'error_message' key.
                The 'error_message' may have instructions about how to handle the error.
    """
    tool_context.state[SUGGESTED_FILES] = suggest_files
    return tool_success(SUGGESTED_FILES, suggest_files)

# Helps encourage the LLM to first set the suggested files.
# This is an important strategy for maintaining consistency through defined values.
def get_suggested_files(tool_context:ToolContext) -> Dict[str, Any]:
    """Get the files to be used for data import.

    Returns:
        Dict[str, Any]: A dictionary containing metadata about the content.
                Includes a 'status' key ('success' or 'error').
                If 'success', includes a {SUGGESTED_FILES} key with list of file names.
                If 'error', includes an 'error_message' key.
    """
    return tool_success(SUGGESTED_FILES, tool_context.state[SUGGESTED_FILES])

# Tool: Approve Suggested Files
# Just like the previous lesson, you'll define a tool which
# accepts no arguments and can sanity check before approving.
APPROVED_FILES = "approved_files"

def approve_suggested_files(tool_context:ToolContext) -> Dict[str, Any]:
    """Approves the {SUGGESTED_FILES} in state for further processing as {APPROVED_FILES}.
    
    If {SUGGESTED_FILES} is not in state, return an error.
    """
    if SUGGESTED_FILES not in tool_context.state:
        return tool_error("Current files have not been set. Take no action other than to inform user.")

    tool_context.state[APPROVED_FILES] = tool_context.state[SUGGESTED_FILES]
    
# List of tools for the file suggestion agent
file_suggestion_agent_tools = [approve_perceived_user_goal, list_available_files, sample_file, 
    set_suggested_files, get_suggested_files,
    approve_suggested_files
]