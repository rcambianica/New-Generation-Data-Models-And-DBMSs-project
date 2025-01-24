# New-Generation-Data-Models-And-DBMSs-project
## Collegamento ad istanza database creata su AURADB:
    - installare python \n
    - installare gestore pacchetti python pip "python3 -m ensurepip --upgrade" dovrebbe funzionare per mac \n
    - digitare su terminale "pip install neo4j" \n
    - connessione al database: \n
        Connect to a database by creating a Driver object and providing a URL and an authentication token. Once you have a Driver instance, use the .verify_connectivity() method to ensure that a working connection can be established.
        from neo4j import GraphDatabase

        # URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
        URI = "neo4j+s://83cd8efc.databases.neo4j.io"
        AUTH = ("<Username>", "<Password>")

        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()

## Documentazione Neo4j Python Driver: https://neo4j.com/docs/api/python-driver/current/

## Esecuzione script python in ambiente virtuale:
    - creare ambiente virtuale "python -m venv sandbox" \n
    - attivare ambiente virtuale "source sandbox/bi/activate" \n
    - eseguire script \n
    - disattivare ambiente virtuale "deactivate" \n

## Importare un dataset con script python: https://www.youtube.com/watch?v=yluHRteVBNI https://www.youtube.com/watch?v=z4KqiHfvhiw