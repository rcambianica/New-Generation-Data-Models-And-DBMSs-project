import csv
import logging
import time
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "provaprova")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def query_a():
    # explanation of the query in the report
    query = """
        MATCH (c1:Customer)-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term:Terminal)
        MATCH (c2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term)
        WHERE c1.id < c2.id
        WITH c1, c2, COUNT(DISTINCT term) AS shared_terminals, 
            avg(t1.amount) AS avg_spent_c1, avg(t2.amount) AS avg_spent_c2
        WHERE shared_terminals >= 3
        AND ABS(avg_spent_c1 - avg_spent_c2) / avg_spent_c1 < 0.1
        RETURN c1.id, avg_spent_c1, c2.id, avg_spent_c2, shared_terminals
        ORDER BY c1.id
    """
    start_time = time.time()

    try:
        logging.info("Processing query A")
        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

        logging.info(f"Query A executed successfully")
        file_path = "query_results/A.csv"

        # writing query results in a .csv file
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Customer_c1",
                    "Avg_spent_c1",
                    "Customer_c2",
                    "Avg_spent_c2",
                    "Shared_terminals",
                ]
            )

            for row in data:
                writer.writerow(
                    [
                        row["c1.id"],
                        f"{row['avg_spent_c1']:.2f}",
                        row["c2.id"],
                        f"{row['avg_spent_c2']:.2f}",
                        row["shared_terminals"],
                    ]
                )

        logging.info("Results written to A.csv")

    except Exception as e:
        logging.error(f'Error "{e}" while processing query A')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query A: {execution_time:.2f} s")
    driver.close()


def query_b():
    # explanation of the query in the report
    query = """
        MATCH (t:Transaction)-[:OCCURS_AT]->(term:Terminal)
        WHERE ((t.datetime.year = date().year AND t.datetime.month = date().month - 1)
        OR (date().month = 1 AND t.datetime.month = 12 AND t.datetime.year = date().year -1))
        WITH term.id AS term_id, AVG(t.amount) AS prev_month_avg
        MATCH (t2:Transaction)-[:OCCURS_AT]->(term:Terminal)
        WHERE term.id = term_id AND (t2.datetime.year = date().year AND t2.datetime.month = date().month) AND t2.amount > 1.2*prev_month_avg
        SET t2.fraudulent = TRUE
    """

    start_time = time.time()

    try:
        logging.info("Processing query B")
        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

        logging.info(f"Query B executed successfully")

    except Exception as e:
        logging.error(f'Error "{e}" while processing query B')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query B: {execution_time:.2f} s")
    driver.close()


def query_c(customer_id=0, k=3):
    # explanation of the query in the report
    start_time = time.time()
    try:
        logging.info("Processing query C")
        co_customers = set()

        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            current_level_customers = {customer_id}

            for _ in range(k):
                query = """
                MATCH (u:Customer)-[:MAKES]->(t:Transaction)-[:OCCURS_AT]->(term:Terminal)
                    <-[:OCCURS_AT]-(t2:Transaction)<-[:MAKES]-(u2:Customer)
                WHERE u.id IN $current_customers AND u2.id <> u.id AND u2.id <> $u_id
                RETURN DISTINCT u2.id AS co_customer_id
                """
                result = session.run(
                    query,
                    u_id=customer_id,
                    current_customers=list(current_level_customers),
                )

                next_level_customers = {record["co_customer_id"] for record in result}
                next_level_customers -= co_customers

                if not next_level_customers:
                    break

                co_customers.update(next_level_customers)
                current_level_customers = next_level_customers

        file_path = "query_results/C.csv"

        # writing query results in a .csv file
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Customer_id", "Cocustomer_ids"])
            writer.writerow([customer_id, list(co_customers)[0]])
            for i in range(1, len(co_customers)):
                writer.writerow(["", list(co_customers)[i]])

        logging.info("Results written to C.csv")

    except Exception as e:
        logging.error(f'Error "{e}" while processing query C')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query C: {execution_time:.2f} s")
    driver.close()


def query_d():
    # explanation of the query in the report
    query = """
        MATCH (t:Transaction)
        WITH t, datetime(t.datetime).hour AS hour
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
        logging.info("Processing query D")
        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            session.run(query)
        logging.info(f"Query D executed successfully")
    except Exception as e:
        logging.error(f'Error "{e}" while processing query D')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query D: {execution_time:.2f} s")
    driver.close()


def query_d_2_batch(tx, data, batch_size=5000):
    # explanation of the query in the report
    query = """
        UNWIND $customers AS pair
        MATCH (c1:Customer {id: pair.c1_id})
        MATCH (c2:Customer {id: pair.c2_id})
        CREATE (c1)-[:BUYING_FRIEND_OF]->(c2)
    """

    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        customers = [{"c1_id": row["c1_id"], "c2_id": row["c2_id"]} for row in batch]
        try:
            logging.info(
                f"Creating buying friends relationship batch {i} to {i + batch_size}"
            )
            tx.run(query, customers=customers)
        except Exception as e:
            logging.error(
                f"Error while processing buying friends relationship batch {i}-{i + batch_size}: {e}"
            )


def query_d_2():
    # explanation of the query in the report
    query = """
        MATCH (c1:Customer)-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term:Terminal)
        MATCH (c2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term)
        WHERE c1.id < c2.id
        WITH c1, c2, COUNT(DISTINCT t1) AS num_transactions_c1,COUNT(DISTINCT t2) AS num_transactions_c2, 
            avg(t1.security_feeling) AS avg_security_feeling_c1, avg(t2.security_feeling) AS avg_security_feeling_c2 
        WHERE num_transactions_c1 > 3 AND num_transactions_c2 > 3
        AND ABS(avg_security_feeling_c1 - avg_security_feeling_c2) < 1
        RETURN c1.id as c1_id, c2.id as c2_id
    """
    start_time = time.time()

    try:
        logging.info("Processing query D 2")
        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

            data = list(data)
            session.execute_write(query_d_2_batch, data)

        logging.info(f"Time to create relationships: {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during relationships creation: {e}")


def query_e():
    # explanation of the query in the report
    query = """
        MATCH (t:Transaction)
        WITH t.period_of_day AS period, 
             COUNT(t) AS num_transactions_per_period,
             COUNT(CASE WHEN t.fraudulent = TRUE THEN 1 ELSE NULL END) AS num_fraud_transactions
        RETURN period, 
               num_transactions_per_period, 
               num_fraud_transactions, 
               num_fraud_transactions * 100.0 / num_transactions_per_period AS fraud_rate
    """

    start_time = time.time()

    try:
        logging.info("Processing query E")
        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

        logging.info("Query E executed successfully")

        # writing query results in a .csv file
        file_path = "query_results/E.csv"
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Period",
                    "Num_Transactions",
                    "Num_Fraud_Transactions",
                    "Fraud_Rate(%)",
                ]
            )

            for row in data:
                writer.writerow(
                    [
                        row["period"],
                        row["num_transactions_per_period"],
                        row["num_fraud_transactions"],
                        f"{row['fraud_rate']:.4f}",
                    ]
                )

        logging.info(f"Results written to {file_path}")

    except Exception as e:
        logging.error(f'Error "{e}" while processing query E')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query E: {execution_time:.2f} s")
    driver.close()
