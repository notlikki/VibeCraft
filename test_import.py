import sys
import os

# Mimic server.py path setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'video_py'))

print(f"CWD: {os.getcwd()}")
print(f"Sys Path: {sys.path}")

try:
    import imageio
    print("ImageIO: OK")
except ImportError as e:
    print(f"ImageIO: FAIL - {e}")

try:
    import cryptography
    print("Cryptography: OK")
except ImportError as e:
    print(f"Cryptography: FAIL - {e}")

try:
    import video_sign
    print("VideoSign: OK")
except ImportError as e:
    print(f"VideoSign: FAIL - {e}")
except Exception as e:
    print(f"VideoSign: ERROR - {e}")
