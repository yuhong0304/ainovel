from flask import Blueprint, request, jsonify
from ..state import state, PROJECTS_DIR
from novel_agent.pipeline.stage_6_learn import RuleLearner

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/api/learn/feedback', methods=['POST'])
def learn_from_feedback():
    """
    从用户反馈/修改中学习规则
    Accepts: {
        "project": str,
        "original": str,
        "edited": str
    }
    """
    data = request.json
    project = data.get('project')
    original = data.get('original')
    edited = data.get('edited')
    
    if not project or not original or not edited:
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        # Load project context
        state.context_manager.load_project(project)
        
        learner = RuleLearner(
            state.llm,
            state.prompt_manager,
            state.context_manager
        )
        
        # Analyze diff
        new_rules = learner.analyze_changes(original, edited)
        
        if "无新规则" in new_rules:
             return jsonify({
                 "success": True,
                 "learned": False,
                 "message": "未发现显著修改模式"
             })
             
        # Save rules
        state.prompt_manager.append_learned_rule(new_rules)
        
        return jsonify({
            "success": True,
            "learned": True,
            "rules": new_rules
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@learning_bp.route('/api/learn/rules', methods=['GET'])
def get_rules():
    """获取所有已学习规则"""
    try:
        rules = state.prompt_manager.get_learned_rules(force_reload=True)
        return jsonify({"rules": rules})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
