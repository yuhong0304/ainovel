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

# ============ API: 统一卡片接口 (Worldbook Unified) ============

@world_bp.route('/api/world/<project>/cards', methods=['GET'])
def get_all_cards(project):
    """获取所有世界观卡片 (角色 + 设定)"""
    try:
        wm = get_manager(project)
        cards = wm.get_cards() # Should return all cards
        
        # Ensure category field is present for frontend
        result = []
        for c in cards:
            d = c.to_dict()
            if 'category' not in d:
                # Map type to category
                type_map = {
                    CardType.CHARACTER: 'character',
                    CardType.LOCATION: 'location',
                    CardType.FACTION: 'faction',
                    CardType.ITEM: 'item',
                    CardType.CONCEPT: 'lore',
                    CardType.EVENT: 'history'
                }
                d['category'] = type_map.get(c.card_type, 'other')
            result.append(d)
            
        return jsonify({"cards": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@world_bp.route('/api/world/<project>/cards', methods=['POST'])
def add_card(project):
    """添加卡片"""
    try:
        wm = get_manager(project)
        data = request.json
        category = data.get('category', 'other')
        
        # Map category to CardType
        cat_map = {
            'character': CardType.CHARACTER,
            'location': CardType.LOCATION,
            'faction': CardType.FACTION,
            'item': CardType.ITEM,
            'lore': CardType.CONCEPT,
            'history': CardType.EVENT
        }
        card_type = cat_map.get(category, CardType.CUSTOM)
        
        if card_type == CardType.CHARACTER:
             # Character fields
             card = wm.create_character(
                name=data.get("name", ""),
                description=data.get("description", ""),
                gender=data.get("gender", ""),
                age=data.get("age", ""),
                appearance=data.get("appearance", ""),
                personality=data.get("personality", ""),
                background=data.get("background", ""),
                abilities=data.get("abilities", [])
            )
        else:
            # Other cards
             card = WorldCard(
                id=str(datetime.now().timestamp()).replace('.', '')[-8:],
                name=data.get("name", ""),
                card_type=card_type,
                description=data.get("description", ""),
                attributes={"details": data.get("details", "")}
            )
             wm.add_card(card)
             
        # Return formatted for frontend
        d = card.to_dict()
        d['category'] = category
        return jsonify({"success": True, "card": d})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@world_bp.route('/api/world/<project>/cards/<card_id>', methods=['PUT'])
def update_card(project, card_id):
    """更新卡片"""
    try:
        wm = get_manager(project)
        data = request.json
        if wm.update_card(card_id, data):
             # Return updated card
             card = wm.get_card(card_id)
             d = card.to_dict()
             # Re-inject category if missing (utils might not store it explicitly same way)
             if 'category' not in d:
                 # Simplified mapping back
                 type_map = {
                    CardType.CHARACTER: 'character',
                    CardType.LOCATION: 'location',
                    CardType.FACTION: 'faction',
                    CardType.ITEM: 'item',
                    CardType.CONCEPT: 'lore',
                    CardType.EVENT: 'history'
                 }
                 d['category'] = type_map.get(card.card_type, 'other')
             return jsonify({"success": True, "card": d})
        else:
             return jsonify({"error": "Card not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@world_bp.route('/api/world/<project>/cards/<card_id>', methods=['DELETE'])
def delete_card(project, card_id):
    """删除卡片"""
    try:
        wm = get_manager(project)
        if wm.delete_card(card_id):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Card not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@world_bp.route('/api/world/<project>/extract', methods=['POST'])
def extract_world_info(project):
    """从正文提取世界观"""
    try:
        # Stub for now, or implement using simple keyword extraction
        # Real implementation would use LLM
        return jsonify({"extracted": []}) 
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
