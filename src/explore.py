import matplotlib.pyplot as plt
import networkx as nx

from src.db import run_df

Q_NODES = """
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS total
ORDER BY total DESC
"""

Q_RELS = """
MATCH ()-[r]->()
RETURN type(r) AS relation, count(r) AS total
ORDER BY total DESC
"""

Q_BEFORE = """
MATCH (v:Visitor)-[r:VIEWED|ADDED_TO_CART|BOUGHT]->(i:Item {itemId: $item})
RETURN v.visitorId AS source, type(r) AS rel, i.itemId AS target
LIMIT $limit
"""

Q_AFTER = """
MATCH (i:Item {itemId: $item})-[s:SIMILAR_TO]->(j:Item)
RETURN i.itemId AS source, type(s) AS rel, j.itemId AS target, s.score AS score
ORDER BY s.score DESC
"""

Q_COUNT_SIM = "MATCH ()-[s:SIMILAR_TO]->() RETURN count(s) AS total"

def node_composition(driver):
    return run_df(driver, Q_NODES)

def rel_composition(driver):
    return run_df(driver, Q_RELS)

def count_similar(driver):
    return int(run_df(driver, Q_COUNT_SIM)["total"].iloc[0])

def neighborhood_before(driver, item, limit=15):
    return run_df(driver, Q_BEFORE, item=int(item), limit=limit)

def neighborhood_after(driver, item, limit=15):
    # edge visitor ke item (dari state before) ditambah edge similar_to
    before = neighborhood_before(driver, item, limit)
    after = run_df(driver, Q_AFTER, item=int(item))
    return before, after

# networkx
def plot_edges(edges, title, item_center=None):
    g = nx.DiGraph()
    for r in edges.itertuples():
        src = f"{'V' if r.rel != 'SIMILAR_TO' else 'I'}:{r.source}"
        dst = f"I:{r.target}"
        g.add_edge(src, dst, rel=r.rel)

    colors = ["tab:blue" if n.startswith("V") else "tab:orange" for n in g.nodes]
    pos = nx.spring_layout(g, seed=7)
    plt.figure(figsize=(8, 6))
    nx.draw(g, pos, node_color=colors, node_size=450, font_size=7, with_labels=True,
            arrows=True)
    plt.title(title)
    plt.show()