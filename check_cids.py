import sqlite3
import requests
from config import Config

# Get the database file path from our central config.
DB_FILE = Config.DATABASE_URL

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

    print(f"Verifying {len(cids_to_check)} CIDs...")

    for recurso in cids_to_check:
        cid = recurso['cid']
        filename = recurso['filename']
        url = f"https://{cid}.ipfs.w3s.link/{filename}"

        try:
            # We use a HEAD request because it's faster, we only want the status
            response = requests.head(url, timeout=10)
            if response.status_code != 200:
                print(f"[FAILED] CID: {cid} | Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] CID: {cid} | Could not connect: {e}")

if __name__ == '__main__':
    check_all_cids()