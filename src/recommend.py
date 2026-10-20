from collections import defaultdict

import numpy as np
import pandas as pd

import src.config as config

def load_truth(p2_csv=config.P2_CSV):
    df = pd.read_csv(p2_csv, usecols=["visitorid", "event", "itemid"])
    df = df[df["event"].isin(["addtocart", "transaction"])]
    return df.groupby("visitorid")["itemid"].agg(set).to_dict()

def candidate_users(x, users, items, idx, sim, truth):
    # user ada di train, punya item bertetangga, dan punya ground truth yang bisa direkomendasikan
    item_set = set(items.tolist())
    has_neigh = (sim > 0).any(axis=1)
    out = []
    for r, u in enumerate(users):
        t = truth.get(u)
        if not t or not (t & item_set):
            continue
        cols = x.indices[x.indptr[r]:x.indptr[r + 1]]
        if has_neigh[cols].any():
            out.append(r)
    return out

def pick_user(cands, users, seed=config.SEED):
    rng = np.random.default_rng(seed)
    r = int(rng.choice(sorted(cands)))
    return r, users[r]

def recommend_knn(x, row, items, idx, sim, k=config.K, top_n=config.TOP_N, exclude_min_weight=2):
    start, end = x.indptr[row], x.indptr[row + 1]
    cols, w = x.indices[start:end], x.data[start:end]

    scores = defaultdict(float)
    for c, wt in zip(cols, w):
        for j, s in zip(idx[c][:k], sim[c][:k]):
            if s > 0:
                scores[int(j)] += float(wt) * float(s)

    seen = set(cols[w >= exclude_min_weight].tolist())
    ranked = sorted(
        ((j, sc) for j, sc in scores.items() if j not in seen),
        key=lambda t: (-t[1], t[0]),
    )[:top_n]
    return pd.DataFrame(
        [(int(items[j]), round(sc, 4)) for j, sc in ranked], columns=["item", "score"]
    )

def hit_at_k(rec, truth, k=config.TOP_N):
    return int(any(i in truth for i in rec[:k]))

def ndcg_at_k(rec, truth, k=config.TOP_N):
    dcg = sum(1 / np.log2(pos + 2) for pos, i in enumerate(rec[:k]) if i in truth)
    idcg = sum(1 / np.log2(pos + 2) for pos in range(min(len(truth), k)))
    return dcg / idcg if idcg > 0 else 0.0

def evaluate_many(x, users, items, idx, sim, truth, cands, n=200, seed=config.SEED):
    rng = np.random.default_rng(seed)
    pick = rng.choice(sorted(cands), size=min(n, len(cands)), replace=False)
    hits, ndcgs = [], []
    for r in pick:
        rec = recommend_knn(x, int(r), items, idx, sim)["item"].tolist()
        t = truth[users[r]]
        hits.append(hit_at_k(rec, t))
        ndcgs.append(ndcg_at_k(rec, t))
    return {"users": len(pick), "hit@5": float(np.mean(hits)), "ndcg@5": float(np.mean(ndcgs))}