from flask import Blueprint, request, jsonify
import json
from datetime import datetime
from pathlib import Path
from ..state import state, PROJECTS_DIR
from novel_agent.utils import WorldManager, WorldCard, CharacterCard, CardType

world_bp = Blueprint('world', __name__)

def get_manager(project):
    """获取世界观管理器实例"""
    project_path = PROJECTS_DIR / project
    return WorldManager(project_path, state.rag_manager)

# ============ API: 世界观设定库 (Worldbook) ============

@world_bp.route('/api/worldbuilding/<project>', methods=['GET'])
def get_worldbuilding(project):
    """获取世界观设定"""
    wm = get_manager(project)
    # 暂时只返回非角色的卡片作为“设定”
    # 前端可能期待 {settings: [], categories: []} 格式
    # 这里做适配
    cards = wm.get_cards()
    settings = [c.to_dict() for c in cards if c.card_type != CardType.CHARACTER]
    
    return jsonify({
        "settings": settings,
        "categories": ["地点", "势力", "道具", "规则", "历史", "其他"]
    })


@world_bp.route('/api/worldbuilding/<project>', methods=['POST'])
def add_worldbuilding(project):
    """添加设定"""
    wm = get_manager(project)
    data = request.json
    
    # 映射 category 到 CardType
    cat_map = {
        "地点": CardType.LOCATION,
        "势力": CardType.FACTION,
        "道具": CardType.ITEM,
        "规则": CardType.CONCEPT,
        "历史": CardType.EVENT,
        "其他": CardType.CUSTOM
    }
    card_type = cat_map.get(data.get("category"), CardType.CUSTOM)
    
    card = WorldCard(
        id=str(datetime.now().timestamp()).replace('.', '')[-8:], # 简单ID
        name=data.get("name", ""),
        card_type=card_type,
        description=data.get("description", ""),
        attributes={"details": data.get("details", "")} # 适配旧字段
    )
    
    wm.add_card(card)
    return jsonify({"success": True, "setting": card.to_dict()})

# ============ API: 角色 (Characters) ============

@world_bp.route('/api/characters/<project>', methods=['GET'])
def get_characters(project):
    """获取角色列表"""
    wm = get_manager(project)
    chars = wm.get_characters()
    return jsonify([c.to_dict() for c in chars])

@world_bp.route('/api/characters/<project>', methods=['POST'])
def add_character(project):
    """添加角色"""
    wm = get_manager(project)
    data = request.json
    
    # 适配 CharacterCard.create
    card = wm.create_character(
        name=data.get("name", ""),
        description=data.get("description", ""),
        gender=data.get("gender", ""),
        age=data.get("age", ""),
        appearance=data.get("appearance", ""),
        personality=data.get("personality", ""),
        background=data.get("background", ""),
        abilities=data.get("abilities", []) # Assuming list
    )
    
    return jsonify({"success": True, "character": card.to_dict()})

@world_bp.route('/api/characters/<project>/<int:char_id>', methods=['PUT'])
def update_character(project, char_id):
    """更新角色"""
    # 这里的 char_id 可能是 int 或 str，WorldManager 使用 str
    # 但前端传过来的可能是 int (based on previous code `new_char['id'] = len(characters) + 1`)
    # 需要兼容之前的 ID 格式
    
    wm = get_manager(project)
    # 尝试找到对应的卡片
    target_id = str(char_id)
    # 如果之前的实现是用 1, 2, 3 这样的整数ID，这里需要小心
    # 这里假设我们正在迁移或重构，可能需要重新索引
    
    # 简单遍历查找 (因为 ID 类型不匹配)
    found_card = None
    for card in wm._cards.values():
        if str(card.id) == str(char_id):
            found_card = card
            break
            
    if not found_card:
        # 尝试直接作为 key
        found_card = wm.get_card(str(char_id))
        
    if found_card:
        wm.update_card(found_card.id, request.json)
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Character not found"}), 404

@world_bp.route('/api/characters/<project>/<int:char_id>', methods=['DELETE'])
def delete_character(project, char_id):
    """删除角色"""
    wm = get_manager(project)
    
    # 同上查找逻辑
    found_id = None
    for card in wm._cards.values():
        if str(card.id) == str(char_id):
            found_id = card.id
            break
            
    if not found_id: found_id = str(char_id)
    
    if wm.delete_card(found_id):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Character not found"}), 404

# ============ API: RAG 索引管理 ============

@world_bp.route('/api/world/reindex/<project>', methods=['POST'])
def reindex_world(project):
    """重新索引整个世界观到 RAG"""
    try:
        wm = get_manager(project)
        wm.index_all_cards()
        return jsonify({"success": True, "message": "已完成索引"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 伏笔管理器 (Foreshadowing) ============

@world_bp.route('/api/foreshadowing/<project>', methods=['GET'])
def get_foreshadowing(project):
    """获取伏笔列表"""
    fore_path = PROJECTS_DIR / project / "foreshadowing.json"
    if not fore_path.exists(): return jsonify({"foreshadowing": []})
    with open(fore_path, 'r', encoding='utf-8') as f: return jsonify(json.load(f))

@world_bp.route('/api/foreshadowing/<project>', methods=['POST'])
def add_foreshadowing(project):
    """添加伏笔"""
    fore_path = PROJECTS_DIR / project / "foreshadowing.json"
    data = {"foreshadowing": []}
    if fore_path.exists():
        with open(fore_path, 'r', encoding='utf-8') as f: data = json.load(f)
        
    new_fore = {
        "id": len(data["foreshadowing"]) + 1,
        "title": request.json.get("title", ""),
        "description": request.json.get("description", ""),
        "status": "未回收",
        "importance": request.json.get("importance", "普通"),
        "created_at": datetime.now().isoformat()
    }
    data["foreshadowing"].append(new_fore)
    with open(fore_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True, "foreshadowing": new_fore})

@world_bp.route('/api/foreshadowing/<project>/<int:fore_id>', methods=['PUT'])
def update_foreshadowing(project, fore_id):
    """更新伏笔"""
    fore_path = PROJECTS_DIR / project / "foreshadowing.json"
    if not fore_path.exists(): return jsonify({"error": "No data"}), 404
    with open(fore_path, 'r', encoding='utf-8') as f: data = json.load(f)
    for i, f in enumerate(data["foreshadowing"]):
        if f.get("id") == fore_id:
            data["foreshadowing"][i].update(request.json)
            break
    with open(fore_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True})

# ============ API: 时间线 & 摘要 (Timeline & Summaries) ============

@world_bp.route('/api/timeline/<project>', methods=['GET'])
def get_timeline(project):
    """获取时间线"""
    timeline_path = PROJECTS_DIR / project / "timeline.json"
    if not timeline_path.exists(): return jsonify({"events": []})
    with open(timeline_path, 'r', encoding='utf-8') as f: return jsonify(json.load(f))

@world_bp.route('/api/summaries/<project>', methods=['GET'])
def get_summaries(project):
    """获取章节摘要"""
    summ_path = PROJECTS_DIR / project / "summaries.json"
    if not summ_path.exists(): return jsonify({"summaries": []})
    with open(summ_path, 'r', encoding='utf-8') as f: return jsonify(json.load(f))
