import argparse
import math
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

load_dotenv()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Impor dataset RetailRocket (events.csv) ke database Neo4J."
    )
    parser.add_argument(
        "-u", "--user", default=os.getenv("USN", "neo4j"), help="Username Neo4j (default: USN di .env)"
    )
    parser.add_argument(
        "-p",
        "--password",
        default=os.getenv("PASSWD", "neo4j"),
        help="Password Neo4J (default: PASSWD di .env)",
    )
    parser.add_argument(
        "-b",
        "--bolt",
        default=os.getenv("URI", "neo4j://127.0.0.1:7687"),
        help="Neo4J URI / Bolt (default: neo4j://127.0.0.1:7687)",
    )
    parser.add_argument(
        "-s",
        "--source",
        default="data",
        help="Direktori/folder sumber data (default: data)",
    )
    parser.add_argument(
        "-f", "--file", default="events.csv", help="Nama berkas CSV (default: events.csv)"
    )
    parser.add_argument(
        "-d",
        "--database",
        default=os.getenv("DBNAME", "neo4j"),
        help="Database tujuan (default: DBNAME di .env)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=10_000, help="Baris per transaksi (default: 10000)"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Kosongkan database tujuan sebelum impor"
    )
    return parser.parse_args()


def create_constraints(session):
    session.run(
        "CREATE CONSTRAINT visitor_id IF NOT EXISTS "
        "FOR (v:Visitor) REQUIRE v.visitorId IS UNIQUE"
    ).consume()
    session.run(
        "CREATE CONSTRAINT item_id IF NOT EXISTS "
        "FOR (i:Item) REQUIRE i.itemId IS UNIQUE"
    ).consume()


def reset_database(session):
    # auto-commit transaction: dihapus per 10.000 simpul agar heap tidak penuh
    session.run(
        "MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS"
    ).consume()


def import_batch(tx, batch):
    cypher_query = """
    UNWIND $batch AS row
    MERGE (v:Visitor {visitorId: row.visitorid})
    MERGE (i:Item {itemId: row.itemid})

    WITH v, i, row
    CALL (v, i, row) {
        WITH v, i, row WHERE row.event = 'view'
        CREATE (v)-[:VIEWED {timestamp: row.timestamp, fold: row.fold}]->(i)

        UNION ALL

        WITH v, i, row WHERE row.event = 'addtocart'
        CREATE (v)-[:ADDED_TO_CART {timestamp: row.timestamp, fold: row.fold}]->(i)

        UNION ALL

        WITH v, i, row WHERE row.event = 'transaction'
        CREATE (v)-[:BOUGHT {timestamp: row.timestamp, fold: row.fold,
                             transactionId: row.transactionid}]->(i)
    }
    """
    tx.run(cypher_query, batch=batch)


def main():
    args = parse_arguments()

    csv_file_path = os.path.join(args.source, args.file)

    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' tidak ditemukan!")
        sys.exit(1)

    try:
        driver = GraphDatabase.driver(
            args.bolt, auth=(args.user, args.password)
        )
        driver.verify_connectivity()
    except Exception as e:
        print(f"Gagal terhubung ke database: {e}")
        sys.exit(1)

    batch_size = args.batch_size

    with driver.session(database=args.database) as session:
        if args.reset:
            print(f"Mengosongkan database '{args.database}'...")
            reset_database(session)
        create_constraints(session)

        print(f"Membaca file data dari: {csv_file_path}")
        chunks = pd.read_csv(
            csv_file_path, chunksize=batch_size, dtype={"transactionid": "string"}
        )

        with open(csv_file_path, encoding="utf-8") as f:
            total_rows = sum(1 for _ in f) - 1  # tanpa baris header
        total_chunks = math.ceil(total_rows / batch_size)

        print("Memulai proses impor data ke Neo4j...")
        for chunk in tqdm(
            chunks, total=total_chunks, desc="Mengimpor Batch Data"
        ):
            # Membersihkan data null/NaN pada transactionid
            chunk["transactionid"] = chunk["transactionid"].fillna("")

            records = chunk.to_dict(orient="records")
            session.execute_write(import_batch, records)

    driver.close()
    print(f"Proses impor berhasil: {total_rows:,} baris.")


if __name__ == "__main__":
    main()
