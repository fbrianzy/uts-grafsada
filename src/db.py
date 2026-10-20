import pandas as pd
from neo4j import GraphDatabase, RoutingControl

import src.config as config

def get_driver(uri=config.URI, user=config.USER, password=config.PASSWORD):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver

def run_read(driver, query, **params):
    records, _, _ = driver.execute_query(
        query,
        parameters_=params,
        database_=config.DB,
        routing_=RoutingControl.READ,
    )
    return [r.data() for r in records]

def run_df(driver, query, **params):
    return pd.DataFrame(run_read(driver, query, **params))

def run_write(driver, query, **params):
    driver.execute_query(query, parameters_=params, database_=config.DB)

def create_constraints(session):
    session.run(
        "CREATE CONSTRAINT visitor_id IF NOT EXISTS "
        "FOR (v:Visitor) REQUIRE v.visitorId IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT item_id IF NOT EXISTS "
        "FOR (i:Item) REQUIRE i.itemId IS UNIQUE"
    )

def reset_db(driver):
    # hapus per 1rb baris, auto-commit jadi pakai session.run
    with driver.session(database=config.DB) as session:
        session.run(
            "CALL () { MATCH (n) DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS"
        ).consume()

IMPORT_QUERY = """
UNWIND $batch AS row
MERGE (v:Visitor {visitorId: row.visitorid})
MERGE (i:Item {itemId: row.itemid})
FOREACH (_ IN CASE WHEN row.event = 'view' THEN [1] ELSE [] END |
    CREATE (v)-[:VIEWED {timestamp: row.timestamp}]->(i))
FOREACH (_ IN CASE WHEN row.event = 'addtocart' THEN [1] ELSE [] END |
    CREATE (v)-[:ADDED_TO_CART {timestamp: row.timestamp}]->(i))
FOREACH (_ IN CASE WHEN row.event = 'transaction' THEN [1] ELSE [] END |
    CREATE (v)-[:BOUGHT {timestamp: row.timestamp,
                         transactionId: row.transactionid}]->(i))
"""

def import_batch(tx, batch):
    tx.run(IMPORT_QUERY, batch=batch)

def clean_chunk(chunk):
    # transactionid float (ada NaN) jadi string integer, kosong kalau bukan transaksi
    tid = chunk["transactionid"].astype("Int64").astype(str)
    chunk["transactionid"] = tid.where(chunk["transactionid"].notna(), "")
    return chunk

def import_events(driver, csv_path, batch_size=config.BATCH_SIZE, max_rows=None):
    from tqdm import tqdm

    with open(csv_path, "rb") as f:
        total_rows = sum(1 for _ in f) - 1
    if max_rows:
        total_rows = min(total_rows, max_rows)
    total_chunks = (total_rows // batch_size) + 1

    done = 0
    with driver.session(database=config.DB) as session:
        create_constraints(session)
        chunks = pd.read_csv(csv_path, chunksize=batch_size)
        for chunk in tqdm(chunks, total=total_chunks, desc="impor batch"):
            if max_rows and done >= max_rows:
                break
            chunk = clean_chunk(chunk)
            session.execute_write(import_batch, chunk.to_dict(orient="records"))
            done += len(chunk)
    return done