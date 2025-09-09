import sqlite3
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Get the database file path from environment variables, with a default value
DB_FILE = os.getenv("DATABASE_URL", "rea.db")

def check_all_cids():
    """
    Checks the status of all CIDs stored in the database.
    It sends a HEAD request to the IPFS gateway to verify if the content is available.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Get all CIDs from the database
    cids_to_check = conn.execute("SELECT cid, filename FROM recursos WHERE cid IS NOT NULL").fetchall()
    conn.close()

    print(f"Verificando {len(cids_to_check)} CIDs...")

    for recurso in cids_to_check:
        cid = recurso['cid']
        filename = recurso['filename']
        url = f"https://{cid}.ipfs.w3s.link/{filename}"

        try:
            # We use a HEAD request because it's faster, we only want the status
            response = requests.head(url, timeout=10)
            if response.status_code != 200:
                print(f"[FALLO] CID: {cid} | Estado: {response.status_code}")
            # else:
            #     print(f"[OK] CID: {cid}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] CID: {cid} | No se pudo conectar: {e}")

if __name__ == '__main__':
    check_all_cids()