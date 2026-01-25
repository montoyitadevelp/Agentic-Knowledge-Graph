# 🕸️ Agentic Knowledge Graph

[![Google ADK](https://img.shields.io/badge/Google_ADK-1.5.0-4285F4?logo=google&logoColor=white)](https://github.com/google/generative-ai-python)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-8E75B2?logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.28.1-008CC1?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-1.73.6-000000?logo=openai&logoColor=white)](https://github.com/BerriAI/litellm)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

> 🤖 Multi-agent system that automatically constructs knowledge graphs from structured data using Google's Agent Development Kit (ADK) and Neo4j

## 🎯 What Does It Do?

This project uses AI agents to transform CSV and JSON files into rich knowledge graphs stored in Neo4j. It analyzes your data, proposes optimal graph schemas, and loads everything automatically.

## 🏗️ How ADK Works

**Google ADK (Agent Development Kit)** is a framework for building AI agent systems:

- 🧠 **Agents**: AI entities with specific roles, powered by LLMs (we use Gemini 2.5 Flash via LiteLLM)
- 🔧 **Tools**: Functions agents can call to perform actions (file operations, database queries, etc.)
- 💾 **Memory**: Persistent state management through `ToolContext` and session services
- 🔄 **Orchestration**: Agents can delegate tasks to sub-agents or iterate through refinement loops

### Agent Collaboration Pattern

```
User Request → Coordinator Agent → Sub-Agent 1 (uses tools)
                                 ↓
                                 → Sub-Agent 2 (uses tools)
                                 ↓
                                 → LoopAgent (iterative refinement)
                                 ↓
                                 ← Aggregated Response
```

**Key Concepts:**
- **Tools**: Return `{'status': 'success'/'error', 'data': ...}` dictionaries
- **State**: Shared memory accessible via `tool_context.state` for inter-agent communication
- **Sessions**: Managed by `InMemorySessionService` for persistent conversations

## 🤖 Agent Architecture

### 1️⃣ **Indent Agent** (`indent_agent/`)
🎯 **Purpose**: Captures and approves user goals for knowledge graph creation

**What it does:**
- Prompts user to describe their desired knowledge graph
- Validates and stores the approved goal in shared state
- Kickstarts the entire workflow

---

### 2️⃣ **File Suggestion Agent** (`file_suggestion_agent/`)
📁 **Purpose**: Recommends relevant data files for graph construction

**What it does:**
- Lists available CSV/JSON files from `NEO4J_IMPORT_DIR`
- Samples file contents to understand structure
- Suggests files matching the user's goal
- Manages user approval workflow

**Tools:**
- `list_files`: Scans import directory
- `sample_file`: Previews file contents
- `approve_files`: Stores approved files in state

---

### 3️⃣ **Structured Data Agents** (`structured_data_agents/`)
🏗️ **Purpose**: Designs optimal knowledge graph schema through iterative refinement

**Complex multi-agent system with:**

#### **Schema Proposal Agent**
- Analyzes approved files to identify nodes vs relationships
- Distinguishes:
  - **Nodes**: Files with single unique identifier
  - **Full Relationships**: Dedicated relationship files
  - **Reference Relationships**: Foreign keys in node files
- Validates uniqueness using `search_file` tool

#### **Schema Critic Agent**
- Reviews proposed schemas for correctness
- Ensures graph connectivity (no isolated components)
- Validates construction rules

#### **Schema Refinement Loop** (LoopAgent)
- Iterates between proposal → criticism → revision
- Continues until schema is validated or max iterations reached
- Produces final construction plan

#### **Schema Proposal Coordinator**
- Top-level orchestrator managing the entire refinement process
- Reads approved files from state
- Delegates to refinement loop
- Outputs `PROPOSED_CONSTRUCTION_PLAN`

**Tools:**
- `search_file`: Case-insensitive search for validating unique IDs
- `sample_file`: Inspects data structure

---

### 4️⃣ **Multi-Agent Coordinator** (`multi_agents/`)
👋 **Purpose**: Demonstration of agent composition patterns

**What it shows:**
- Sub-agent delegation
- Stateful greeting and farewell agents
- How to compose specialized agents

---

### 5️⃣ **Normal Agent** (`normal_agent/`)
🔰 **Purpose**: Simple demonstration agent

**What it shows:**
- Basic ADK agent structure
- Neo4j tool integration pattern
- Entry point for learning the framework

## 🗄️ Neo4j Integration

**Central Database Wrapper** (`neo4j_for_adk.py`):
- `Neo4jForADK`: ADK-friendly Neo4j interface
- `send_query(cypher_query, parameters)`: Execute Cypher queries
- `to_python()`: Converts Neo4j types to Python dicts
- `result_to_adk()`: Formats results for agent consumption

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (for Neo4j)
- Gemini API key

### 1. Clone & Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd Agentic-Knowledge-Graph

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
NEO4J_IMPORT_DIR=D:/path/to/your/data
```

### 3. Start Neo4j

```bash
# Pull Neo4j image
docker pull neo4j:5

# Run Neo4j container
docker run -d \
  --name agentic-kg-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Access Neo4j Browser at http://localhost:7474

### 4. Run Agents

```bash
# Navigate to agent directory
cd <agent_directory>

# Run agent
python call.py
```

Example:
```bash
cd structured_data_agents
python call.py
```

## 📂 Project Structure

```
Agentic-Knowledge-Graph/
├── data/                          # Data files for import
├── indent_agent/                  # Goal definition agent
│   ├── agent.py
│   ├── tools.py
│   └── call.py
├── file_suggestion_agent/         # File selection agent
│   ├── agent.py
│   ├── tools.py
│   └── call.py
├── structured_data_agents/        # Schema design agents
│   ├── schema_proposal_agent.py
│   ├── schema_critic_agent.py
│   ├── schema_refinement_loop.py
│   └── call.py
├── multi_agents/                  # Agent composition demo
├── normal_agent/                  # Basic agent demo
├── neo4j_for_adk.py              # Neo4j integration wrapper
├── requirements.txt
└── .env
```

## 🔄 Workflow Example

1. **User**: "I want to build a knowledge graph of my sales data"
2. **Indent Agent**: Captures and approves goal
3. **File Suggestion Agent**:
   - Lists: `customers.csv`, `orders.csv`, `products.json`
   - User approves files
4. **Structured Data Agents**:
   - Analyzes files
   - Proposes schema (e.g., Customer nodes, Product nodes, PURCHASED relationships)
   - Critic validates
   - Refines until optimal
5. **Construction** (future): Loads data into Neo4j

## 🛠️ Tech Stack

- **Google ADK 1.5.0**: Agent orchestration framework
- **LiteLLM 1.73.6**: LLM abstraction layer
- **Gemini 2.5 Flash**: Default LLM backend
- **Neo4j 5.28.1**: Graph database
- **Neo4j GraphRAG 1.8.0**: Graph utilities
- **RapidFuzz 3.13.0**: Fuzzy string matching

## 📝 Development Notes

**Agent Pattern:**
- Each agent has `agent.py` (definition), `tools.py` (functions), `call.py` (runner)

**Tool Pattern:**
- Always return `{'status': 'success'/'error', ...}`
- Never raise exceptions to agents

**State Management:**
- Use `tool_context.state[key]` for shared memory
- State persists across agent interactions

**Agent Composition:**
- Use `sub_agents` for delegation
- Wrap agents as tools with `AgentTool()`
- Use `LoopAgent` for iterative refinement

## 📄 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! This project demonstrates advanced ADK patterns for multi-agent knowledge graph construction.
