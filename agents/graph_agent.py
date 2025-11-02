import os
import json
import mimetypes
from dotenv import load_dotenv
from services.gemini_client import get_gemini_client
from neo4j import GraphDatabase

# ✅ Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def build_graph_from_document(file_path: str, language: str = "English") -> str:
    """
    Extracts entities & relationships using Gemini and inserts them into Neo4j.
    Returns graph JSON for D3 visualization.
    """
    client = get_gemini_client()

    # Upload file to Gemini
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    uploaded_file = client.files.upload(file=file_path)

    system_prompt = (
    f"You are 'Lexis-Graph', an investigative legal case analyst.\n"
    f"Always respond in {language}.\n\n"
    "From the uploaded document, extract key *actors* and *relationships* relevant to the story of the case.\n"
    "Focus on people (petitioners, accused, witnesses, judges, lawyers), institutions (courts, police, organizations), "
    "and events (arrest, filing, judgment, investigation).\n"
    "Ignore generic entities like IPC sections, legal citations, or articles unless essential.\n"
    "Show relationships like:\n"
    "  (Person)-[:REPRESENTS]->(Person)\n"
    "  (Judge)-[:PRESIDED]->(Case)\n"
    "  (Police)-[:INVESTIGATED]->(Person)\n"
    "  (Court)-[:HEARD]->(Case)\n"
    "  (Event)-[:INVOLVES]->(Person)\n\n"
    " Return only valid JSON in the format:\n"
    "{ \"nodes\": [ {\"id\": \"string\", \"label\": \"string\", \"name\": \"string\"} ], "
    "\"edges\": [ {\"source\": \"string\", \"target\": \"string\", \"relation\": \"string\"} ] }\n"
    "Exclude legal sections, IPC codes, and citations to keep the graph focused and readable."
)


    # Generate structured graph data
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[system_prompt, uploaded_file]
    )

    text = (response.text or "{}").strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    try:
        graph_data = json.loads(text)
    except Exception:
        print("⚠️ Gemini response was not valid JSON — fallback to empty graph.")
        graph_data = {"nodes": [], "edges": []}

    # Ensure credentials
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("⚠️ Missing Neo4j credentials! Check your .env file.")
        return json.dumps(graph_data, indent=2)

    # ✅ Safe connection to Neo4j
    driver = None
    try:
        driver = GraphDatabase.driver(
            uri=str(NEO4J_URI),
            auth=(str(NEO4J_USERNAME), str(NEO4J_PASSWORD))
        )
        with driver.session(database=NEO4J_DATABASE) as session:
            # Reset previous data (demo only)
            session.run("MATCH (n) DETACH DELETE n")

            for node in graph_data.get("nodes", []):
                session.run(
                    "MERGE (n:Entity {id:$id}) "
                    "SET n.label=$label, n.name=$name",
                    node
                )

            for edge in graph_data.get("edges", []):
                session.run(
                    "MATCH (a:Entity {id:$source}), (b:Entity {id:$target}) "
                    "MERGE (a)-[r:REL {type:$relation}]->(b)",
                    edge
                )

        print("✅ Graph data successfully inserted into Neo4j AuraDB.")

    except Exception as e:
        print(f"❌ Neo4j connection or query error: {e}")

    finally:
        if driver:
            driver.close()

    return json.dumps(graph_data, indent=2)
