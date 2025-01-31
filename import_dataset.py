from datetime import datetime
import time
from neo4j import GraphDatabase
import pickle

URI = "bolt://44.192.121.100"
AUTH = ("neo4j", "parameter-earth-scratchpad")
driver = GraphDatabase.driver(URI, auth=AUTH)

def insert_dataset(data):
    insert_terminals(data)
    insert_customers(data)
    insert_transactions(data)

def load_customers_in_batch(tx, data, batch_size=1000):
    query = """
    UNWIND $customers AS customer
    CREATE (c:Customer {
        customer_id: customer.customer_id,
        x_customer_id: customer.x_customer_id,
        y_customer_id: customer.y_customer_id,
        mean_amount: customer.mean_amount,
        std_amount: customer.std_amount,
        mean_nb_tx_per_day: customer.mean_nb_tx_per_day
    })
    WITH c, customer.available_terminals AS terminals
    UNWIND terminals AS terminal_id
    MATCH (t:Terminal {terminal_id: terminal_id})
    MERGE (c)-[:CAN_USE]->(t);
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
        
        print(f"Processing batch {i} to {i+batch_size}")  #monitoraggio batch di terminali
        tx.run(query, customers=customers)
        
def insert_customers(data):
    start_time = time.time()
    try:
        # Carica il file pickle con i dati
        with open(f'dataset/dataset {data}/customers.pkl', 'rb') as f:
            customers = pickle.load(f)

        with driver.session() as session:
            session.execute_write(load_customers_in_batch, customers)
            
        
        print(f"Tempo per importare i customers: {time.time() - start_time:.2f} s")
    except Exception as e:
        print(f"Errore: {e}")

def load_terminals_in_batch(tx, data, batch_size=1000):
    query = """
    UNWIND $terminals AS terminal
    CREATE (t:Terminal {terminal_id: terminal.terminal_id, x_terminal_id: terminal.x_terminal_id, y_terminal_id: terminal.y_terminal_id})
    """
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        terminals = [{'terminal_id': row['TERMINAL_ID'], 'x_terminal_id': row['x_terminal_id'], 'y_terminal_id': row['y_terminal_id']} for row in batch]
        print(f"Processing terminals batch {i} to {i + batch_size}")  # Monitoraggio batch di terminali
        tx.run(query, terminals=terminals)

def insert_terminals(data):
    start_time = time.time()
    try:
        with open(f'dataset/dataset {data}/terminals.pkl', 'rb') as f:
            terminals = pickle.load(f)

        with driver.session() as session:
            session.execute_write(load_terminals_in_batch, terminals)
            
        print(f"Tempo per importare i terminals: {time.time() - start_time:.2f} s")
    except Exception as e:
        print(f"Errore: {e}")

def load_transactions_in_batch(tx, data, batch_size=10000):
    query = """
    UNWIND $transactions AS transaction
    MERGE (t:Transaction {transaction_id: transaction.transaction_id, tx_datetime: transaction.tx_datetime, tx_amount: transaction.tx_amount, tx_time_seconds: transaction.tx_time_seconds, tx_time_days: transaction.tx_time_days})
    WITH t, transaction.customer_id AS customer_id, transaction.terminal_id AS terminal_id
    MATCH (c:Customer {customer_id: customer_id}), (term:Terminal {terminal_id: terminal_id})
    MERGE (c)-[:MADE]->(t)
    MERGE (t)-[:OCCURRED_AT]->(term)
    """

    # Elabora i dati in batch
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        transactions = [{
            'transaction_id': row['TRANSACTION_ID'],
            'tx_datetime': row['TX_DATETIME'],
            'tx_amount': row['TX_AMOUNT'],
            'tx_time_seconds': row['TX_TIME_SECONDS'],
            'tx_time_days': row['TX_TIME_DAYS'],
            'customer_id': row['CUSTOMER_ID'],
            'terminal_id': row['TERMINAL_ID']
        } for row in batch]

        # Debug: Verifica se i customer_id e terminal_id sono validi
        for transaction in transactions:
            print(f"Transaction {transaction['transaction_id']}: customer_id={transaction['customer_id']}, terminal_id={transaction['terminal_id']}")

        # Esegui la query per creare i nodi e le relazioni
        tx.run(query, transactions=transactions)


def insert_transactions(data):
    start_time = time.time()
    try:
        # Carica il file pickle con i dati
        with open(f'dataset/dataset {data}/transactions.pkl', 'rb') as f:
            transactions = pickle.load(f)

        with driver.session() as session:
            session.execute_write(load_transactions_in_batch, transactions)
        
        print(f"Tempo per importare le transactions: {time.time() - start_time:.2f} s")
    except Exception as e:
        print(f"Errore: {e}")