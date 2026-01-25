import re
from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.components.types import TextChunk, TextChunks
from neo4j_graphrag.experimental.components.pdf_loader import DataLoader
from neo4j_graphrag.experimental.components.types import PdfDocument, DocumentInfo
from neo4j_graphrag.llm import VertexAILLM
from neo4j_graphrag.embeddings import VertexAIEmbeddings
from pathlib import Path
from neo4j_for_adk import graphdb

# Define a custom text splitter. Chunking strategy could be yet-another-agent
class RegexTextSplitter(TextSplitter):
    """Split text using regex matched delimiters."""
    def __init__(self, re: str):
        self.re = re
    
    async def run(self, text: str) -> TextChunks:
        """Splits a piece of text into chunks.

        Args:
            text (str): The text to be split.

        Returns:
            TextChunks: A list of chunks.
        """
        texts = re.split(self.re, text)
        i = 0
        chunks = [TextChunk(text=str(text), index=i) for (i, text) in enumerate(texts)]
        return TextChunks(chunks=chunks)
    
# custom file data loader
class MarkdownDataLoader(DataLoader):
    def extract_title(self,markdown_text):
        # Define a regex pattern to match the first h1 header
        pattern = r'^# (.+)$'

        # Search for the first match in the markdown text
        match = re.search(pattern, markdown_text, re.MULTILINE)

        # Return the matched group if found
        return match.group(1) if match else "Untitled"

    async def run(self, filepath: Path, metadata = {}) -> PdfDocument:
        with open(filepath, "r") as f:
            markdown_text = f.read()
        doc_headline = self.extract_title(markdown_text)
        markdown_info = DocumentInfo(
            path=str(filepath),
            metadata={
                "title": doc_headline,
            }
        )
        return PdfDocument(text=markdown_text, document_info=markdown_info)
    
def file_context(file_path:str, num_lines=5) -> str:
    """Helper function to extract the first few lines of a file

    Args:
        file_path (str): Path to the file
        num_lines (int, optional): Number of lines to extract. Defaults to 5.

    Returns:
        str: First few lines of the file
    """
    with open(file_path, 'r') as f:
        lines = []
        for _ in range(num_lines):
            line = f.readline()
            if not line:
                break
            lines.append(line)
    return "\n".join(lines)

# per-chunk entity extraction prompt, with context
def contextualize_er_extraction_prompt(context:str) -> str:
    """Creates a prompt with pre-amble file content for context during entity+relationship extraction.
    The context is concatenated into the string, which later will be used as a template
    for values like {schema} and {text}.
    """
    general_instructions = """
    You are a top-tier algorithm designed for extracting
    information in structured formats to build a knowledge graph.

    Extract the entities (nodes) and specify their type from the following text.
    Also extract the relationships between these nodes.

    Return result as JSON using the following format:
    {{"nodes": [ {{"id": "0", "label": "Person", "properties": {{"name": "John"}} }}],
    "relationships": [{{"type": "KNOWS", "start_node_id": "0", "end_node_id": "1", "properties": {{"since": "2024-08-01"}} }}] }}

    Use only the following node and relationship types (if provided):
    {schema}

    Assign a unique ID (string) to each node, and reuse it to define relationships.
    Do respect the source and target node types for relationship and
    the relationship direction.

    Make sure you adhere to the following rules to produce valid JSON objects:
    - Do not return any additional information other than the JSON in it.
    - Omit any backticks around the JSON - simply output the JSON on its own.
    - The JSON object must not wrapped into a list - it is its own JSON object.
    - Property names must be enclosed in double quotes
    """

    context_goes_here = f"""
    Consider the following context to help identify entities and relationships:
    <context>
    {context}  
    </context>"""
    
    input_goes_here = """
    Input text:

    {text}
    """

    return general_instructions + "\n" + context_goes_here + "\n" + input_goes_here
    

# create an Gemini client for use by Neo4j GraphRAG
llm_for_neo4j = VertexAILLM(model_name="gemini-2.5-flash", model_params={"temperature": 0})
  
# use Gemini for creating embeddings
embedder = VertexAIEmbeddings(model="textembedding-gecko-001")

# use the same driver set up by neo4j_for_adk.py
neo4j_driver = graphdb.get_driver()

