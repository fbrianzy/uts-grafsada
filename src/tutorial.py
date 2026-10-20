from neo4j import GraphDatabase, RoutingControl

import src.config as config

def add_friend(driver, name, friend_name):
    driver.execute_query(
        "MERGE (a:Person {name: $name}) "
        "MERGE (friend:Person {name: $friend_name}) "
        "MERGE (a)-[:KNOWS]->(friend)",
        name=name, friend_name=friend_name, database_=config.DB,
    )

def print_friends(driver, name):
    records, _, _ = driver.execute_query(
        "MATCH (a:Person)-[:KNOWS]->(friend) WHERE a.name = $name "
        "RETURN friend.name ORDER BY friend.name",
        name=name, database_=config.DB, routing_=RoutingControl.READ,
    )
    for record in records:
        print(record["friend.name"])

def clear_demo(driver):
    # hapus node tutorial saja, graf retail rocket tidak ikut
    driver.execute_query("MATCH (p:Person) DETACH DELETE p", database_=config.DB)

if __name__ == "__main__":
    with GraphDatabase.driver(config.URI, auth=(config.USER, config.PASSWORD)) as driver:
        add_friend(driver, "Arthur", "Guinevere")
        add_friend(driver, "Arthur", "Lancelot")
        add_friend(driver, "Arthur", "Merlin")
        print_friends(driver, "Arthur")