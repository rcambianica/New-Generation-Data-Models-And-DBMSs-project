import pandas as pd

# carica il file .pkl contenente il dataset, ora carica i rawdata presenti come esempio
# capire se è meglio usare libreria pickle o pandas
with open('/home/ric/Downloads/2018-09-30.pkl','rb') as f:
    dataset = pd.read_pickle(f)
print(dataset)