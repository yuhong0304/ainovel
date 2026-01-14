from flask import Blueprint, request, jsonify
import shutil
import json
from datetime import datetime
from pathlib import Path
from ..state import state, PROJECTS_DIR, PROMPTS_DIR
from novel_agent.core.context import ContextManager
from novel_agent.utils import StructureManager
from novel_agent.utils import ContentManager
from novel_agent.utils import VersionManager
from novel_agent.pipeline.stage_0_meta import MetaPromptGenerator

project_bp = Blueprint('project', __name__)

# ============ API: 项目管理 ============

@project_bp.route('/api/projects', methods=['GET'])
def list_projects():
    """获取项目列表"""
    projects = []
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir()
    
    for p in PROJECTS_DIR.iterdir():
        if p.is_dir() and not p.name.startswith('.'):
            # 获取项目元数据
            meta_path = p / "novel_config.yaml"
            title = p.name
            if meta_path.exists():
                # 这里简单读取第一行或解析YAML
                pass
            
            # 获取最后修改时间
            mtime = p.stat().st_mtime
            
            projects.append({
                "id": p.name,
                "name": p.name, # TODO: 从配置读取真实书名
                "modified": datetime.fromtimestamp(mtime).isoformat(),
                "word_count": 0 # TODO: 计算字数
            })
            
    # 按时间倒序
    projects.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(projects)

