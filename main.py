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
    import_dataset.insert_dataset(dataset_size)
    