import sqlite3
import requests

DB_FILE = "rea.db"

def check_all_cids():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cids_to_check = conn.execute("SELECT cid, filename FROM recursos WHERE cid IS NOT NULL").fetchall()
    conn.close()

    print(f"Verificando {len(cids_to_check)} CIDs...")

    for recurso in cids_to_check:
        cid = recurso['cid']
        filename = recurso['filename']
        url = f"https://{cid}.ipfs.w3s.link/{filename}"

        try:
            # Usamos un HEAD request porque es más rápido, solo queremos el estado
            response = requests.head(url, timeout=10)
            if response.status_code != 200:
                print(f"[FALLO] CID: {cid} | Estado: {response.status_code}")
            # else:
            #     print(f"[OK] CID: {cid}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] CID: {cid} | No se pudo conectar: {e}")

if __name__ == '__main__':
    check_all_cids()