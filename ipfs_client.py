import os, requests
WEB3_TOKEN = os.getenv("WEB3_STORAGE_TOKEN")

def upload_to_ipfs(file_bytes, filename):
    if not WEB3_TOKEN:
        raise RuntimeError("No hay token IPFS.")
    url = "https://api.web3.storage/upload"
    headers = {"Authorization": f"Bearer {WEB3_TOKEN}"}
    files = {"file": (filename, file_bytes)}
    r = requests.post(url, headers=headers, files=files, timeout=120)
    r.raise_for_status()
    data = r.json()
    cid = data.get("cid")
    gateway_url = f"https://{cid}.ipfs.w3s.link/{filename}" if cid else None
    return cid, gateway_url