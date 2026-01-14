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
    print("=== Testing Project List ===")
    res = client.get('/api/projects')
    print(f"List Status: {res.status_code}")
    
    # Create dummy project for testing routes
    print("\n=== Creating Dummy Project for Testing ===")
    client.post('/api/projects', json={"name": "test_audit_project"})

    print("\n=== Testing Project Detail (Settings.jsx) ===")
    res = client.get('/api/projects/test_audit_project')
    print(f"Detail Status: {res.status_code}")
    print(res.json)

    print("\n=== Testing Daily Stats (Dashboard.jsx) ===")
    res = client.get('/api/statistics/test_audit_project/daily')
    print(f"Daily Status: {res.status_code}")
    print(res.json)

    print("\n=== Testing Recent Edits (Dashboard.jsx) ===")
    res = client.get('/api/statistics/test_audit_project/recent')
    print(f"Recent Status: {res.status_code}")
    print(res.json)

    print("\n=== Testing Structure Generation Stub (Outliner.jsx) ===")
    res = client.post('/api/project/test_audit_project/structure/generate', json={"master_outline": "test"})
    print(f"Generate Status: {res.status_code}")
    print(res.json)
    
    # Cleanup
    client.delete('/api/projects/test_audit_project')