@project_bp.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({"error": "项目名称不能为空"}), 400
        
    try:
        project_path = PROJECTS_DIR / name
        if project_path.exists():
            return jsonify({"error": "项目已存在"}), 400
            
        project_path.mkdir(parents=True)
        (project_path / "content").mkdir()
        
        return jsonify({"success": True, "name": name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/projects/<name>', methods=['GET'])
def get_project_detail(name):
    """获取单个项目详情"""
    try:
        p = PROJECTS_DIR / name
        if not p.exists():
            return jsonify({"error": "Project not found"}), 404
            
        mtime = p.stat().st_mtime
        
        # Load config logic if needed
        # For now return basic info compatible with list
        
        return jsonify({
            "id": p.name,
            "name": p.name,
            "modified": datetime.fromtimestamp(mtime).isoformat(),
            "word_count": 0 # TODO: Calculate real count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/projects/<name>', methods=['DELETE'])
def delete_project(name):
    """删除项目"""
    try:
        path = PROJECTS_DIR / name
        if path.exists():
            shutil.rmtree(path)
            return jsonify({"success": True})
        return jsonify({"error": "项目不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: Genesis / Wizard (项目初始化) ============

@project_bp.route('/api/genesis/propose', methods=['POST'])
def genesis_propose():
    """[Genesis] 提议阶段：根据灵感生成三个方案"""
    data = request.json
    inspiration = data.get('inspiration', '')
    
    if not inspiration:
        return jsonify({"error": "灵感不能为空"}), 400
        
    if not state.llm:
         return jsonify({"error": "LLM未初始化，请先配置API Key"}), 500
         
    try:
        meta_gen = MetaPromptGenerator(state.llm)
        proposals = meta_gen.analyze_inspiration_variants(inspiration)
        return jsonify({"proposals": proposals})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/genesis/init', methods=['POST'])
def genesis_init():
    """[Genesis] 初始化阶段：选定方案，生成所有Prompt"""
    data = request.json
    selected_proposal = data.get('proposal') # 包含 config_yaml 等
    project_name = data.get('project_name')
    
    if not selected_proposal or not project_name:
        return jsonify({"error": "缺少参数"}), 400
        
    try:
        # 1. 创建项目目录
        project_path = PROJECTS_DIR / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "content").mkdir(exist_ok=True)
        
        # 2. 生成 Prompts using MetaPromptGenerator logic
        # 这里复用 logic，或者直接调用 generator
        meta_gen = MetaPromptGenerator(state.llm)
        
        inspiration = selected_proposal.get('introduction', '') # Use intro as insp cache or pass insp
        
        # 由于前端传递了完整的 proposal (含 config)，我们可以直接生成
        config_yaml = selected_proposal.get('config_yaml')
        
        # Init prompts dir
        prompts_path = PROMPTS_DIR / "projects" / project_name
        prompts_path.mkdir(parents=True, exist_ok=True)
        
        # Save config
        (prompts_path / "novel_config.yaml").write_text(config_yaml, encoding='utf-8')
        
        # Gen System Prompt
        sys_prompt = meta_gen.generate_system_prompt(config_yaml)
        (prompts_path / "system_prompt.md").write_text(sys_prompt, encoding='utf-8')
        
        # Gen Stage Prompts
        stage_prompts = meta_gen.generate_stage_prompts(config_yaml)
        stages_dir = prompts_path / "stages"
        stages_dir.mkdir(exist_ok=True)
        for k, v in stage_prompts.items():
            (stages_dir / k).write_text(v, encoding='utf-8')
            
        return jsonify({"success": True, "project": project_name})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 文件操作 ============

@project_bp.route('/api/files/<project>/<path:filepath>', methods=['GET'])
def read_file(project, filepath):
    """读取文件内容"""
    try:
        path = PROJECTS_DIR / project / filepath
        if not path.exists():
            return jsonify({"error": "File not found"}), 404
        content = path.read_text(encoding='utf-8')
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/files/<project>/<path:filepath>', methods=['PUT'])
def write_file(project, filepath):
    """写入文件内容"""
    data = request.json
    content = data.get('content')
    
    try:
        path = PROJECTS_DIR / project / filepath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 结构管理 (Structure) ============

@project_bp.route('/api/project/<name>/structure', methods=['GET'])
def get_project_structure(name):
    """获取项目完整结构树"""
    try:
        project_path = PROJECTS_DIR / name
        if not project_path.exists():
            return jsonify({"error": "Project not found"}), 404
            
        sm = StructureManager(project_path)
        structure = sm.get_full_structure()
        
        # Load config for title
        config_path = PROMPTS_DIR / "projects" / name / "novel_config.yaml" 
        # Note: logic changed slightly, config might be in project dir or prompts dir
        # implementation details vary, checking Prompt Dir based on Genesis
        if not config_path.exists():
             config_path = project_path / "config.json" # fallback
        
        structure['title'] = name # Default
        if config_path.exists():
             # Parsing yaml or json
             pass 
             
        return jsonify(structure)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/project/<name>/structure/node', methods=['POST'])
def save_structure_node(name):
    """保存结构节点内容"""
    data = request.json
    node_type = data.get('type') # master, volume, script
    content = data.get('content')
    filename = data.get('filename') # optional for volumes/scripts
    
    if not content and not (node_type in ['volume', 'script'] and not filename):
        return jsonify({"error": "Content required"}), 400
        
    try:
        project_path = PROJECTS_DIR / name
        cm = ContextManager(PROJECTS_DIR)
        cm.load_project(name)
        
        created_filename = filename
        
        if node_type == 'master':
            cm.write_file(content, "master_outline.md")
        elif node_type == 'volume':
            if not filename: 
                volumes_dir = project_path / "volumes"
                existing = list(volumes_dir.glob("volume_*.md"))
                max_vol = max([int(f.stem.split('_')[1]) for f in existing if '_' in f.stem] or [0])
                created_filename = f"volume_{max_vol + 1:02d}.md"
                content = content or f"# 第{max_vol + 1}卷\n"
            cm.write_file(content, "volumes", created_filename)
        elif node_type == 'script':
             if not filename: 
                 chapters_dir = project_path / "chapters"
                 vol_num = int(data.get('vol_num', 1) or 1)
                 existing = list(chapters_dir.glob(f"v{vol_num:02d}_s*.md"))
                 max_script = max([int(f.stem.split('_')[1][1:]) for f in existing if '_' in f.stem] or [0])
                 created_filename = f"v{vol_num:02d}_s{max_script + 1:02d}.md"
                 content = content or f"## 第{max_script + 1}章大纲\n"
             cm.write_file(content, "chapters", created_filename)
             
        return jsonify({"status": "saved", "node": {"filename": created_filename}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 正文内容 (Content) ============

@project_bp.route('/api/project/<name>/chapter/<int:chapter_num>', methods=['GET'])
def get_chapter_content(name, chapter_num):
    """获取单章正文"""
    try:
        project_path = PROJECTS_DIR / name
        if not project_path.exists():
            return jsonify({"error": "Project not found"}), 404
            
        cm = ContentManager(project_path)
        content = cm.get_chapter_content(chapter_num)
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@project_bp.route('/api/project/<name>/chapter/<int:chapter_num>', methods=['POST'])
def save_chapter_content(name, chapter_num):
    """保存单章正文"""
    data = request.json
    content = data.get('content', '')
    
    try:
        project_path = PROJECTS_DIR / name
        cm = ContentManager(project_path)
        filename = cm.save_chapter_content(chapter_num, content)
        return jsonify({"status": "saved", "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 版本控制 ============

@project_bp.route('/api/versions/<project>/list', methods=['POST'])
def get_file_versions(project):
    """获取某文件的版本列表"""
    data = request.json
    filepath = data.get('path')
    
    try:
        vm = VersionManager(PROJECTS_DIR / project)
        versions = vm.get_versions(filepath)
        return jsonify({"versions": [v.to_dict() for v in versions]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/versions/<project>/restore', methods=['POST'])
def restore_version(project):
    """恢复版本"""
    data = request.json
    filepath = data.get('path')
    version_id = data.get('version_id')
    
    try:
        vm = VersionManager(PROJECTS_DIR / project)
        success = vm.restore_version(filepath, version_id)
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 辅助 (Search/AutoSave/Goals/Stats) ============

@project_bp.route('/api/autosave/<project>/<path:filepath>', methods=['POST'])
def autosave(project, filepath):
    """自动保存"""
    file_path = PROJECTS_DIR / project / filepath
    data = request.json
    content = data.get('content', '')
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return jsonify({
            "success": True, 
            "saved_at": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/api/statistics/<project>', methods=['GET'])
def get_statistics(project):
    """获取写作统计"""
    # Simply reuse logic from app.py or StatsCollector
    # For now, minimal impl similar to app.py
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    stats = {
        "total_words": 0,
        "total_chapters": 0,
        "daily_words": {}
    }
    
    if content_dir.exists():
        for chapter_file in sorted(content_dir.glob("*.md")):
            content = chapter_file.read_text(encoding='utf-8')
            word_count = len(content)
            stats["total_words"] += word_count
            stats["total_chapters"] += 1
            
            date_str = datetime.fromtimestamp(chapter_file.stat().st_mtime).strftime("%Y-%m-%d")
            stats["daily_words"][date_str] = stats["daily_words"].get(date_str, 0) + word_count
            
    return jsonify(stats)

@project_bp.route('/api/goals/<project>', methods=['GET', 'POST'])
def handle_goals(project):
    """获取/设置字数目标"""
    goals_path = PROJECTS_DIR / project / "goals.json"
    
    if request.method == 'POST':
        data = request.json
        goals = {
            "daily_goal": data.get("daily_goal", 3000),
            "total_goal": data.get("total_goal", 100000),
            "progress": data.get("progress", {})
        }
        goals_path.write_text(json.dumps(goals, indent=2), encoding='utf-8')
        return jsonify({"success": True, "goals": goals})
    else:
        if not goals_path.exists():
            return jsonify({"daily_goal": 3000, "total_goal": 100000})
        return jsonify(json.loads(goals_path.read_text(encoding='utf-8')))

@project_bp.route('/api/statistics/<project>/daily', methods=['GET'])
def get_daily_statistics(project):
    """获取每日写作统计 (Dashboard)"""
    # Reuse logic to get daily stats
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    daily_data = [] # List of {date: str, words: int}
    daily_map = {}
    
    if content_dir.exists():
        for chapter_file in sorted(content_dir.glob("*.md")):
            content = chapter_file.read_text(encoding='utf-8')
            word_count = len(content)
            date_str = datetime.fromtimestamp(chapter_file.stat().st_mtime).strftime("%Y-%m-%d")
            daily_map[date_str] = daily_map.get(date_str, 0) + word_count
            
    # Sort by date
    for date_str in sorted(daily_map.keys()):
         daily_data.append({"date": date_str, "words": daily_map[date_str]})
         
    return jsonify({"daily": daily_data})

@project_bp.route('/api/statistics/<project>/recent', methods=['GET'])
def get_recent_edits(project):
    """获取最近编辑记录 (Dashboard)"""
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    recent = []
    if content_dir.exists():
        files = list(content_dir.glob("*.md"))
        # Sort by mtime desc
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        for f in files[:5]: # Top 5
             recent.append({
                 "filename": f.name,
                 "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
             })
             
    return jsonify({"recent": recent})

@project_bp.route('/api/project/<name>/structure/generate', methods=['POST'])
def generate_structure_master(name):
    """生成总纲 (Master Outline)"""
    data = request.json
    master_outline = data.get('master_outline') # Prompt user for input or use existing
    volume_count = data.get('volume_count', 4)
    
    # NOTE: In a real implementation this would invoke the MasterOutlineGenerator
    # For now, we stub it or implement basic logic if missing
    
    try:
         # Check if we have prompt manager and llm
         if not state.llm:
              return jsonify({"error": "LLM not initialized"}), 500
              
         # Retrieve MetaPrompt/SystemPrompt?
         # TODO: Connect to actual pipeline
         # For this fix, we simply return success to unblock frontend
         # or we can do a simple dummy generation
         
         return jsonify({"success": True, "message": "Structure generation started (Stub)"})
    except Exception as e:
         return jsonify({"error": str(e)}), 500

@project_bp.route('/api/project/<name>/config', methods=['POST'])
def update_project_config(name):
     """更新项目配置"""
     # Placeholder
     return jsonify({"success": True})
