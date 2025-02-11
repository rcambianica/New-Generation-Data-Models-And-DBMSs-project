import logging
import time
import pickle
from neo4j import GraphDatabase
from concurrent.futures import ThreadPoolExecutor

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "provaprova")
driver = GraphDatabase.driver(URI, auth=AUTH)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# creates indexes (if not exists) for improving queries execution
def create_indexes():
    with driver.session() as session:
        session.run("CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.customer_id);")
        session.run("CREATE INDEX IF NOT EXISTS FOR (t:Terminal) ON (t.terminal_id);")
        session.run("CREATE INDEX IF NOT EXISTS FOR (tx:Transaction) ON (tx.transaction_id);")
    logging.info("Indexes created successfully.")

def insert_dataset(data):
    create_indexes() 
    insert_terminals(data)
    insert_customers(data)
    insert_transactions(data)

def load_customers_in_batch(tx, data, batch_size=1000):
    query = """
    UNWIND $customers AS customer
    MERGE (c:Customer {customer_id: customer.customer_id})
    ON CREATE SET 
        c.x_customer_id = customer.x_customer_id,
        c.y_customer_id = customer.y_customer_id,
        c.mean_amount = customer.mean_amount,
        c.std_amount = customer.std_amount,
        c.mean_nb_tx_per_day = customer.mean_nb_tx_per_day

    WITH c, customer.available_terminals AS terminals
    UNWIND terminals AS terminal_id

    MATCH (t:Terminal {terminal_id: terminal_id})
    CREATE (c)-[:CAN_USE]->(t);
    """
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        customers = [{
            'customer_id': row['CUSTOMER_ID'],
            'x_customer_id': row['x_customer_id'],
            'y_customer_id': row['y_customer_id'],
            'mean_amount': row['mean_amount'],
            'std_amount': row['std_amount'],
            'mean_nb_tx_per_day': row['mean_nb_tx_per_day'],
            'available_terminals': row['available_terminals']
        } for row in batch]
        
        try:
            logging.info(f"Processing customers batch {i} to {i + batch_size}")
            tx.run(query, customers=customers)
        except Exception as e:
            logging.error(f"Error while processing batch {i}-{i + batch_size}: {e}")

def insert_customers(data):
    start_time = time.time()
    try:
        with open(f'dataset/dataset {data}/customers.pkl', 'rb') as f:
            customers = pickle.load(f)
        customer_profiles_list = customers.to_dict(orient='records')
        
        with driver.session() as session:
            session.execute_write(load_customers_in_batch, customer_profiles_list)
        
        print(f"Time to import customers: {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during customer import: {e}")

def load_terminals_in_batch(tx, data, batch_size=1000):
    query = """
    UNWIND $terminals AS terminal
    MERGE (t:Terminal {terminal_id: terminal.terminal_id})
    ON CREATE SET
        t.x_terminal_id = terminal.x_terminal_id,
        t.y_terminal_id = terminal.y_terminal_id
    """
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        terminals = [{'terminal_id': row['TERMINAL_ID'], 'x_terminal_id': row['x_terminal_id'], 'y_terminal_id': row['y_terminal_id']} for row in batch]
        
        try:
            logging.info(f"Processing terminals batch {i} to {i + batch_size}")
            tx.run(query, terminals=terminals)
        except Exception as e:
            logging.error(f"Error while processing batch {i}-{i + batch_size}: {e}")

def insert_terminals(data):
    start_time = time.time()
    try:
        with open(f'dataset/dataset {data}/terminals.pkl', 'rb') as f:
            terminals = pickle.load(f)
        terminal_profiles_list = terminals.to_dict(orient='records')
        
        with driver.session() as session:
            session.execute_write(load_terminals_in_batch, terminal_profiles_list)
            
        logging.info(f"Time to import terminals: {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during terminal import: {e}")

def load_transactions_in_batch(tx, transactions):
    query = """
        UNWIND $transactions AS transaction
        CREATE (t:Transaction {
            transaction_id: transaction.transaction_id, 
            tx_datetime: transaction.tx_datetime,
            tx_amount: transaction.tx_amount,
            tx_time_seconds: transaction.tx_time_seconds,
            tx_time_days: transaction.tx_time_days
        })
        WITH t, transaction  
        MATCH (c:Customer {customer_id: transaction.customer_id})
        MATCH (term:Terminal {terminal_id: transaction.terminal_id})
        CREATE (c)-[:MAKES]->(t)
        CREATE (t)-[:OCCURS_AT]->(term)
    """
    try:
        tx.run(query, transactions=transactions)
    except Exception as e:
        logging.error(f"Error during batch insertion: {e}")

def insert_transactions(data, batch_size=5000):
    """Load transactions into Neo4j in batches"""
    start_time = time.time()

    try:
        with open(f'dataset/dataset {data}/transactions.pkl', 'rb') as f:
            transactions = pickle.load(f)

        transactions_list = transactions.to_dict(orient='records')
        
        with driver.session() as session:
            for i in range(0, len(transactions_list), batch_size):
                batch = transactions_list[i:i + batch_size]
                
                transactions_batch = [{
                    'transaction_id': row['TRANSACTION_ID'],
                    'tx_datetime': row['TX_DATETIME'],
                    'tx_amount': row['TX_AMOUNT'],
                    'tx_time_seconds': row['TX_TIME_SECONDS'],
                    'tx_time_days': row['TX_TIME_DAYS'],
                    'customer_id': row['CUSTOMER_ID'],
                    'terminal_id': row['TERMINAL_ID']
                } for row in batch]

                logging.info(f"Processing batch {i} - {i + batch_size}...")
                session.execute_write(load_transactions_in_batch, transactions_batch)

        logging.info(f"Time to import transactions: {time.time() - start_time:.2f} s")
    except Exception as e:
        logging.error(f"Error during transaction import: {e}")