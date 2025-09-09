import requests
from flask import current_app

def upload_to_ipfs(file_bytes, filename):
    """
    Uploads a file to IPFS using the Web3.Storage API.
    It retrieves the API token from the current Flask app configuration.

    Args:
        file_bytes (bytes): The file content in bytes.
        filename (str): The name of the file.

    Returns:
        tuple: A tuple containing the CID and the gateway URL of the uploaded file.
    """
    # Get the token from the centralized app configuration.
    token = current_app.config.get('WEB3_STORAGE_TOKEN')
    
    if not token:
        # Raise an error if the token is not configured in the app.
        raise RuntimeError("WEB3_STORAGE_TOKEN is not set in the application configuration.")
        
    url = "https://api.web3.storage/upload"
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (filename, file_bytes)}
    
    # Send the POST request to upload the file.
    r = requests.post(url, headers=headers, files=files, timeout=120)
    r.raise_for_status()
    
    # Get the CID and gateway URL from the response.
    data = r.json()
    cid = data.get("cid")
    gateway_url = f"https://{cid}.ipfs.w3s.link/{filename}" if cid else None
    
    return cid, gateway_url