import sys
import os
import json
import numpy as np
import imageio.v3 as iio
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from video_utils import content_hash

# Configuration
GRID_ROWS = 8
GRID_COLS = 8

def sign_image(image_path: str):
    # Ensure provenance directory exists
    os.makedirs("provenance", exist_ok=True)
    
    # Check if private key exists
    if not os.path.exists("keys/private_key.pem"):
        raise FileNotFoundError("Error: keys/private_key.pem not found. Run from project root or generate keys.")
    
    with open("keys/private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=None)

    # Load Image
    try:
        image = iio.imread(image_path)
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")

    # Handle RGBA by converting to RGB (transparency creates hashing complexity)
    if image.shape[-1] == 4:
         image = image[..., :3]

    h, w, _ = image.shape
    
    # Calculate Block Sizes
    block_h = h // GRID_ROWS
    block_w = w // GRID_COLS

    block_hashes = []

    # 8x8 Block Hashing
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            # Define Region
            y1 = r * block_h
            y2 = (r + 1) * block_h if r < GRID_ROWS - 1 else h
            x1 = c * block_w
            x2 = (c + 1) * block_w if c < GRID_COLS - 1 else w
            
            # Extract Block
            block = image[y1:y2, x1:x2]
            
            # Hash Block
            block_bytes = block.astype(np.uint8).tobytes()
            b_hash = content_hash(block_bytes)
            block_hashes.append(b_hash.hex())

    import uuid
    prov_id = uuid.uuid4().hex[:8]
    
    # Save Hash Map
    provenance_data = {
        "id": prov_id,
        "grid": [GRID_ROWS, GRID_COLS],
        "hashes": block_hashes
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

    print(f"Image signed with 8x8 Grid. Hashes saved to {prov_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python image_sign.py <image.png>")
        sys.exit(1)
    sign_image(sys.argv[1])
