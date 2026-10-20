import os
from pathlib import Path

# koneksi neo4j
URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")
DB = "neo4j"

# path data
DATA_DIR = Path("ecommerce-dataset")
EVENTS_CSV = DATA_DIR / "events.csv"
P1_CSV = DATA_DIR / "events_p1.csv"
P2_CSV = DATA_DIR / "events_p2.csv"

# dari excel: 25	23031554144	BAGUS FEBRIANSYAH PRATAMA	5/25/2015	7/25/2015		8/3/2015	8/18/2015
# periode dari excel
P1 = ("2015-05-25", "2015-07-25")  # train
P2 = ("2015-08-03", "2015-08-18")  # test

# bobot event untuk matriks user-item
WEIGHTS = {"view": 1, "addtocart": 2, "transaction": 3}

# import
BATCH_SIZE = 5000

# similarity dan rekomendasi
MIN_ITEM_USERS = 3  # item dengan visitor kurang dari ini tidak dihitung
NEIGH_K = 10  # tetangga per item yang disimpan
K = 5  # tetangga per item yang dipakai saat knn
TOP_N = 5  # panjang daftar rekomendasi
N_ADS = 3  # item yang diiklankan
SEED = 42