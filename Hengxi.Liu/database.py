import os
from neo4j import GraphDatabase

# Connection settings are read from environment variables rather than hard-coded
# credentials. Defaults are local-only and do not include a password.
URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")


class Neo4jDatabase:
    def __init__(self, uri, username, password):
        if not password:
            raise RuntimeError(
                "NEO4J_PASSWORD is not set. Configure it as an environment variable."
            )
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password)
        )

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(
                query,
                parameters or {}
            )
            return [record.data() for record in result]


if __name__ == "__main__":
    db = Neo4jDatabase(URI, USERNAME, PASSWORD)
    try:
        result = db.execute_query(
            """
            RETURN 'MPM Knowledge Graph' AS System
            """
        )
        print("System:", result[0]["System"])
        print("Status: Connection successful")
    finally:
        db.close()
