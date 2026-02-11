import base64
import os

# Read your existing session file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
session_path = os.path.join(BASE_DIR, "session.session")
with open(session_path, "rb") as f:
    session_data = f.read()

# Encode to base64
session_b64 = base64.b64encode(session_data).decode('utf-8')

# Print it (copy this value)
print(session_b64)

# Optional: Save to a temp file to copy easily
with open("session_b64.txt", "w") as f:
    f.write(session_b64)
print("\nSessionB64 saved to session_b64.txt")