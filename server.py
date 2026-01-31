import os
import sys
from flask import Flask, request, send_file, send_from_directory

# Add CWD to system path so we can import video_py modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Also add the python_backend subdirectory so 'import video_utils' works inside those scripts
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python_backend'))

# Import Video Backend
VIDEO_IMPORT_ERROR = None
try:
    # Import directly since we added python_backend to path
    import video_sign
    import video_verify
    import image_sign
    import image_sign
    import image_verify
    import pdf_sign
    import pdf_verify
    from job_manager import job_manager
    VIDEO_BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Video backend not available: {e}")
    VIDEO_IMPORT_ERROR = str(e)
    VIDEO_BACKEND_AVAILABLE = False

app = Flask(__name__, static_folder='ui', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB Limit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR = os.path.join(BASE_DIR, 'keys')
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, 'private_key.pem')
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, 'public_key.pem')

# Ensure Device Keys Exist on Startup
# Priority 1: Load from Environment (Render / Production)
if os.environ.get('PRIVATE_KEY') and os.environ.get('PUBLIC_KEY'):
    try:
        Path(KEYS_DIR).mkdir(exist_ok=True)
        # We assume the keys are passed as PEM strings in the Env Vars
        # Newlines might need handling if they are escaped as \n
        priv_env = os.environ['PRIVATE_KEY'].replace('\\n', '\n')
        pub_env = os.environ['PUBLIC_KEY'].replace('\\n', '\n')
        
        with open(PRIVATE_KEY_PATH, "w") as f:
            f.write(priv_env)
        with open(PUBLIC_KEY_PATH, "w") as f:
            f.write(pub_env)
        print("✔ Loaded Device Keys from Environment Variables")
    except Exception as e:
        print(f"Failed to load keys from environment: {e}")

# Priority 2: Generate New Keys if missing (Local Dev)
if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
    print("Generating Device Identity Keys...")
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        from pathlib import Path
        
        Path(KEYS_DIR).mkdir(exist_ok=True)
        
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ))
            
        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(private_key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ))
        print("✔ Device Identity Created")
    except Exception as e:
        print(f"Failed to generate keys: {e}")

@app.route('/health')
def health_check():
    return {'status': 'alive', 'service': 'hemlock-engine'}, 200

@app.route('/')
def serve_index():
    return send_from_directory('ui', 'index.html')

@app.route('/provenance/<path:filename>')
def serve_provenance(filename):
    return send_from_directory('provenance', filename)

@app.route('/input/<path:filename>')
def serve_input(filename):
    # Determine mimetype based on extension
    ext = os.path.splitext(filename)[1].lower()
    mimetype = 'application/octet-stream'
    if ext in ['.jpg', '.jpeg', '.png']:
        mimetype = 'image/jpeg'
    elif ext in ['.mp4', '.mov']:
        mimetype = 'video/mp4'
    return send_from_directory('.', filename, mimetype=mimetype)

# --- JOB HELPERS ---
def process_protect_async(input_path, mimetype):
    try:
        if mimetype == 'image/jpeg':
             image_sign.sign_image(input_path)
        elif mimetype == 'application/pdf':
             pdf_sign.sign_pdf(input_path)
        else:
             video_sign.sign_video(input_path)
        return {"file_path": input_path, "mimetype": mimetype}
    except Exception as e:
        raise e

def process_verify_async(input_path, mimetype, verify_key_path):
    try:
        if mimetype == 'image/jpeg':
            report = image_verify.verify_image(input_path, public_key_path=verify_key_path)
        elif mimetype == 'application/pdf':
            report = pdf_verify.verify_pdf(input_path, public_key_path=verify_key_path)
        else:
            report = video_verify.verify_video(input_path, public_key_path=verify_key_path)
        
        status = report.get('status', 'UNKNOWN')
        if status == "FAILED":
             status = "TAMPERED"
             
        return {'status': status, 'details': report}
    except Exception as e:
        # Return a structure similar to success but with error status
        return {'status': 'TAMPERED', 'details': str(e)}

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = job_manager.get_job(job_id)
    if not job:
        return {'error': 'Job not found'}, 404
    return job

@app.route('/api/protect', methods=['POST'])
def protect_media():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400

    filename = file.filename
    # Determine mimetype based on extension
    ext = os.path.splitext(filename)[1].lower()
    mimetype = None
    
    if ext in ['.jpg', '.jpeg', '.png']:
        mimetype = 'image/jpeg' 
    elif ext == '.pdf':
        mimetype = 'application/pdf'
    elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
        mimetype = 'video/mp4'
    
    if mimetype is None:
        return {'error': 'Unsupported file type'}, 400 

    if not VIDEO_BACKEND_AVAILABLE:
        return {'error': 'Backend not available', 'details': VIDEO_IMPORT_ERROR}, 501
        
    # Save input
    input_path = os.path.join(BASE_DIR, f'input{ext}')
    
    # We rename input file with UUID to avoid collision in concurrent jobs (optional but good practice)
    # For now, keeping "input.mp4" means race condition if 2 users upload same ext.
    # FIX: Use unique filename for Job Mode
    import uuid
    unique_filename = f"input_{uuid.uuid4().hex}{ext}"
    input_path = os.path.join(BASE_DIR, unique_filename)
    
    file.save(input_path)
    
    # Submit Job
    job_id = job_manager.submit_job(process_protect_async, input_path, mimetype)
    return {"job_id": job_id, "input_path": unique_filename}

@app.route('/api/verify', methods=['POST'])
def verify_media():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    # Handles...
    import uuid
    unique_filename = f"verify_{uuid.uuid4().hex}{ext}"
    input_path = os.path.join(BASE_DIR, unique_filename)
    file.save(input_path)

    mimetype = None
    if ext in ['.jpg', '.jpeg', '.png']:
        mimetype = 'image/jpeg'
    elif ext == '.pdf':
        mimetype = 'application/pdf'
    elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
        mimetype = 'video/mp4'
        
    if mimetype is None:
        # If verify uploaded a non-supported file, we likely should error or just try to verify as video?
        # Better to error.
        return {'error': 'Unsupported file type'}, 400

    if not VIDEO_BACKEND_AVAILABLE:
        return {'error': 'Backend not available', 'details': VIDEO_IMPORT_ERROR}, 501

    # Submit Job
    # Check key
    final_key_path = PUBLIC_KEY_PATH
    if 'key' in request.form and request.form['key'].strip():
         user_key = request.form['key'].strip()
         if "BEGIN PUBLIC KEY" in user_key:
             temp_key_path = os.path.join(BASE_DIR, f'temp_key_{uuid.uuid4().hex}.pem')
             with open(temp_key_path, 'w') as f:
                 f.write(user_key)
             final_key_path = temp_key_path

    job_id = job_manager.submit_job(process_verify_async, input_path, mimetype, final_key_path)
    return {"job_id": job_id}

@app.route('/api/public-key')
def get_public_key():
    # Always return the Device Identity Key
    key_path = PUBLIC_KEY_PATH
    
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            return {'key': f.read()}
    return {'key': '-----BEGIN PUBLIC KEY-----\nNo Key Generated Yet\n-----END PUBLIC KEY-----'}

if __name__ == '__main__':
    print("Starting Hemlock Server on http://localhost:5000")
    app.run(debug=True, port=5000)
