"""
番茄小说Agent Web应用
Flask后端 + 现代前端界面
"""

import os
import sys
import json
import queue
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Generator

from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS

# 添加agent目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from novel_agent.core.gemini_client import (
    GeminiClient, 
    get_usage_summary, 
    get_available_models,
    get_model_by_name,
    reset_cost_tracker
)
from novel_agent.core.prompt import PromptManager
from novel_agent.core.context import ContextManager
from novel_agent.pipeline import (
    MetaPromptGenerator,
    MasterOutlineGenerator,
    VolumeOutlineGenerator,
    ChapterOutlineGenerator,
    ContentGenerator,
    PolishProcessor,
    RuleLearner
)

# ============ 配置 ============

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent.parent # web module -> novel_agent package
# Actually, app.py is in src/novel_agent/web/app.py
# parent = web
# parent.parent = novel_agent
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
PROJECTS_DIR = Path.cwd() / "projects"

# 确保目录存在
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# ============ 全局状态 ============

class AppState:
    """应用全局状态"""
    def __init__(self):
        self.llm: Optional[GeminiClient] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.context_manager: Optional[ContextManager] = None
        self.current_model: str = "gemini-2.5-pro"
        
        # 生成进度队列
        self.progress_queues: dict = {}
        
        # 生成参数配置
        self.generation_config = {
            "temperature": 0.7,
            "max_tokens": 8192,
            "top_p": 0.95,
            "top_k": 40
        }
        
        # 参数预设
        self.config_presets = {
            "creative": {"temperature": 1.0, "max_tokens": 8192, "top_p": 0.95, "top_k": 50},
            "balanced": {"temperature": 0.7, "max_tokens": 8192, "top_p": 0.9, "top_k": 40},
            "precise": {"temperature": 0.3, "max_tokens": 4096, "top_p": 0.8, "top_k": 20}
        }
        
    def initialize(self):
        """初始化"""
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        self.current_model = model_name
        
        self.llm = GeminiClient(model_name=model_name)
        self.prompt_manager = PromptManager(str(PROMPTS_DIR))
        self.context_manager = ContextManager(str(PROJECTS_DIR))
        
    def switch_model(self, model_name: str):
        """切换模型"""
        self.llm = GeminiClient(model_name=model_name)
        self.current_model = model_name
    
    def get_llm_config(self):
        """获取LLM配置对象"""
        from novel_agent.core.llm_base import GenerationConfig
        return GenerationConfig(
            temperature=self.generation_config["temperature"],
            max_tokens=self.generation_config["max_tokens"],
            top_p=self.generation_config["top_p"],
            top_k=self.generation_config["top_k"]
        )


state = AppState()


# ============ 页面路由 ============

@app.route('/')
def index():
    """仪表盘"""
    return render_template('index.html')


@app.route('/project/<name>')
def project_detail(name):
    """项目详情页"""
    return render_template('project.html', project_name=name)


@app.route('/settings')
def settings():
    """设置页"""
    return render_template('settings.html')


@app.route('/tools')
def tools():
    """工具箱页"""
    return render_template('tools.html')


