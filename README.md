# HEMLOCK
### Verifiable Media Engine & Cryptographic Provenance Protocol

![Status](https://img.shields.io/badge/Status-Active-success)
![Version](https://img.shields.io/badge/Version-1.0.5-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

> **"Truth in the age of synthesis."**

Hemlock is a dual-layer defense system designed to restore trust in digital media. As Generative AI models scrape the web to train on unauthorized data, Hemlock provides creators with an **Invisible Armor** against style theft and a **Cryptographic Seal** to prove authenticity.

---

## � The Problem
We are witnessing the **erosion of digital trust**.
*   **Deepfakes** manipulate public opinion.
*   **Style Mimicry** threatens the livelihood of digital artists.
*   **Verification Gap**: There is no standard way to prove a file is "human-made" or "original" once it leaves the creator's device.

## 🛡️ The Solution
Hemlock introduces a "Scan -> Inject -> Sign" pipeline:

1.  **Adversarial Defense (The Shield)**:
    *   Injects mathematical perturbations into the image/video.
    *   **Invisible to Humans**: The image looks identical.
    *   **Blinding to Machines**: Disrupts feature extraction, preventing AI models from learning the style or likeness.

2.  **Cryptographic Provenance (The Seal)**:
    *   Hashes the protected content (SHA-256).
    *   Signs it with a **Device Identity Key** (RSA-2048 / ECDSA).
    *   Creates a tamper-evident record. Any pixel modification breaks the seal.

---

## ✨ Key Features
*   **🎨 Style Protection**: Prevents Midjourney/Stable Diffusion from cloning your artistic style.
*   **🔒 Tamper Detection**: Instantly identifies if an image has been Photoshopped or AI-edited.
*   **📍 Visual Localization**: Generates a "Heat Map" showing exactly *where* the image was manipulated.
*   **⚡ High-Performance Backend**: Pure Python engine optimized for media processing.
*   **📱 Modern UI**: Responsive, glassmorphic interface built with Tailwind CSS.

---

## �️ Technology Stack
*   **Backend**: Python (Flask)
*   **Core Logic**: `numpy`, `imageio`, `cryptography`
*   **Frontend**: HTML5, Vanilla JS, Tailwind CSS
*   **Deployment**: Ready for Render / Heroku / Docker

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.8 or higher
*   `pip` (Python Package Manager)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/hemlock.git
    cd hemlock
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure `ffmpeg` is installed for video processing. `imageio[ffmpeg]` usually handles this automatically.)*

3.  **Run the Server**
    ```bash
    python server.py
    ```

4.  **Access the App**
    Open your browser and navigate to: `http://localhost:5000`

---

## 🔑 Key Management (Security)

Hemlock uses a Public/Private key infrastructure.

**Local Development:**
*   On first run, keys are auto-generated in the `keys/` directory.

**Production (Render/Cloud):**
*   **Do not commit keys to Git.** (The `.gitignore` handles this).
*   Set your identity via Environment Variables:
    *   `PRIVATE_KEY`: Content of `keys/private_key.pem`
    *   `PUBLIC_KEY`: Content of `keys/public_key.pem`

---

## 📸 Usage Guide

### 1. Protect (Sign)
1.  Upload your artwork or footage.
2.  Hemlock injects the adversarial noise (~2-5s).
3.  The file is signed.
4.  **Download** the protected asset.

### 2. Authenticate (Verify)
1.  Upload a suspicious file.
2.  Provide the creator's **Public Key**.
3.  Hemlock verifies the signature and hash map.
4.  **Result**:
    *   ✅ **VERIFIED**: Authentic, original media.
    *   ❌ **TAMPER DETECTED**: File has been altered. (View the red localized map to see where).

---

## 🎓 Try It Yourself (The "Doodle" Test)
Want to see Hemlock in action? Follow this 1-minute loop:

### 1. The Creator (Sign)
1.  Switch to **Sign Mode** in the app.
2.  Upload any image.
3.  **IMPORTANT**: Copy the `Public Key` shown in the black box. (Paste it in Notepad for a second).
4.  Download your signed image.

### 2. The Attacker (Tamper)
Now, let's break the seal.
1.  Open your downloaded image in **Paint**, **Photoshop**, or even an **AI Editor**.
2.  Draw a mustache, change a pixel, or let AI "change" it.
3.  Save the file.
    *   *Note: If you convert the file type (e.g., PNG to JPG), Hemlock considers the entire file changed!*

### 3. The Detective (Verify)
1.  Switch to **Verify Mode** in Hemlock.
2.  Upload your "tampered" image.
3.  Paste the `Public Key` you saved earlier.
4.  Watch the magic:
    *   **Result**: ❌ TAMPER DETECTED.
    *   **Heatmap**: See exactly where you drew that mustache!

---

## 📂 Project Structure
```
Hemlock/
├── server.py              # Main Flask Application
├── python_backend/        # Core Verification & Signing Logic
│   ├── image_sign.py      # Image Hashing & Defense
│   ├── image_verify.py    # Multi-Provenance Verification
│   └── video_utils.py     # Frame extraction utilities
├── ui/                    # Frontend Assets
│   └── index.html         # Main Application Interface
├── provenance/            # Local ledger (Stores Hashes/Signatures)
└── presentation/          # Interactive Project Slides
```

---

---

## 👥 Team

**VibeCraft Development Team**
- Project Lead: [Your Name]
- Backend Developer: [Your Name]
- Frontend Developer: [Your Name]
- Security Engineer: [Your Name]

---

**© 2026 Hemlock Project - VibeCraft Edition.**
*Built for the Future of Media.*
