import asyncio
from main_call import make_agent_caller
from unstructured_data_agents.agent import ner_schema_agent

async def main():
    ner_agent_initial_state = {
    "approved_user_goal": {
        "kind_of_graph": "supply chain analysis",
        "description": """A multi-level bill of materials for manufactured products, useful for root cause analysis. 
        Add product reviews to start analysis from reported issues like quality, difficulty, or durability."""
    },
    "approved_files": [
        "product_reviews/gothenburg_table_reviews.md",
        "product_reviews/helsingborg_dresser_reviews.md",
        "product_reviews/jonkoping_coffee_table_reviews.md",
        "product_reviews/linkoping_bed_reviews.md",
        "product_reviews/malmo_desk_reviews.md",
        "product_reviews/norrkoping_nightstand_reviews.md",
        "product_reviews/orebro_lamp_reviews.md",
        "product_reviews/stockholm_chair_reviews.md",
        "product_reviews/uppsala_sofa_reviews.md",
        "product_reviews/vasteras_bookshelf_reviews.md"
    ],
    "approved_construction_plan": {
        "Product": {
            "construction_type": "node",
            "label": "Product",
        },
        "Assembly": {
            "construction_type": "node",
            "label": "Assembly",
        },
        "Part": {
            "construction_type": "node",
            "label": "Part",
        },
        "Supplier": {
            "construction_type": "node",
            "label": "Supplier",
        }
        # Relationship construction omitted, since it won't get used in this notebook
    }
}
    ner_agent_caller = await make_agent_caller(ner_schema_agent, ner_agent_initial_state)

    await ner_agent_caller.call("Add product reviews to the knowledge graph to trace product complaints back through the manufacturing process.")


if __name__ == "__main__":
    asyncio.run(main())

