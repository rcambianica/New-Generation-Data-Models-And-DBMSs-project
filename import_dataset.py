import logging
import time
import pickle
from neo4j import GraphDatabase
from concurrent.futures import ThreadPoolExecutor

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "provaprova")
driver = GraphDatabase.driver(URI, auth=AUTH)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_indexes():
    with driver.session() as session:
        session.run("CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.id);")
        session.run("CREATE INDEX IF NOT EXISTS FOR (t:Terminal) ON (t.id);")
        session.run("CREATE INDEX IF NOT EXISTS FOR (tx:Transaction) ON (tx.id);")
    logging.info("Indexes created successfully.")


def insert_dataset(dataset_selection):
    create_indexes()
    insert_terminals(dataset_selection)
    insert_customers(dataset_selection)
    insert_transactions(dataset_selection)


def load_customers_in_batch(tx, data, batch_size=5000):
    query = """
    UNWIND $customers AS customer
    MERGE (c:Customer {id: customer.customer_id})
    ON CREATE SET 
        c.x = customer.x_customer_id,
        c.y = customer.y_customer_id,
        c.spending_amount = customer.spending_amount,
        c.spending_frequency = customer.spending_frequency
    WITH c, customer.available_terminals AS terminals
    UNWIND terminals AS terminal_id
    MATCH (t:Terminal {id: terminal_id}) 
    CREATE (c)-[:CAN_USE]->(t);
    """

    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        customers = [
            {
                "customer_id": row["CUSTOMER_ID"],
                "x_customer_id": row["x_customer_id"],
                "y_customer_id": row["y_customer_id"],
                "spending_amount": row["mean_amount"],
                "spending_frequency": row["mean_nb_tx_per_day"],
                "available_terminals": row["available_terminals"],
            }
            for row in batch
        ]
        try:
            logging.info(f"Processing customers batch {i} to {i + batch_size}")
            tx.run(query, customers=customers)
        except Exception as e:
            logging.error(f"Error in batch {i}-{i + batch_size}: {e}")


def insert_customers(dataset_selection):
    start_time = time.time()
    try:
        with open(f"dataset/dataset {dataset_selection}/customers.pkl", "rb") as f:
            customers = pickle.load(f)
        customer_profiles_list = customers.to_dict(orient="records")

        with driver.session() as session:
            session.execute_write(load_customers_in_batch, customer_profiles_list)

        logging.info(f"Customers imported in {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during customer import: {e}")


def load_terminals_in_batch(tx, data, batch_size=5000):
    query = """
    UNWIND $terminals AS terminal
    MERGE (t:Terminal {id: terminal.terminal_id})
    ON CREATE SET
        t.x = terminal.x_terminal_id,
        t.y = terminal.y_terminal_id
    """

    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        terminals = [
            {
                "terminal_id": row["TERMINAL_ID"],
                "x_terminal_id": row["x_terminal_id"],
                "y_terminal_id": row["y_terminal_id"],
            }
            for row in batch
        ]

        try:
            logging.info(f"Processing terminals batch {i} to {i + batch_size}")
            tx.run(query, terminals=terminals)
        except Exception as e:
            logging.error(f"Error in batch {i}-{i + batch_size}: {e}")


def insert_terminals(dataset_selection):
    start_time = time.time()
    try:
        with open(f"dataset/dataset {dataset_selection}/terminals.pkl", "rb") as f:
            terminals = pickle.load(f)
        terminal_profiles_list = terminals.to_dict(orient="records")

        with driver.session() as session:
            session.execute_write(load_terminals_in_batch, terminal_profiles_list)

        logging.info(f"Terminals imported in {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during terminal import: {e}")


def load_transactions_in_batch(tx, transactions):
    query = """
    UNWIND $transactions AS transaction
    CREATE (t:Transaction {
        id: transaction.transaction_id, 
        datetime: datetime(transaction.tx_datetime),
        amount: transaction.tx_amount,
        time_seconds: transaction.tx_time_seconds,
        time_days: transaction.tx_time_days
    })
    WITH t, transaction  
    MATCH (c:Customer {id: transaction.customer_id})
    MATCH (term:Terminal {id: transaction.terminal_id})
    CREATE (c)-[:MAKES]->(t)
    CREATE (t)-[:OCCURS_AT]->(term);
    """

    try:
        tx.run(query, transactions=transactions)
    except Exception as e:
        logging.error(f"Error during batch insertion: {e}")


def insert_transactions(dataset_selection, batch_size=5000):
    start_time = time.time()
    try:
        with open(f"dataset/dataset {dataset_selection}/transactions.pkl", "rb") as f:
            transactions = pickle.load(f)
        transactions_list = transactions.to_dict(orient="records")

        with driver.session() as session:
            for i in range(0, len(transactions_list), batch_size):
                batch = transactions_list[i : i + batch_size]
                transactions_batch = [
                    {
                        "transaction_id": row["TRANSACTION_ID"],
                        "tx_datetime": row["TX_DATETIME"],
                        "tx_amount": row["TX_AMOUNT"],
                        "tx_time_seconds": row["TX_TIME_SECONDS"],
                        "tx_time_days": row["TX_TIME_DAYS"],
                        "customer_id": row["CUSTOMER_ID"],
                        "terminal_id": row["TERMINAL_ID"],
                    }
                    for row in batch
                ]

                logging.info(f"Processing transactions batch {i} - {i + batch_size}...")
                session.execute_write(load_transactions_in_batch, transactions_batch)

        logging.info(f"Transactions imported in {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during transaction import: {e}")
    driver.close()