# ============ API: 项目管理 ============

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有项目"""
    projects = []
    
    for project_dir in PROJECTS_DIR.iterdir():
        if project_dir.is_dir():
            config_path = project_dir / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 统计章节数
                content_dir = project_dir / "content"
                chapter_count = len(list(content_dir.glob("*.md"))) if content_dir.exists() else 0
                
                projects.append({
                    "name": config.get("name", project_dir.name),
                    "title": config.get("title", ""),
                    "stage": config.get("current_stage", ""),
                    "volume": config.get("current_volume", 1),
                    "chapter": config.get("current_chapter", 1),
                    "created_at": config.get("created_at", ""),
                    "updated_at": config.get("updated_at", ""),
                    "chapter_count": chapter_count
                })
    
    return jsonify({"projects": projects})


@app.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.json
    name = data.get('name')
    title = data.get('title', name)
    inspiration = data.get('inspiration', '')
    
    if not name:
        return jsonify({"error": "项目名称不能为空"}), 400
    
    try:
        project = state.context_manager.create_project(name, title=title)
        
        # 保存灵感
        if inspiration:
            state.context_manager.write_file(inspiration, "inspiration.md")
        
        return jsonify({
            "success": True,
            "name": name,
            "message": f"项目 '{name}' 创建成功"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects/<name>', methods=['GET'])
def get_project(name):
    """获取项目详情"""
    project_path = PROJECTS_DIR / name
    
    if not project_path.exists():
        return jsonify({"error": "项目不存在"}), 404
    
    config_path = project_path / "config.json"
    config = {}
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 获取文件结构
    files = get_project_files(project_path)
    
    return jsonify({
        "name": name,
        "config": config,
        "files": files
    })


@app.route('/api/projects/<name>', methods=['DELETE'])
def delete_project(name):
    """删除项目"""
    import shutil
    
    project_path = PROJECTS_DIR / name
    
    if not project_path.exists():
        return jsonify({"error": "项目不存在"}), 404
    
    try:
        shutil.rmtree(project_path)
        return jsonify({"success": True, "message": f"项目 '{name}' 已删除"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_project_files(project_path: Path) -> list:
    """获取项目文件结构"""
    files = []
    
    for item in sorted(project_path.rglob("*")):
        if item.is_file():
            rel_path = item.relative_to(project_path)
            files.append({
                "path": str(rel_path),
                "name": item.name,
                "size": item.stat().st_size,
                "type": item.suffix[1:] if item.suffix else "file",
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
    
    return files


# ============ API: 文件管理 ============

@app.route('/api/files/<project>/<path:filepath>', methods=['GET'])
def read_file(project, filepath):
    """读取文件内容"""
    file_path = PROJECTS_DIR / project / filepath
    
    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404
    
    try:
        content = file_path.read_text(encoding='utf-8')
        return jsonify({
            "path": filepath,
            "content": content,
            "size": len(content)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/files/<project>/<path:filepath>', methods=['PUT'])
def save_file(project, filepath):
    """保存文件"""
    file_path = PROJECTS_DIR / project / filepath
    data = request.json
    content = data.get('content', '')
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return jsonify({"success": True, "message": "保存成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/files/<project>/<path:filepath>', methods=['DELETE'])
def delete_file(project, filepath):
    """删除文件"""
    file_path = PROJECTS_DIR / project / filepath
    
    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404
    
    try:
        file_path.unlink()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 生成 ============

@app.route('/api/generate/meta', methods=['POST'])
def generate_meta():
    """分析灵感，生成配置"""
    data = request.json
    project = data.get('project')
    inspiration = data.get('inspiration')
    
    if not project or not inspiration:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        state.context_manager.load_project(project)
        
        meta_gen = MetaPromptGenerator(state.llm)
        config = meta_gen.analyze_inspiration(inspiration)
        
        # 保存配置
        config_path = PROJECTS_DIR / project / "novel_config.yaml"
        config_path.write_text(config, encoding='utf-8')
        
        return jsonify({
            "success": True,
            "config": config
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate/master', methods=['POST'])
def generate_master():
    """生成总纲"""
    data = request.json
    project = data.get('project')
    context = data.get('context', '')
    
    try:
        state.context_manager.load_project(project)
        
        master_gen = MasterOutlineGenerator(
            state.llm, state.prompt_manager, state.context_manager
        )
        
        outline = master_gen.generate(
            user_input="根据配置生成总纲",
            additional_context=context
        )
        
        # 保存
        master_gen.save_outline(outline)
        
        return jsonify({
            "success": True,
            "content": outline
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate/volume', methods=['POST'])
def generate_volume():
    """生成粗纲"""
    data = request.json
    project = data.get('project')
    volume_number = data.get('volume', 1)
    
    try:
        state.context_manager.load_project(project)
        
        # 读取总纲
        master_outline = state.context_manager.read_file("master_outline.md")
        if not master_outline:
            return jsonify({"error": "请先生成总纲"}), 400
        
        volume_gen = VolumeOutlineGenerator(
            state.llm, state.prompt_manager, state.context_manager
        )
        
        outline = volume_gen.generate(
            master_outline=master_outline,
            volume_number=volume_number
        )
        
        volume_gen.save_outline(outline, volume_number)
        
        return jsonify({
            "success": True,
            "content": outline
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate/content', methods=['POST'])
def generate_content():
    """生成正文"""
    data = request.json
    project = data.get('project')
    chapter_outline = data.get('outline')
    chapter_number = data.get('chapter', 1)
    
    try:
        state.context_manager.load_project(project)
        
        content_gen = ContentGenerator(
            state.llm, state.prompt_manager, state.context_manager
        )
        
        content = content_gen.generate(chapter_outline=chapter_outline)
        content_gen.save_content(content, chapter_number, "raw")
        
        return jsonify({
            "success": True,
            "content": content,
            "word_count": len(content)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate/polish', methods=['POST'])
def generate_polish():
    """润色正文"""
    data = request.json
    project = data.get('project')
    content = data.get('content')
    chapter_number = data.get('chapter', 1)
    
    try:
        state.context_manager.load_project(project)
        
        polish_proc = PolishProcessor(
            state.llm, state.prompt_manager, state.context_manager
        )
        
        polished = polish_proc.polish(content)
        polish_proc.save_versions(content, polished, chapter_number)
        
        return jsonify({
            "success": True,
            "content": polished,
            "word_count": len(polished)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: SSE 实时进度 ============

@app.route('/api/generate/stream', methods=['POST'])
def generate_stream():
    """流式生成（SSE）"""
    data = request.json
    project = data.get('project')
    stage = data.get('stage')  # meta/master/volume/chapter/content/polish
    params = data.get('params', {})
    
    # 创建进度队列
    queue_id = f"{project}_{stage}_{datetime.now().timestamp()}"
    progress_queue = queue.Queue()
    state.progress_queues[queue_id] = progress_queue
    
    # 启动后台生成
    def generate_task():
        try:
            progress_queue.put({"type": "start", "message": f"开始{stage}生成..."})
            
            state.context_manager.load_project(project)
            
            if stage == "content":
                content_gen = ContentGenerator(
                    state.llm, state.prompt_manager, state.context_manager
                )
                
                # 流式生成
                full_content = ""
                for chunk in content_gen.generate_stream(
                    chapter_outline=params.get('outline', '')
                ):
                    full_content += chunk
                    progress_queue.put({
                        "type": "chunk",
                        "content": chunk,
                        "total": len(full_content)
                    })
                
                progress_queue.put({
                    "type": "complete",
                    "content": full_content,
                    "word_count": len(full_content)
                })
            else:
                progress_queue.put({"type": "error", "message": "不支持的生成类型"})
                
        except Exception as e:
            progress_queue.put({"type": "error", "message": str(e)})
        finally:
            progress_queue.put({"type": "done"})
    
    thread = threading.Thread(target=generate_task)
    thread.start()
    
    return jsonify({"queue_id": queue_id})


@app.route('/api/generate/progress/<queue_id>')
def get_progress(queue_id):
    """获取生成进度（SSE）"""
    def event_stream():
        if queue_id not in state.progress_queues:
            yield f"data: {json.dumps({'type': 'error', 'message': '无效的队列ID'})}\n\n"
            return
        
        progress_queue = state.progress_queues[queue_id]
        
        while True:
            try:
                event = progress_queue.get(timeout=60)
                yield f"data: {json.dumps(event)}\n\n"
                
                if event.get('type') == 'done':
                    del state.progress_queues[queue_id]
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )


# ============ API: 设置 ============

@app.route('/api/settings/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    models = get_available_models()
    return jsonify({
        "models": models,
        "current": state.current_model
    })


@app.route('/api/settings/model', methods=['POST'])
def set_model():
    """切换模型"""
    data = request.json
    model_name = data.get('model')
    
    if not model_name:
        return jsonify({"error": "模型名称不能为空"}), 400
    
    try:
        state.switch_model(model_name)
        return jsonify({
            "success": True,
            "model": model_name,
            "message": f"已切换到 {model_name}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/settings/usage', methods=['GET'])
def get_usage():
    """获取Token使用统计"""
    usage = get_usage_summary()
    return jsonify(usage)


@app.route('/api/settings/usage/reset', methods=['POST'])
def reset_usage():
    """重置使用统计"""
    reset_cost_tracker()
    return jsonify({"success": True})


# ============ API: 生成参数 ============

@app.route('/api/settings/params', methods=['GET'])
def get_params():
    """获取生成参数"""
    return jsonify({
        "config": state.generation_config,
        "presets": state.config_presets
    })


@app.route('/api/settings/params', methods=['POST'])
def set_params():
    """设置生成参数"""
    data = request.json
    
    # 更新参数
    for key in ["temperature", "max_tokens", "top_p", "top_k"]:
        if key in data:
            state.generation_config[key] = data[key]
    
    return jsonify({
        "success": True,
        "config": state.generation_config
    })


@app.route('/api/settings/params/preset/<name>', methods=['POST'])
def apply_preset(name):
    """应用预设参数"""
    if name not in state.config_presets:
        return jsonify({"error": "预设不存在"}), 404
    
    state.generation_config.update(state.config_presets[name])
    return jsonify({
        "success": True,
        "preset": name,
        "config": state.generation_config
    })


# ============ API: Prompt模板管理 ============

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """获取所有Prompt模板"""
    templates = []
    
    stages_dir = PROMPTS_DIR / "stages"
    if stages_dir.exists():
        for f in stages_dir.glob("*.md"):
            content = f.read_text(encoding='utf-8')
            templates.append({
                "name": f.stem,
                "path": f"stages/{f.name}",
                "size": len(content),
                "preview": content[:200] + "..." if len(content) > 200 else content
            })
    
    system_dir = PROMPTS_DIR / "system"
    if system_dir.exists():
        for f in system_dir.glob("*.md"):
            content = f.read_text(encoding='utf-8')
            templates.append({
                "name": f.stem,
                "path": f"system/{f.name}",
                "size": len(content),
                "preview": content[:200] + "..." if len(content) > 200 else content
            })
    
    return jsonify({"templates": templates})


@app.route('/api/prompts/<path:filepath>', methods=['GET'])
def get_prompt(filepath):
    """读取Prompt模板内容"""
    file_path = PROMPTS_DIR / filepath
    
    if not file_path.exists():
        return jsonify({"error": "模板不存在"}), 404
    
    content = file_path.read_text(encoding='utf-8')
    
    # 解析变量
    import re
    variables = list(set(re.findall(r'\{\{\s*(\w+)\s*\}\}', content)))
    
    return jsonify({
        "path": filepath,
        "content": content,
        "variables": variables
    })


@app.route('/api/prompts/<path:filepath>', methods=['PUT'])
def save_prompt(filepath):
    """保存Prompt模板"""
    file_path = PROMPTS_DIR / filepath
    data = request.json
    content = data.get('content', '')
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts/preview', methods=['POST'])
def preview_prompt():
    """预览Prompt（填入变量）"""
    data = request.json
    template = data.get('template', '')
    variables = data.get('variables', {})
    
    # 简单变量替换
    result = template
    for key, value in variables.items():
        result = result.replace('{{' + key + '}}', str(value))
        result = result.replace('{{ ' + key + ' }}', str(value))
    
    return jsonify({
        "preview": result
    })


# ============ API: 真正的流式生成 ============

@app.route('/api/stream/generate', methods=['POST'])
def stream_generate():
    """真正的流式生成（直接SSE）"""
    data = request.json
    prompt = data.get('prompt', '')
    system_prompt = data.get('system_prompt', '')
    
    def generate():
        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            full_content = ""
            config = state.get_llm_config()
            
            for chunk in state.llm.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                config=config
            ):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'total': len(full_content)})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'content': full_content, 'word_count': len(full_content)})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ============ API: 角色数据库 (17) ============

@app.route('/api/characters/<project>', methods=['GET'])
def get_characters(project):
    """获取项目角色列表"""
    chars_path = PROJECTS_DIR / project / "characters.json"
    
    if not chars_path.exists():
        return jsonify({"characters": []})
    
    with open(chars_path, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    
    return jsonify({"characters": characters})


@app.route('/api/characters/<project>', methods=['POST'])
def add_character(project):
    """添加角色"""
    chars_path = PROJECTS_DIR / project / "characters.json"
    
    characters = []
    if chars_path.exists():
        with open(chars_path, 'r', encoding='utf-8') as f:
            characters = json.load(f)
    
    data = request.json
    new_char = {
        "id": len(characters) + 1,
        "name": data.get("name", ""),
        "alias": data.get("alias", ""),
        "gender": data.get("gender", ""),
        "age": data.get("age", ""),
        "role": data.get("role", "主角"),  # 主角/配角/反派/龙套
        "personality": data.get("personality", ""),
        "appearance": data.get("appearance", ""),
        "background": data.get("background", ""),
        "abilities": data.get("abilities", []),
        "relationships": data.get("relationships", []),
        "speech_style": data.get("speech_style", ""),
        "first_appearance": data.get("first_appearance", ""),
        "status": data.get("status", "存活"),
        "created_at": datetime.now().isoformat()
    }
    
    characters.append(new_char)
    
    with open(chars_path, 'w', encoding='utf-8') as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "character": new_char})


@app.route('/api/characters/<project>/<int:char_id>', methods=['PUT'])
def update_character(project, char_id):
    """更新角色"""
    chars_path = PROJECTS_DIR / project / "characters.json"
    
    if not chars_path.exists():
        return jsonify({"error": "角色不存在"}), 404
    
    with open(chars_path, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    
    for i, char in enumerate(characters):
        if char.get("id") == char_id:
            characters[i].update(request.json)
            break
    
    with open(chars_path, 'w', encoding='utf-8') as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True})


@app.route('/api/characters/<project>/<int:char_id>', methods=['DELETE'])
def delete_character(project, char_id):
    """删除角色"""
    chars_path = PROJECTS_DIR / project / "characters.json"
    
    if not chars_path.exists():
        return jsonify({"error": "角色不存在"}), 404
    
    with open(chars_path, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    
    characters = [c for c in characters if c.get("id") != char_id]
    
    with open(chars_path, 'w', encoding='utf-8') as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True})


# ============ API: 世界观设定库 (18) ============

@app.route('/api/worldbuilding/<project>', methods=['GET'])
def get_worldbuilding(project):
    """获取世界观设定"""
    world_path = PROJECTS_DIR / project / "worldbuilding.json"
    
    if not world_path.exists():
        return jsonify({"settings": [], "categories": ["地点", "势力", "道具", "规则", "历史", "其他"]})
    
    with open(world_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)


@app.route('/api/worldbuilding/<project>', methods=['POST'])
def add_worldbuilding(project):
    """添加设定"""
    world_path = PROJECTS_DIR / project / "worldbuilding.json"
    
    data = {"settings": [], "categories": ["地点", "势力", "道具", "规则", "历史", "其他"]}
    if world_path.exists():
        with open(world_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    new_setting = {
        "id": len(data["settings"]) + 1,
        "name": request.json.get("name", ""),
        "category": request.json.get("category", "其他"),
        "description": request.json.get("description", ""),
        "details": request.json.get("details", ""),
        "related": request.json.get("related", []),
        "created_at": datetime.now().isoformat()
    }
    
    data["settings"].append(new_setting)
    
    with open(world_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "setting": new_setting})


# ============ API: 伏笔管理器 (19) ============

@app.route('/api/foreshadowing/<project>', methods=['GET'])
def get_foreshadowing(project):
    """获取伏笔列表"""
    fore_path = PROJECTS_DIR / project / "foreshadowing.json"
    
    if not fore_path.exists():
        return jsonify({"foreshadowing": []})
    
    with open(fore_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)


@app.route('/api/foreshadowing/<project>', methods=['POST'])
def add_foreshadowing(project):
    """添加伏笔"""
    fore_path = PROJECTS_DIR / project / "foreshadowing.json"
    
    data = {"foreshadowing": []}
    if fore_path.exists():
        with open(fore_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    new_fore = {
        "id": len(data["foreshadowing"]) + 1,
        "title": request.json.get("title", ""),
        "description": request.json.get("description", ""),
        "planted_chapter": request.json.get("planted_chapter", ""),
        "planned_payoff": request.json.get("planned_payoff", ""),
        "actual_payoff": request.json.get("actual_payoff", ""),
        "status": request.json.get("status", "未回收"),  # 未回收/部分回收/已回收
        "importance": request.json.get("importance", "普通"),  # 主线/支线/普通
        "created_at": datetime.now().isoformat()
    }
    
    data["foreshadowing"].append(new_fore)
    
    with open(fore_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "foreshadowing": new_fore})


@app.route('/api/foreshadowing/<project>/<int:fore_id>', methods=['PUT'])
def update_foreshadowing(project, fore_id):
    """更新伏笔状态"""
    fore_path = PROJECTS_DIR / project / "foreshadowing.json"
    
    if not fore_path.exists():
        return jsonify({"error": "伏笔不存在"}), 404
    
    with open(fore_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for i, fore in enumerate(data["foreshadowing"]):
        if fore.get("id") == fore_id:
            data["foreshadowing"][i].update(request.json)
            break
    
    with open(fore_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True})


# ============ API: 章节摘要 (20) ============

@app.route('/api/summaries/<project>', methods=['GET'])
def get_summaries(project):
    """获取章节摘要"""
    summ_path = PROJECTS_DIR / project / "summaries.json"
    
    if not summ_path.exists():
        return jsonify({"summaries": []})
    
    with open(summ_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)


@app.route('/api/summaries/<project>/generate/<int:chapter>', methods=['POST'])
def generate_summary(project, chapter):
    """生成章节摘要"""
    summ_path = PROJECTS_DIR / project / "summaries.json"
    content_path = PROJECTS_DIR / project / "content" / f"chapter_{chapter:03d}.md"
    
    if not content_path.exists():
        return jsonify({"error": "章节不存在"}), 404
    
    content = content_path.read_text(encoding='utf-8')
    
    # 使用LLM生成摘要
    prompt = f"请用50-100字总结以下章节的主要情节:\n\n{content[:3000]}"
    result = state.llm.generate(prompt, config=state.get_llm_config())
    
    data = {"summaries": []}
    if summ_path.exists():
        with open(summ_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # 更新或添加
    found = False
    for i, s in enumerate(data["summaries"]):
        if s.get("chapter") == chapter:
            data["summaries"][i]["summary"] = result.content
            found = True
            break
    
    if not found:
        data["summaries"].append({
            "chapter": chapter,
            "summary": result.content,
            "generated_at": datetime.now().isoformat()
        })
    
    with open(summ_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "summary": result.content})


# ============ API: 生成历史 (15) ============

@app.route('/api/history/<project>', methods=['GET'])
def get_history(project):
    """获取生成历史"""
    hist_path = PROJECTS_DIR / project / "history.json"
    
    if not hist_path.exists():
        return jsonify({"history": []})
    
    with open(hist_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 只返回最近50条
    data["history"] = data["history"][-50:]
    return jsonify(data)


def log_generation(project, stage, content, tokens=0):
    """记录生成历史"""
    hist_path = PROJECTS_DIR / project / "history.json"
    
    data = {"history": []}
    if hist_path.exists():
        with open(hist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    data["history"].append({
        "id": len(data["history"]) + 1,
        "stage": stage,
        "preview": content[:200] if content else "",
        "length": len(content) if content else 0,
        "tokens": tokens,
        "timestamp": datetime.now().isoformat()
    })
    
    # 只保留最近100条
    data["history"] = data["history"][-100:]
    
    with open(hist_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============ API: 统计分析 (25-30) ============

@app.route('/api/statistics/<project>', methods=['GET'])
def get_statistics(project):
    """获取写作统计"""
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    stats = {
        "total_words": 0,
        "total_chapters": 0,
        "avg_chapter_length": 0,
        "dialogue_ratio": 0,
        "chapters": [],
        "daily_words": {},
        "word_frequency": {}
    }
    
    if not content_dir.exists():
        return jsonify(stats)
    
    import re
    from collections import Counter
    
    all_text = ""
    chapter_lengths = []
    
    for chapter_file in sorted(content_dir.glob("*.md")):
        content = chapter_file.read_text(encoding='utf-8')
        word_count = len(content)
        
        stats["chapters"].append({
            "name": chapter_file.stem,
            "words": word_count,
            "modified": datetime.fromtimestamp(chapter_file.stat().st_mtime).isoformat()
        })
        
        stats["total_words"] += word_count
        chapter_lengths.append(word_count)
        all_text += content
        
        # 按日期统计
        date_str = datetime.fromtimestamp(chapter_file.stat().st_mtime).strftime("%Y-%m-%d")
        stats["daily_words"][date_str] = stats["daily_words"].get(date_str, 0) + word_count
    
    stats["total_chapters"] = len(chapter_lengths)
    stats["avg_chapter_length"] = sum(chapter_lengths) // len(chapter_lengths) if chapter_lengths else 0
    
    # 对话比例 (简单估算：引号内的内容)
    dialogue = len(re.findall(r'[""「」『』].*?[""「」『』]', all_text))
    stats["dialogue_ratio"] = round(dialogue / max(len(all_text), 1) * 100, 1)
    
    # 词频分析 (取前20个)
    words = re.findall(r'[\u4e00-\u9fff]+', all_text)
    word_counts = Counter([w for w in words if len(w) >= 2])
    stats["word_frequency"] = dict(word_counts.most_common(20))
    
    return jsonify(stats)


@app.route('/api/statistics/cost', methods=['GET'])
def get_cost_statistics():
    """获取成本统计"""
    usage = get_usage_summary()
    
    # 按模型分类成本
    return jsonify({
        "usage": usage,
        "breakdown": {
            "pro_cost": usage.get("total_cost_usd", 0) * 0.7,  # 估算
            "flash_cost": usage.get("total_cost_usd", 0) * 0.3
        }
    })


# ============ API: 导出功能 (31-35) ============

@app.route('/api/export/<project>/txt', methods=['GET'])
def export_txt(project):
    """导出为TXT"""
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    if not content_dir.exists():
        return jsonify({"error": "无内容可导出"}), 404
    
    full_text = ""
    for chapter_file in sorted(content_dir.glob("*.md")):
        content = chapter_file.read_text(encoding='utf-8')
        full_text += f"\n\n{'='*40}\n{chapter_file.stem}\n{'='*40}\n\n{content}"
    
    # 保存到导出目录
    export_dir = project_path / "export"
    export_dir.mkdir(exist_ok=True)
    
    export_path = export_dir / f"{project}.txt"
    export_path.write_text(full_text, encoding='utf-8')
    
    return jsonify({
        "success": True,
        "path": str(export_path),
        "size": len(full_text)
    })


@app.route('/api/export/<project>/zip', methods=['GET'])
def export_zip(project):
    """打包导出ZIP"""
    import zipfile
    import io
    
    project_path = PROJECTS_DIR / project
    
    if not project_path.exists():
        return jsonify({"error": "项目不存在"}), 404
    
    # 创建内存中的ZIP
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(project_path)
                zf.write(file_path, arcname)
    
    memory_file.seek(0)
    
    return Response(
        memory_file.getvalue(),
        mimetype='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename={project}.zip'
        }
    )


@app.route('/api/export/<project>/merge', methods=['POST'])
def export_merged(project):
    """合并导出章节"""
    data = request.json
    chapters = data.get("chapters", [])  # 章节列表
    format_type = data.get("format", "txt")  # txt/md
    
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    merged = ""
    for chapter_file in sorted(content_dir.glob("*.md")):
        if not chapters or chapter_file.stem in chapters:
            content = chapter_file.read_text(encoding='utf-8')
            merged += f"\n\n# {chapter_file.stem}\n\n{content}"
    
    export_dir = project_path / "export"
    export_dir.mkdir(exist_ok=True)
    
    filename = f"{project}_merged.{format_type}"
    export_path = export_dir / filename
    export_path.write_text(merged, encoding='utf-8')
    
    return jsonify({
        "success": True,
        "path": str(export_path),
        "size": len(merged)
    })


# ============ API: 批量生成 (9, 16) ============

@app.route('/api/batch/generate', methods=['POST'])
def batch_generate():
    """批量生成多章"""
    data = request.json
    project = data.get("project")
    start_chapter = data.get("start", 1)
    count = data.get("count", 3)
    
    results = []
    
    try:
        state.context_manager.load_project(project)
        
        for i in range(count):
            chapter_num = start_chapter + i
            
            # 生成本章（简化版）
            content_gen = ContentGenerator(
                state.llm, state.prompt_manager, state.context_manager
            )
            
            outline = f"第{chapter_num}章的内容"
            content = content_gen.generate(chapter_outline=outline)
            content_gen.save_content(content, chapter_num, "raw")
            
            results.append({
                "chapter": chapter_num,
                "words": len(content),
                "success": True
            })
            
            log_generation(project, f"content_chapter_{chapter_num}", content)
        
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 版本历史 (4) ============

@app.route('/api/versions/<project>/<path:filepath>', methods=['GET'])
def get_versions(project, filepath):
    """获取文件版本历史"""
    versions_dir = PROJECTS_DIR / project / ".versions" / filepath
    
    if not versions_dir.exists():
        return jsonify({"versions": []})
    
    versions = []
    for v_file in sorted(versions_dir.glob("*.md"), reverse=True):
        versions.append({
            "name": v_file.stem,
            "size": v_file.stat().st_size,
            "created": datetime.fromtimestamp(v_file.stat().st_mtime).isoformat()
        })
    
    return jsonify({"versions": versions[:20]})  # 最近20个版本


@app.route('/api/versions/<project>/<path:filepath>', methods=['POST'])
def save_version(project, filepath):
    """保存版本快照"""
    file_path = PROJECTS_DIR / project / filepath
    versions_dir = PROJECTS_DIR / project / ".versions" / filepath
    
    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404
    
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_path = versions_dir / f"v_{timestamp}.md"
    
    content = file_path.read_text(encoding='utf-8')
    version_path.write_text(content, encoding='utf-8')
    
    return jsonify({"success": True, "version": timestamp})


# ============ API: 主题设置 (36) ============

@app.route('/api/settings/theme', methods=['GET'])
def get_theme():
    """获取主题设置"""
    return jsonify({
        "theme": state.generation_config.get("theme", "dark"),
        "available": ["dark", "light"]
    })


@app.route('/api/settings/theme', methods=['POST'])
def set_theme():
    """设置主题"""
    data = request.json
    theme = data.get("theme", "dark")
    state.generation_config["theme"] = theme
    return jsonify({"success": True, "theme": theme})


# ============ API: 自动保存 (1) ============

@app.route('/api/autosave/<project>/<path:filepath>', methods=['POST'])
def autosave(project, filepath):
    """自动保存"""
    file_path = PROJECTS_DIR / project / filepath
    data = request.json
    content = data.get('content', '')
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        
        # 记录自动保存时间
        return jsonify({
            "success": True,
            "saved_at": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 搜索替换 (3) ============

@app.route('/api/search/<project>', methods=['POST'])
def search_content(project):
    """全文搜索"""
    data = request.json
    query = data.get("query", "")
    
    if not query:
        return jsonify({"results": []})
    
    project_path = PROJECTS_DIR / project
    results = []
    
    for file_path in project_path.rglob("*.md"):
        content = file_path.read_text(encoding='utf-8')
        
        if query in content:
            # 找到匹配位置
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if query in line:
                    results.append({
                        "file": str(file_path.relative_to(project_path)),
                        "line": i + 1,
                        "context": line[:100],
                        "match_count": line.count(query)
                    })
    
    return jsonify({"results": results[:50]})


@app.route('/api/replace/<project>', methods=['POST'])
def replace_content(project):
    """全文替换"""
    data = request.json
    search = data.get("search", "")
    replace = data.get("replace", "")
    files = data.get("files", [])  # 指定文件列表，空为全部
    
    if not search:
        return jsonify({"error": "搜索内容不能为空"}), 400
    
    project_path = PROJECTS_DIR / project
    replaced_count = 0
    
    for file_path in project_path.rglob("*.md"):
        rel_path = str(file_path.relative_to(project_path))
        
        if files and rel_path not in files:
            continue
        
        content = file_path.read_text(encoding='utf-8')
        
        if search in content:
            new_content = content.replace(search, replace)
            file_path.write_text(new_content, encoding='utf-8')
            replaced_count += content.count(search)
    
    return jsonify({
        "success": True,
        "replaced_count": replaced_count
    })


# ============ API: 字数目标 (5) ============

@app.route('/api/goals/<project>', methods=['GET'])
def get_goals(project):
    """获取字数目标"""
    goals_path = PROJECTS_DIR / project / "goals.json"
    
    if not goals_path.exists():
        return jsonify({
            "daily_goal": 3000,
            "total_goal": 100000,
            "progress": {}
        })
    
    with open(goals_path, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/goals/<project>', methods=['POST'])
def set_goals(project):
    """设置字数目标"""
    goals_path = PROJECTS_DIR / project / "goals.json"
    data = request.json
    
    goals = {
        "daily_goal": data.get("daily_goal", 3000),
        "total_goal": data.get("total_goal", 100000),
        "progress": data.get("progress", {})
    }
    
    with open(goals_path, 'w', encoding='utf-8') as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "goals": goals})


# ============ API: 时间线 (21) ============

@app.route('/api/timeline/<project>', methods=['GET'])
def get_timeline(project):
    """获取时间线"""
    timeline_path = PROJECTS_DIR / project / "timeline.json"
    
    if not timeline_path.exists():
        return jsonify({"events": []})
    
    with open(timeline_path, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/timeline/<project>', methods=['POST'])
def add_timeline_event(project):
    """添加时间线事件"""
    timeline_path = PROJECTS_DIR / project / "timeline.json"
    
    data = {"events": []}
    if timeline_path.exists():
        with open(timeline_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    new_event = {
        "id": len(data["events"]) + 1,
        "time": request.json.get("time", ""),
        "title": request.json.get("title", ""),
        "description": request.json.get("description", ""),
        "chapter": request.json.get("chapter", ""),
        "characters": request.json.get("characters", []),
        "type": request.json.get("type", "plot")  # plot/character/world
    }
    
    data["events"].append(new_event)
    
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "event": new_event})


# ============ 启动 ============

def run_server():
    """启动Web服务器"""
    print("🚀 番茄小说Agent Web版启动中...")
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
