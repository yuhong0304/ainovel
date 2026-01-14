import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from novel_agent.web.app import app, state

# Initialize state
state.initialize()

# Create test client
with app.test_client() as client:
    response = client.get('/api/projects')
    print(f"Status Code: {response.status_code}")
    print("Response Data:")
    print(json.dumps(response.json, indent=2, ensure_ascii=False))
