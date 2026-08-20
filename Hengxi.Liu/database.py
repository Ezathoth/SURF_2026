from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "YOUR_NEO4J_PASSWORD"


class Neo4jDatabase:

    def __init__(self, uri, username, password):
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

    db = Neo4jDatabase(
        URI,
        USERNAME,
        PASSWORD
    )

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