import sys
import os
import threading
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# path setup
current_dir = Path(__file__).parent
agent_dir = current_dir.parent
src_dir = agent_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from novel_agent.web.state import state, PROJECTS_DIR, PROMPTS_DIR, BASE_DIR
from novel_agent.web.api import register_blueprints

app = Flask(__name__, static_folder=str(BASE_DIR / 'web/static'))
CORS(app) # Enable CORS

# Register Blueprints
register_blueprints(app)

# ============ 静态文件服务 ============

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/') or path.startswith('static/'):
         return jsonify({"error": "Not Found"}), 404
    
    # Serve React App
    # Assuming standard vite build output to dist
    dist_dir = BASE_DIR / 'web/static/dist'
    if not dist_dir.exists():
        # Fallback for dev or generic static
        return jsonify({"message": "Frontend not built or not found in web/static/dist"}), 404
        
    if path != "" and (dist_dir / path).exists():
        return send_from_directory(dist_dir, path)
    else:
        return send_from_directory(dist_dir, 'index.html')

def create_app():
    """应用工厂函数"""
    # 确保在应用启动时初始化全局状态
    print("🚀 Initializing Application State...")
    state.initialize()
    return app

def run_server():
    """启动Web服务器"""
    print("🚀 番茄小说Agent Web版启动中... (Refactored Modular Version)")
    state.initialize()
    print(f"✓ 模型: {state.current_model}")
    print(f"✓ 项目目录: {PROJECTS_DIR}")
    print("\n访问: http://localhost:5000\n")
    
    # 确保在开发模式下能够找到模板
    if not app.debug:
        import webbrowser
        try:
            threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
        except:
            pass
            
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

if __name__ == '__main__':
    run_server()
