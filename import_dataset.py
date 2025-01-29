import time
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
    start_time=time.time()
    with open('dataset/dataset ' +str(file)+'/customers.pkl','rb') as f:
        customers = pickle.load(f)
    print(customers)
    print("Time to import the customers: {0:.2}s".format(time.time()-start_time))

def load_terminals(file):
    start_time=time.time()
    with open('dataset/dataset ' +str(file)+'/terminals.pkl','rb') as f:
        terminals = pickle.load(f)
    print(terminals)
    #leggo gli attributi separatamente, altrimenti pickle converte i tipi automaticamente
    terminal_ids = terminals['TERMINAL_ID'].tolist()
    x_terminal_ids = terminals['x_terminal_id'].tolist()
    y_terminal_ids = terminals['y_terminal_id'].tolist()
    transaction_execution_commands = []

    for i in range(len(terminal_ids)):
        neo4j_create_statemenet = "create (t:Terminal {terminal_id:" + str(terminal_ids[i]) +", x_terminal_id:  " + str(x_terminal_ids[i]) +", y_terminal_id: " + str(y_terminal_ids[i]) + "})"
        transaction_execution_commands.append(neo4j_create_statemenet)
            
    execute_transactions(transaction_execution_commands)

    print("Time to import the terminals: {0:.2}s".format(time.time()-start_time))
def load_transactions(file):
    start_time=time.time()
    with open('dataset/dataset ' +str(file)+'/transactions.pkl','rb') as f:
        transactions = pickle.load(f)
    print(transactions)
    print("Time to import the transactions: {0:.2}s".format(time.time()-start_time))
