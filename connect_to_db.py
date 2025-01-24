from neo4j import GraphDatabase, RoutingControl

#capire se con la versione free di AURADB possiamo condividere un'istanza
#qui andranno i dati d'accesso, per ora sono collegati alla mia istanza
URI = "neo4j+s://4a9cf144.databases.neo4j.io"
AUTH = ("neo4j", "Z1yj8uqtOlzCnS7UKPcu7kafYA4g2u_pYz5oUulUkmw")
#l'oggetto che permette l'esecuzione di query neo4j è driver
#funzione che permette la creazione e l'inserimento di un'entità nel database remoto
def add_friend(driver, name, friend_name):
    driver.execute_query(
        "MERGE (a:Person {name: $name}) "
        "MERGE (friend:Person {name: $friend_name}) "
        "MERGE (a)-[:KNOWS]->(friend)",
        name=name, friend_name=friend_name, database_="neo4j",
    )


def print_friends(driver, name):
    records, _, _ = driver.execute_query(
        "MATCH (a:Person)-[:KNOWS]->(friend) WHERE a.name = $name "
        "RETURN friend.name ORDER BY friend.name",
        name=name, database_="neo4j", routing_=RoutingControl.READ,
    )
    for record in records:
        print(record["friend.name"])


with GraphDatabase.driver(URI, auth=AUTH) as driver:
    add_friend(driver, "Arthur", "Guinevere")
    add_friend(driver, "Arthur", "Lancelot")
    add_friend(driver, "Arthur", "Merlin")
    add_friend(driver,"Riccardo", "Cambianica")
    print_friends(driver, "Arthur")