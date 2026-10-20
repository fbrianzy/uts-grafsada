import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize

import src.config as config
from src.db import run_df

Q_INTERACTIONS = """
MATCH (v:Visitor)-[r:VIEWED|ADDED_TO_CART|BOUGHT]->(i:Item)
RETURN v.visitorId AS visitor, i.itemId AS item,
       sum(CASE type(r)
             WHEN 'VIEWED' THEN $w_view
             WHEN 'ADDED_TO_CART' THEN $w_cart
             ELSE $w_buy END) AS weight
"""

def fetch_interactions(driver):
    w = config.WEIGHTS
    return run_df(
        driver, Q_INTERACTIONS,
        w_view=w["view"], w_cart=w["addtocart"], w_buy=w["transaction"],
    )

def build_matrix(df):
    # baris user, kolom item. vektor user = baris, vektor item = kolom
    u = pd.Categorical(df["visitor"])
    i = pd.Categorical(df["item"])
    x = csr_matrix(
        (df["weight"].to_numpy(dtype=np.float32), (u.codes, i.codes)),
        shape=(len(u.categories), len(i.categories)),
    )
    return x, u.categories.to_numpy(), i.categories.to_numpy()

def describe(x, label):
    r, c = x.shape
    size = (x.data.nbytes + x.indices.nbytes + x.indptr.nbytes) / 1e6
    per_row = np.diff(x.indptr)
    return {
        "vsm": label,
        "shape": f"{r} x {c}",
        "dimensi": c,
        "nnz": x.nnz,
        "sparsity_%": round(100 * (1 - x.nnz / (r * c)), 4),
        "ukuran_mb": round(size, 2),
        "rata_nnz_per_vektor": round(per_row.mean(), 2),
        "maks_nnz_per_vektor": int(per_row.max()),
    }

def describe_both(x):
    return pd.DataFrame([describe(x, "user (baris)"), describe(x.T.tocsr(), "item (kolom)")])

def projection_cost(x):
    # batas atas edge proyeksi: tiap pasangan yang berbagi satu tetangga
    b = x.copy()
    b.data[:] = 1
    user_deg = np.asarray(b.sum(axis=1)).ravel()
    item_deg = np.asarray(b.sum(axis=0)).ravel()
    n_u, n_i = x.shape
    rows = []
    for name, n, pairs in [
        ("user-user", n_u, (item_deg * (item_deg - 1) / 2).sum()),
        ("item-item", n_i, (user_deg * (user_deg - 1) / 2).sum()),
    ]:
        rows.append({
            "proyeksi": name,
            "jumlah_simpul": n,
            "ukuran_matriks_penuh": f"{n} x {n}",
            "memori_penuh_gb_float32": round(n * n * 4 / 1e9, 2),
            "batas_atas_edge": int(pairs),
        })
    return pd.DataFrame(rows)

def plot_sample(x, ids, axis, n=25, threshold=0.15, seed=config.SEED, pool=300):
    # ambil sampel acak dari simpul paling aktif, hubungkan kalau cosine >= threshold
    m = x if axis == "user" else x.T.tocsr()
    deg = np.diff(m.indptr)
    top = np.argsort(-deg)[:pool]
    rng = np.random.default_rng(seed)
    pick = rng.choice(top, size=min(n, len(top)), replace=False)

    sub = normalize(m[pick])
    sim = (sub @ sub.T).toarray()
    g = nx.Graph()
    prefix = "U" if axis == "user" else "I"
    g.add_nodes_from(f"{prefix}:{ids[p]}" for p in pick)
    for a in range(len(pick)):
        for b in range(a + 1, len(pick)):
            if sim[a, b] >= threshold:
                g.add_edge(f"{prefix}:{ids[pick[a]]}", f"{prefix}:{ids[pick[b]]}",
                           weight=sim[a, b])

    plt.figure(figsize=(8, 6))
    nx.draw(g, nx.spring_layout(g, seed=7), node_size=300, font_size=6,
            with_labels=True, node_color="tab:blue" if axis == "user" else "tab:orange")
    plt.title(f"proyeksi {axis}-{axis}, {g.number_of_nodes()} simpul, "
              f"{g.number_of_edges()} edge (cosine >= {threshold})")
    plt.show()
    return g