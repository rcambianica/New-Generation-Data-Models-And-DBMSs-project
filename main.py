import datetime
import import_dataset, dataset_generator
if __name__ == '__main__':
    n_customers = 5000
    n_terminals = 200
    print("- GENERAZIONE DATASET -")
    print("1 - dataset da 50 Mbyte")
    print("2 - dataset da 100 Mbyte")
    print("3 - dataset da 200 Mbyte")
    print("Inserire la scelta: ")
    scelta = input()
    dataset_generator.generate_dataset(scelta, n_customers, n_terminals, nb_days=100, start_date=datetime.date.today(), r=5)
    #carica i customers dal file .pkl e li carica su neo4j
    import_dataset.load_customers('dataset/dataset ' +str(scelta)+'/customers.pkl')
    #carica i terminals dal file .pkl e li carica su neo4j
    import_dataset.load_terminals('dataset/dataset ' +str(scelta)+'/terminals.pkl')
    #carica le transactions dal file .pkl e li carica su neo4j
    import_dataset.load_transactions('dataset/dataset ' +str(scelta)+'/transactions.pkl')