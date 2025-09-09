import os, requests

# Get the Web3.Storage token from environment variables
WEB3_TOKEN = os.getenv("WEB3_STORAGE_TOKEN")

def upload_to_ipfs(file_bytes, filename):
    """
    Uploads a file to IPFS using the Web3.Storage API.

    Args:
        file_bytes (bytes): The file content in bytes.
        filename (str): The name of the file.

    Returns:
        tuple: A tuple containing the CID and the gateway URL of the uploaded file.
    """
    if not WEB3_TOKEN:
        raise RuntimeError("No hay token IPFS.")
        
    url = "https://api.web3.storage/upload"
    headers = {"Authorization": f"Bearer {WEB3_TOKEN}"}
    files = {"file": (filename, file_bytes)}
    
    # Send the POST request to upload the file
    r = requests.post(url, headers=headers, files=files, timeout=120)
    r.raise_for_status()
    
    # Get the CID and gateway URL from the response
    data = r.json()
    cid = data.get("cid")
    gateway_url = f"https://{cid}.ipfs.w3s.link/{filename}" if cid else None
    
    return cid, gateway_url