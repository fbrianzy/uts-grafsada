import argparse
import os
import sys

import src.config as config
from src.db import get_driver, import_events, reset_db

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Impor dataset Retail Rocket ke database Neo4j."
    )
    parser.add_argument(
        "-u", "--user", default=config.USER, help="Username Neo4j (default: env atau neo4j)"
    )
    parser.add_argument(
        "-p", "--password", default=config.PASSWORD, help="Password Neo4j (default: env atau neo4j)"
    )
    parser.add_argument(
        "-b", "--bolt", default=config.URI, help=f"URI Bolt (default: {config.URI})"
    )
    parser.add_argument(
        "-s", "--source", default=str(config.DATA_DIR),
        help=f"Folder sumber data (default: {config.DATA_DIR})",
    )
    parser.add_argument(
        "-f", "--file", default=config.P1_CSV.name,
        help=f"Nama file csv di folder sumber (default: {config.P1_CSV.name})",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Kosongkan database sebelum impor"
    )
    parser.add_argument(
        "--max-rows", type=int, default=None, help="Batasi jumlah baris (untuk uji coba)"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    csv_path = os.path.join(args.source, args.file)
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' tidak ditemukan!")
        print("Jalankan prep.build_periods() dulu untuk membuat file periode.")
        sys.exit(1)

    try:
        driver = get_driver(args.bolt, args.user, args.password)
    except Exception as e:
        print(f"Gagal terhubung ke database: {e}")
        sys.exit(1)

    with driver:
        if args.reset:
            print("Mengosongkan database...")
            reset_db(driver)
        print(f"Membaca file data dari: {csv_path}")
        done = import_events(driver, csv_path, max_rows=args.max_rows)
    print(f"Proses impor berhasil, {done} baris masuk.")

if __name__ == "__main__":
    main()