import import_dataset, dataset_generator, queries

if __name__ == "__main__":
    print("- GENERAZIONE DATASET -")
    print("1 - dataset da 50 Mbyte")
    print("2 - dataset da 100 Mbyte")
    print("3 - dataset da 200 Mbyte")
    print("Inserire la scelta: ")
    #dataset_size = input()

    # generates the three tables (terminals, customers and transactions) and saves in three .pkl files
    #dataset_generator.generate_dataset(dataset_size)
    # imports the dataset into the database
    #import_dataset.insert_dataset(dataset_size)

    queries.query_a()
    # queries.query_b()
    # queries.query_c()
    # queries.query_d()
    # queries.query_d_2()
    # queries.query_e()
