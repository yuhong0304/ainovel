import sys
from pathlib import Path
import json
import time

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from novel_agent.web.app import app, state

# Initialize state
state.initialize()

def run_test():
    with app.test_client() as client:
        print("\n=== 1. Setup Dummy Project ===")
        client.post('/api/projects', json={"name": "test_calib_project"})
        
        print("\n=== 2. Testing Worldbook Unified API ===")
        # POST Card
        res = client.post('/api/world/test_calib_project/cards', json={
            "name": "Test Char",
            "category": "character",
            "gender": "Unknown"
        })
        print(f"POST Card: {res.status_code}")
        if res.status_code == 200:
            card_id = res.json['card']['id']
            print(f"  Created ID: {card_id}")
            
            # GET Cards
            res = client.get('/api/world/test_calib_project/cards')
            print(f"GET Cards: {res.status_code} (Count: {len(res.json.get('cards', []))})")
            
            # PUT Card
            res = client.put(f'/api/world/test_calib_project/cards/{card_id}', json={"name": "Updated Char"})
            print(f"PUT Card: {res.status_code}")
            
            # DELETE Card
            res = client.delete(f'/api/world/test_calib_project/cards/{card_id}')
            print(f"DELETE Card: {res.status_code}")

        print("\n=== 3. Testing Batch Generation SSE ===")
        # Create Job
        res = client.post('/api/batch/create', json={"project": "test_calib_project", "count": 1})
        print(f"Batch Create: {res.status_code}")
        if res.status_code == 200:
            job_id = res.json['job_id']
            # Test SSE Endpoint existence (GET)
            res = client.get(f'/api/batch/progress/{job_id}')
            print(f"Batch Progress Stream: {res.status_code} (Header: {res.headers.get('Content-Type')})")

        print("\n=== 4. Testing Export Download Alias ===")
        # Create dummy file
        export_dir = Path("d:/game/novel/projects/test_calib_project/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        (export_dir / "test.txt").write_text("content")
        
        # Test Alias URL
        res = client.get('/api/export/test_calib_project/download/test.txt')
        print(f"Download Alias: {res.status_code}")
        
        print("\n=== 5. Testing Previous Fixes (Regression) ===")
        print(f"Stats Daily: {client.get('/api/statistics/test_calib_project/daily').status_code}")
        print(f"Project Detail: {client.get('/api/projects/test_calib_project').status_code}")

        # Cleanup
        # client.delete('/api/projects/test_calib_project')

if __name__ == "__main__":
    try:
        run_test()
        print("\n✅ Verification Complete")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
