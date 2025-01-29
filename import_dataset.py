from neo4j import GraphDatabase
import pickle

URI = "neo4j+s://4a9cf144.databases.neo4j.io"
AUTH = ("neo4j", "Z1yj8uqtOlzCnS7UKPcu7kafYA4g2u_pYz5oUulUkmw")

def execute_transactions(transaction_execution_commands):
    data_base_connection = GraphDatabase.driver(URI, auth=AUTH)
    session = data_base_connection.session()    
    for i in transaction_execution_commands:
        session.run(i)
    session.close()
    data_base_connection.close()

def load_customers(file):
    with open(file,'rb') as f:
        customers = pickle.load(f)
    print(customers)

def load_terminals(file):
    with open(file, 'rb') as f:
        terminals = pickle.load(f)
    #leggo gli attributi separatamente, altrimenti pickle converte i tipi automaticamente
    terminal_ids = terminals['TERMINAL_ID'].tolist()
    x_terminal_ids = terminals['x_terminal_id'].tolist()
    y_terminal_ids = terminals['y_terminal_id'].tolist()
    transaction_execution_commands = []

    for i in range(len(terminal_ids)):
        neo4j_create_statemenet = "create (t:Terminal {terminal_id:" + str(terminal_ids[i]) +", x_terminal_id:  " + str(x_terminal_ids[i]) +", y_terminal_id: " + str(y_terminal_ids[i]) + "})"
        transaction_execution_commands.append(neo4j_create_statemenet)
            
    execute_transactions(transaction_execution_commands)

def load_transactions(file):
    with open(file,'rb') as f:
        transactions = pickle.load(f)
    print(transactions)