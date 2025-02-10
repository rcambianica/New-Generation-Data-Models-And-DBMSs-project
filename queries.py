import csv
import logging
import time
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "provaprova")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def query_a():
    #con il dataset da 50MB ci mette tra i 2 e 3 minuti
    query = """
        MATCH (c1:Customer)-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term:Terminal),
              (c2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term)
        WHERE c1.customer_id <> c2.customer_id
        WITH c1, c2, COUNT(DISTINCT term) AS shared_terminals, 
            avg(t1.tx_amount) AS avg_spent_c1, avg(t2.tx_amount) AS avg_spent_c2
        WHERE shared_terminals >= 3
        AND ABS(avg_spent_c1 - avg_spent_c2) / avg_spent_c1 < 0.1
        RETURN c1.customer_id, avg_spent_c1, c2.customer_id, avg_spent_c2, shared_terminals
    """
    start_time = time.time()

    try:
        logging.info("Processing query A")
        with driver.session() as session:
            result = session.run(query)  
            data = result.data() 
        
        logging.info(f"Query A executed successfully")
        file_path = "A.csv"

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Customer1", "AvgSpent1", "Customer2", "AvgSpent2", "SharedTerminals"])

            for row in data:
                writer.writerow([row["c1.customer_id"], f"{row['avg_spent_c1']:.2f}", 
                                 row["c2.customer_id"], f"{row['avg_spent_c2']:.2f}", 
                                 row["shared_terminals"]])

        logging.info("Results written to A.csv")

    except Exception as e:
        logging.error(f"Error \"{e}\" while processing query A")

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query A: {execution_time:.2f} s")
    driver.close()

def query_d():
    query = """
        MATCH (t:Transaction)
        WITH t, datetime(t.tx_datetime).hour AS hour
        SET 
            t.period_of_day = CASE 
                WHEN hour >= 6 AND hour < 12 THEN 'morning'
                WHEN hour >= 12 AND hour < 18 THEN 'afternoon'
                WHEN hour >= 18 AND hour < 24 THEN 'evening'
                ELSE 'night'
            END,
            t.product_category = ['high-tech', 'food', 'clothing', 'consumable', 'other'][toInteger(rand() * 5)],
            t.security_feeling = toInteger(rand() * 5) + 1;
    """
    
    start_time = time.time()

    try:
        logging.info("Processing query d")
        with driver.session() as session:
            session.run(query) 
        logging.info(f"Query D executed successfully")
    except Exception as e:
        logging.error(f"Error \"{e}\" while processing query D") 

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query d: {execution_time:.2f} s")
    driver.close()