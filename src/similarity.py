import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize
from tqdm import tqdm

import src.config as config
from src.db import run_df, run_write

Q_WRITE = """
UNWIND $rows AS row
MATCH (a:Item {itemId: row.a})
MATCH (b:Item {itemId: row.b})
MERGE (a)-[s:SIMILAR_TO]->(b)
SET s.score = row.score
"""

Q_TOP = """
MATCH (i:Item {itemId: $item})-[s:SIMILAR_TO]->(j:Item)
RETURN j.itemId AS item, s.score AS score
ORDER BY s.score DESC
LIMIT 5
"""

def item_matrix(x, min_users=config.MIN_ITEM_USERS):
    # x user x item, hasil item x user. item yang jarang disentuh dinolkan
    xi = x.T.tocsr().copy()
    deg = np.diff(xi.indptr)
    xi = xi.multiply((deg >= min_users).astype(np.float32)[:, None]).tocsr()
    xi.eliminate_zeros()
    return xi

def topk_cosine(xi, k=config.NEIGH_K, chunk=256):
    xn = normalize(xi)
    xt = xn.T.tocsr()
    n = xn.shape[0]
    idx = np.zeros((n, k), dtype=np.int32)
    sim = np.zeros((n, k), dtype=np.float32)

    for a in tqdm(range(0, n, chunk), desc="cosine item-item"):
        b = min(a + chunk, n)
        s = (xn[a:b] @ xt).toarray().astype(np.float32)
        s[np.arange(b - a), np.arange(a, b)] = 0  # buang diri sendiri
        kk = min(k, n - 1)
        part = np.argpartition(-s, kk - 1, axis=1)[:, :kk]
        vals = np.take_along_axis(s, part, axis=1)
        order = np.argsort(-vals, axis=1)
        idx[a:b, :kk] = np.take_along_axis(part, order, axis=1)
        sim[a:b, :kk] = np.take_along_axis(vals, order, axis=1)
    return idx, sim

def top_for_item(item_id, items, idx, sim, n=5):
    pos = int(np.where(items == item_id)[0][0])
    rows = [(int(items[j]), float(s)) for j, s in zip(idx[pos][:n], sim[pos][:n]) if s > 0]
    return pd.DataFrame(rows, columns=["item", "score"])

def pick_reference_item(xi, items, seed=config.SEED, pool=200):
    # acak dari item yang paling banyak disentuh supaya punya tetangga
    deg = np.diff(xi.indptr)
    top = np.argsort(-deg)[:pool]
    rng = np.random.default_rng(seed)
    return int(items[rng.choice(top)])

def to_rows(items, idx, sim):
    rows = []
    for a in range(idx.shape[0]):
        for j, s in zip(idx[a], sim[a]):
            if s > 0:
                rows.append({"a": int(items[a]), "b": int(items[j]), "score": round(float(s), 6)})
    return rows

def write_similar(driver, items, idx, sim, batch=5000):
    rows = to_rows(items, idx, sim)
    for i in tqdm(range(0, len(rows), batch), desc="tulis SIMILAR_TO"):
        run_write(driver, Q_WRITE, rows=rows[i:i + batch])
    return len(rows)

def delete_similar(driver):
    with driver.session(database=config.DB) as session:
        session.run(
            "CALL { MATCH ()-[s:SIMILAR_TO]->() DELETE s } IN TRANSACTIONS OF 10000 ROWS"
        ).consume()

def top_from_graph(driver, item_id):
    return run_df(driver, Q_TOP, item=int(item_id))