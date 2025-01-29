import import_dataset, dataset_generator

if __name__ == '__main__':
    print("- GENERAZIONE DATASET -")
    print("1 - dataset da 50 Mbyte")
    print("2 - dataset da 100 Mbyte")
    print("3 - dataset da 200 Mbyte")
    print("Inserire la scelta: ")
    dataset_size = input()

    #generazione delle tre tabelle
    dataset_generator.generate_dataset(dataset_size)
    
    #carica i customers dal file .pkl e li carica su neo4j (per ora no)
    import_dataset.load_customers(dataset_size)
    #carica i terminals dal file .pkl e li carica su neo4j
    import_dataset.load_terminals(dataset_size)
    #carica le transactions dal file .pkl e li carica su neo4j (per ora no)
    import_dataset.load_transactions(dataset_size)