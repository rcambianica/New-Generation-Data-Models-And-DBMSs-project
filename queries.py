import logging
import time
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "provaprova")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info(f"Query d executed successfully")
    except Exception as e:
        logging.error(f"Error \"{e}\" while processing query d") 

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query d: {execution_time:.2f} s")

driver.close()
