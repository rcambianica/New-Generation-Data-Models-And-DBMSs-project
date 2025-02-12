import import_dataset, dataset_generator, queries

if __name__ == "__main__":
    print("- DATASET GENERATION -")
    print("1 - 50 Mbyte dataset")
    print("2 - 100 Mbyte dataset")
    print("3 - 200 Mbyte dataset")
    print("Choose one option: ")
    dataset_selection = input()

    # generates the three tables (terminals, customers and transactions) and saves in three .pkl files
    # dataset_generator.generate_dataset(dataset_selection)

    # imports the dataset into the database
    # import_dataset.insert_dataset(dataset_selection)

    # queries.query_a()
    # queries.query_b()
    # queries.query_c(customer_id=300, k=5)
    # queries.query_d()
    # queries.query_d_2()
    # queries.query_e()
