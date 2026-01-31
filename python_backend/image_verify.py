import sys
import os
import json
import numpy as np
import imageio.v3 as iio
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from video_utils import content_hash

def verify_image(image_path: str, public_key_path: str = "keys/public_key.pem"):
    report = {
        "file": image_path,
        "status": "UNKNOWN",
        "failure_type": None,
        "mismatched_blocks": [],
        "tamper_map": None
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
    candidates = []
    
    # Find all hash files
    try:
        if not os.path.exists(provenance_dir):
            os.makedirs(provenance_dir)
            
        hash_files = [f for f in os.listdir(provenance_dir) if f.startswith("hashes_") and f.endswith(".json")]
        
        # Also include legacy/latest 'image_hashes.json' if it exists, for backward compatibility
        if os.path.exists(os.path.join(provenance_dir, "image_hashes.json")):
            hash_files.append("image_hashes.json")
            
    except Exception as e:
        report["status"] = "ERROR"
        report["failure_type"] = f"Provenance Scan Failed: {e}"
        return report

    if not hash_files:
        report["status"] = "FAILED"
        report["failure_type"] = "NO_PROVENANCE_FOUND"
        return report

    # 3. Load Image to verify
    try:
        image = iio.imread(image_path)
    except Exception:
        report["status"] = "ERROR" 
        return report

    if image.shape[-1] == 4:
        image = image[..., :3]
    
    h, w, _ = image.shape
    
    best_match_score = -1
    best_candidate_report = None
    
    # Iterate through all available provenance files to find the correct origin
    for hash_file in hash_files:
        candidate_uuid = hash_file.replace("hashes_", "").replace(".json", "")
        # Handle legacy filename
        if hash_file == "image_hashes.json":
            candidate_uuid = "legacy"
            sig_file = "image_sig.bin"
        else:
            sig_file = f"sig_{candidate_uuid}.bin"
            
        json_path = os.path.join(provenance_dir, hash_file)
        sig_path = os.path.join(provenance_dir, sig_file)
        
        if not os.path.exists(sig_path):
            continue

        try:
            # A. Verify Signature
            with open(json_path, "r") as f:
                prov_json_str = f.read()
                prov_data = json.loads(prov_json_str)

            with open(sig_path, "rb") as f:
                signature = f.read()
                
            data_to_verify = json.dumps(prov_data, sort_keys=True).encode()
            public_key.verify(signature, data_to_verify, ec.ECDSA(hashes.SHA256()))
            
            # Signature Valid -> Calculate Match Score
            GRID_ROWS, GRID_COLS = prov_data["grid"]
            stored_hashes = prov_data["hashes"]
            
            # Basic dimension check
            if len(stored_hashes) != GRID_ROWS * GRID_COLS:
                continue

            block_h = h // GRID_ROWS
            block_w = w // GRID_COLS
            
            match_count = 0
            idx = 0
            mismatches = []
            
            # Temporary tamper map for this candidate
            temp_tamper_map = image.copy()
            has_tamper = False

            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    y1 = r * block_h
                    y2 = (r + 1) * block_h if r < GRID_ROWS - 1 else h
                    x1 = c * block_w
                    x2 = (c + 1) * block_w if c < GRID_COLS - 1 else w
                    
                    block = image[y1:y2, x1:x2]
                    block_bytes = block.astype(np.uint8).tobytes()
                    curr_hash = content_hash(block_bytes).hex()
                    
                    if curr_hash == stored_hashes[idx]:
                        match_count += 1
                    else:
                        has_tamper = True
                        mismatches.append(idx)
                        # Draw Red (on temp map)
                        roi = temp_tamper_map[y1:y2, x1:x2].astype(float)
                        red_overlay = np.zeros_like(roi)
                        red_overlay[:] = [255, 0, 0]
                        blended = roi * 0.6 + red_overlay * 0.4
                        temp_tamper_map[y1:y2, x1:x2] = blended.astype(np.uint8)
                        # Borders
                        border = 2
                        temp_tamper_map[y1:y1+border, x1:x2] = [255, 0, 0]
                        temp_tamper_map[y2-border:y2, x1:x2] = [255, 0, 0]
                        temp_tamper_map[y1:y2, x1:x1+border] = [255, 0, 0]
                        temp_tamper_map[y1:y2, x2-border:x2] = [255, 0, 0]

                    idx += 1
            
            score = match_count / (GRID_ROWS * GRID_COLS)
            
            # Save candidate info
            candidate_state = {
                "score": score,
                "status": "VERIFIED" if not has_tamper else "TAMPERED",
                "failure_type": None if not has_tamper else "BLOCK_HASH_MISMATCH",
                "mismatched_blocks": mismatches,
                "tamper_map_img": temp_tamper_map,
                "signed_by": "ECDSA"
            }
            
            # Pick best match
            if score > best_match_score:
                best_match_score = score
                best_candidate_report = candidate_state
                
                # Optimization: If perfect match, stop looking
                if score == 1.0:
                    break
        
        except InvalidSignature:
            continue # Try next file
        except Exception:
            continue

    # 4. Final Report Generation
    if best_candidate_report:
        report["status"] = best_candidate_report["status"]
        report["failure_type"] = best_candidate_report["failure_type"]
        report["mismatched_blocks"] = best_candidate_report["mismatched_blocks"]
        report["signed_by"] = best_candidate_report["signed_by"]
        
        if best_candidate_report["status"] == "TAMPERED":
            map_path = "provenance/tamper_map.png"
            iio.imwrite(map_path, best_candidate_report["tamper_map_img"])
            report["tamper_map"] = map_path
            print(f"Tamper detected (Best Match: {best_match_score:.1%}). Map saved to {map_path}")
        else:
            print(f"Image verified successfully (Match: {best_match_score:.1%})")
            
    else:
        # No valid signature or provenance found matching even partially
        report["status"] = "FAILED"
        report["failure_type"] = "NO_VALID_PROVENANCE_FOUND"

    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python image_verify.py <image.png>")
        sys.exit(1)
    print(json.dumps(verify_image(sys.argv[1]), indent=2))
