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
        AND avg_spent_c1 > 0
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


def query_c(id=0):
    start_time = time.time()
    try:
        logging.info("Processing query C")
        # execution of the query on the database through the usage of a driver session
        with driver.session() as session:
            # explanation of the query in the report
            # Trova i terminali usati dal cliente u
            query_1 = """
                MATCH (u:Customer {id: $customer_id})-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term1:Terminal)
                RETURN DISTINCT term1.id AS terminal_id
                """

            terminals_u = session.run(query_1, customer_id=id)
            terminal_ids = [record["terminal_id"] for record in terminals_u]

            # Trova i clienti che hanno usato i terminali di u
            query_2 = """
                    MATCH (u:Customer {id: $customer_id})-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term1:Terminal)<-[:OCCURS_AT]-(t2:Transaction)<-[:MAKES]-(u2:Customer)
                    WHERE term1.id IN $terminal_ids AND u.id <> u2.id
                    RETURN DISTINCT u2.id AS co_customer_id
                    """
            co_customers_u2 = session.run(
                query_2, customer_id=id, terminal_ids=terminal_ids
            )
            co_customers = [record["co_customer_id"] for record in co_customers_u2]

            # Trova ulteriori terminali e clienti collegati
            query_3 = """
                    MATCH (u2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term2:Terminal)<-[:OCCURS_AT]-(t3:Transaction)<-[:MAKES]-(u3:Customer)
                    WHERE u2.id IN $co_customers AND u2.id <> u3.id AND u3.id <> $customer_id
                    RETURN DISTINCT u3.id AS co_customer_id
                    """
            co_customers_u3 = session.run(
                query_3, co_customers=co_customers, customer_id=id
            )
            co_customers_final = [
                record["co_customer_id"] for record in co_customers_u3
            ]

            file_path = "query_results/C.csv"

            # writing query results in a .csv file
            with open(file_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Customer_id", "Cocustomer_id"])

                for coid in co_customers_final:
                    writer.writerow(
                        [
                            id,
                            coid,
                        ]
                    )

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
        MATCH (c1:Customer)-[:MAKES]->(t1:Transaction)-[:OCCURS_AT]->(term:Terminal),
              (c2:Customer)-[:MAKES]->(t2:Transaction)-[:OCCURS_AT]->(term)
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
