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
    query = """
        MATCH (c1:Customer)-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term:Terminal)
        MATCH (c2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term)
        WHERE c1.customer_id < c2.customer_id
        WITH c1, c2, COUNT(DISTINCT term) AS shared_terminals, 
            avg(t1.tx_amount) AS avg_spent_c1, avg(t2.tx_amount) AS avg_spent_c2
        WHERE shared_terminals >= 3
        AND avg_spent_c1 > 0
        AND ABS(avg_spent_c1 - avg_spent_c2) / avg_spent_c1 < 0.1
        RETURN c1.customer_id, avg_spent_c1, c2.customer_id, avg_spent_c2, shared_terminals
        ORDER BY c1.customer_id
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
                        row["c1.customer_id"],
                        f"{row['avg_spent_c1']:.2f}",
                        row["c2.customer_id"],
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
    query = """
        MATCH (t:Transaction)-[:OCCURS_AT]-(term:Terminal)
        WHERE (date().year = t.tx_datetime.year AND date().month - t.tx_datetime.month = 1)
        OR (date().month = 1 AND t.tx_datetime.month = 12 AND t.tx_datetime.year = date().year -1)
        WITH term.terminal_id AS term_id, avg(t.tx_amount) AS prev_month_avg
        MATCH (t2:Transaction)-[:OCCURS_AT]-(term{terminal_id:term_id})
        WHERE (t2.tx_datetime.year = date().year AND t2.tx_datetime.month = date().month) AND t2.tx_amount > 1.2*prev_month_avg
        WITH t2, term_id, prev_month_avg, t2.transaction_id as fraud_tx_id, t2.tx_amount as tx_amount
        SET t2.fraudolent = TRUE
    """
    start_time = time.time()

    try:
        logging.info("Processing query B")
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

        logging.info(f"Query B executed successfully")
    #     file_path = "B.csv"

    #     with open(file_path, mode="w", newline="") as file:
    #         writer = csv.writer(file)
    #         writer.writerow(
    #             [
    #                 "Terminal_id",
    #                 "Id_fradudolent_transaction",
    #                 "Fraudolent_transaction_amount",
    #                 "Avg_previous_month",
    #             ]
    #         )

    #         for row in data:
    #             writer.writerow(
    #                 [
    #                     row["term_id"],
    #                     row["fraud_tx_id"],
    #                     f"{row['tx_amount']:.2f}",
    #                     f"{row['prev_month_avg']:.2f}",
    #                 ]
    #             )

    #     logging.info("Results written to B.csv")

    except Exception as e:
        logging.error(f'Error "{e}" while processing query B')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query B: {execution_time:.2f} s")
    driver.close()


# def query_c():


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
        logging.error(f'Error "{e}" while processing query D')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query d: {execution_time:.2f} s")
    driver.close()


def query_d_2_batch(tx, data, batch_size=5000):

    query = """
        UNWIND $customers AS pair
        MATCH (c1:Customer {customer_id: pair.c1_id})
        MATCH (c2:Customer {customer_id: pair.c2_id})
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
    start_time = time.time()
    query = """
        MATCH (c1:Customer)-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term:Terminal),
              (c2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term)
        WHERE c1.customer_id < c2.customer_id
        WITH c1, c2, COUNT(DISTINCT t1) AS num_transactions_c1,COUNT(DISTINCT t2) AS num_transactions_c2, 
            avg(t1.security_feeling) AS avg_security_feeling_c1, avg(t2.security_feeling) AS avg_security_feeling_c2 
        WHERE num_transactions_c1 > 3 AND num_transactions_c2 > 3
        AND ABS(avg_security_feeling_c1 - avg_security_feeling_c2) < 1
        RETURN c1.customer_id as c1_id, c2.customer_id as c2_id
    """
    start_time = time.time()

    try:
        logging.info("Processing query D 2")
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

            data = list(data)
            session.execute_write(query_d_2_batch, data)

        logging.info(f"Time to create relationships: {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during relationships creation: {e}")


def query_e():
    query = """
        MATCH (t:Transaction)
        WITH t.period_of_day as period, COUNT(t) as num_transactions_per_period
        MATCH (tf:Transaction{fraudolent:TRUE})
        WHERE tf.period_of_day = period
        WITH period, num_transactions_per_period, COUNT(tf) as num_fraudolent_transactions_per_period
        RETURN period, num_transactions_per_period, num_fraudolent_transactions_per_period*1.0/num_transactions_per_period as average_number_of_fraud_transactions
    """
    start_time = time.time()

    try:
        logging.info("Processing query E")
        with driver.session() as session:
            result = session.run(query)
            data = result.data()

        logging.info(f"Query E executed successfully")
        file_path = "E.csv"

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Period",
                    "Num_transactions_per_period",
                    "Average_num_of_fraud_transactions",
                ]
            )

            for row in data:
                writer.writerow(
                    [
                        row["period"],
                        row["num_transactions_per_period"],
                        f"{row['average_number_of_fraud_transactions']:.2f}",
                    ]
                )

        logging.info("Results written to E.csv")

    except Exception as e:
        logging.error(f'Error "{e}" while processing query E')

    execution_time = time.time() - start_time
    logging.info(f"Execution time for query E: {execution_time:.2f} s")
    driver.close()
