import sys
import os
from pathlib import Path

# Add src to path
current_dir = Path.cwd()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

print("Testing backend import and initialization...")

try:
    from novel_agent.web.app import create_app, app
    
    print("✅ App module imported successfully.")
    
    flask_app = create_app()
    print("✅ Flask app created.")
    
    # Print registered routes to verify blueprints
    print("Registered Routes:")
    found_project = False
    found_gen = False
    found_learn = False
    for rule in flask_app.url_map.iter_rules():
        # print(f" - {rule}")
        if "/api/projects" in str(rule):
            found_project = True
        if "/api/generate/stream" in str(rule):
            found_gen = True
        if "/api/learn/rules" in str(rule):
            found_learn = True
            
    if found_project:
        print("✅ Project API detected.")
    else:
        print("❌ Project API NOT detected.")
        sys.exit(1)
        
    if found_gen:
        print("✅ Generation API detected.")
    else:
        print("❌ Generation API NOT detected.")
        sys.exit(1)
        
    if found_learn:
        print("✅ Learning API detected.")
    else:
        print("❌ Learning API NOT detected.")
        sys.exit(1)
        
    print("✅ Verification Passed: Backend structure is valid.")
    
    # Phase 2 Verification
    print("\nPhase 2 Component Verification:")
    try:
        from novel_agent.core.rag import RAGManager
        print("✅ RAGManager imported.")
    except ImportError as e:
        print(f"❌ Failed to import RAGManager: {e}")
        
    try:
        from novel_agent.pipeline.style_analyzer import StyleAnalyzer
        sa = StyleAnalyzer("测试文本。这是一个短句。")
        metrics = sa.analyze_text("测试文本。这是一个短句。")
        print(f"✅ StyleAnalyzer functional. Metrics: {metrics}")
    except Exception as e:
        print(f"❌ Failed to test StyleAnalyzer: {e}")

    try:
        from novel_agent.utils import WorldManager
        print("✅ WorldManager imported.")
    except ImportError as e:
        print(f"❌ Failed to import WorldManager: {e}")
        
except Exception as e:
    print(f"❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
