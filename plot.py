import matplotlib.pyplot as plt
import numpy as np

# Nomi delle query
queries = ["Query A", "Query B", "Query C", "Query D", "Query D_2", "Query E"]

# Dati delle performance (in secondi) per diverse dimensioni del dataset
sizes = ["50MB", "100MB", "200MB"]
performance = {
    "50MB": [47.93, 5.12, 12.32, 6.73, 66.71, 0.83],
    "100MB": [206.24, 8.23, 42.17, 12.67, 237.12, 1.29],
    "200MB": [789.17, 12.49, 150.42, 25.21, 611.12, 2.94]
}

# Creazione del grafico a barre per ogni dimensione del dataset
x = np.arange(len(queries))  # Indici per le query
width = 0.25  # Larghezza delle barre

fig, ax = plt.subplots(figsize=(10, 6))

# Aggiungi le barre per ogni dimensione del dataset
for i, size in enumerate(sizes):
    if None not in performance[size]:  # Controlla se ci sono valori mancanti
        ax.bar(x + i * width, performance[size], width, label=size)

# Etichette e titoli
ax.set_xlabel("Queries")
ax.set_ylabel("Execution time (s)")
ax.set_title("Queries performance")

# Modifica degli intervalli per l'ascissa (y-axis)
ax.set_xticks(x + width)
ax.set_xticklabels(queries)

# Imposta intervalli sull'asse y per una visualizzazione migliore
ax.set_yticks(np.arange(0, 800, 50))  # Cambia l'intervallo a seconda della grandezza dei tuoi dati
ax.set_ylim(0, 800)  # Imposta un limite superiore all'asse y per visualizzare meglio

# Aggiungi la legenda
ax.legend(title="Dataset Size")

# Mostra il grafico
plt.savefig("performance_plot_adjusted.png", dpi=300)  # Salva l'immagine con alta qualità
plt.show()
