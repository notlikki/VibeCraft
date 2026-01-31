import sys
import os
import json
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

def verify_pdf(pdf_path: str, public_key_path: str = "keys/public_key.pem"):
    report = {
        "file": pdf_path,
        "status": "UNKNOWN",
        "failure_type": None
    }

    # 1. Load Public Key
    try:
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
    except Exception as e:
        report["status"] = "ERROR"
        report["failure_type"] = f"Key Load Failed: {e}"
        return report

    # 2. Multi-Provenance Discovery
    provenance_dir = "provenance"
    
    try:
        if not os.path.exists(provenance_dir):
            os.makedirs(provenance_dir)
            
        hash_files = [f for f in os.listdir(provenance_dir) if f.startswith("hashes_") and f.endswith(".json")]
            
    except Exception as e:
        report["status"] = "ERROR"
        report["failure_type"] = f"Provenance Scan Failed: {e}"
        return report

    if not hash_files:
        report["status"] = "FAILED"
        report["failure_type"] = "NO_PROVENANCE_FOUND"
        return report

    # 3. Hash PDF
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
            target_hash = hashlib.sha256(content).hexdigest()
    except Exception as e:
        report["status"] = "ERROR"
        report["failure_type"] = f"File Read Failed: {e}"
        return report
    
    # 4. Find Match
    match_found = False
    
    for hash_file in hash_files:
        candidate_uuid = hash_file.replace("hashes_", "").replace(".json", "")
        sig_file = f"sig_{candidate_uuid}.bin"
            
        json_path = os.path.join(provenance_dir, hash_file)
        sig_path = os.path.join(provenance_dir, sig_file)
        
        if not os.path.exists(sig_path):
            continue

        try:
            # Load Data
            with open(json_path, "r") as f:
                prov_json_str = f.read()
                prov_data = json.loads(prov_json_str)

            # Skip if not a PDF record (optional check, but good for safety)
            if prov_data.get("type") != "pdf":
                continue

            # Check Hash Match First (Efficiency)
            if prov_data.get("hash") != target_hash:
                continue

            # Verify Signature
            with open(sig_path, "rb") as f:
                signature = f.read()
                
            data_to_verify = json.dumps(prov_data, sort_keys=True).encode()
            public_key.verify(signature, data_to_verify, ec.ECDSA(hashes.SHA256()))
            
            # If we get here, it's a valid match
            match_found = True
            report["status"] = "VERIFIED"
            report["signed_by"] = "ECDSA"
            break
        
        except InvalidSignature:
            continue
        except Exception:
            continue

    if not match_found:
        report["status"] = "TAMPERED" 
        report["failure_type"] = "HASH_MISMATCH_OR_NO_RECORD"

    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pdf_verify.py <file.pdf>")
        sys.exit(1)
    print(json.dumps(verify_pdf(sys.argv[1]), indent=2))
