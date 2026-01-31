import sys
import os
import json
import hashlib
import uuid
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

def sign_pdf(pdf_path: str):
    # Ensure provenance directory exists
    os.makedirs("provenance", exist_ok=True)
    
    # Check if private key exists
    if not os.path.exists("keys/private_key.pem"):
        raise FileNotFoundError("Error: keys/private_key.pem not found. Run from project root or generate keys.")
    
    with open("keys/private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=None)

    # Load PDF Content
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
    except Exception as e:
        raise ValueError(f"Failed to load PDF: {e}")

    # Calculate Hash
    file_hash = hashlib.sha256(content).hexdigest()

    prov_id = uuid.uuid4().hex[:8]
    
    # Save Hash Map
    provenance_data = {
        "id": prov_id,
        "type": "pdf",
        "hash": file_hash
    }
    
    prov_filename = f"hashes_{prov_id}.json"
    prov_path = os.path.join("provenance", prov_filename)
    
    with open(prov_path, "w") as f:
        json.dump(provenance_data, f)

    # Sign the Provenance Data
    data_to_sign = json.dumps(provenance_data, sort_keys=True).encode()
    signature = private_key.sign(data_to_sign, ec.ECDSA(hashes.SHA256()))

    sig_filename = f"sig_{prov_id}.bin"
    sig_path = os.path.join("provenance", sig_filename)

    with open(sig_path, "wb") as f:
        f.write(signature)

    print(f"PDF signed. Provenance saved to {prov_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pdf_sign.py <file.pdf>")
        sys.exit(1)
    sign_pdf(sys.argv[1])
