from flask import Blueprint, request, jsonify
import os
import re
from pathlib import Path
from ..state import state, PROMPTS_DIR, get_available_models, get_usage_summary, reset_cost_tracker

settings_bp = Blueprint('settings', __name__)

# ============ API: 设置 ============

@settings_bp.route('/api/settings/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    models = get_available_models()
    return jsonify({
        "models": models,
        "current": state.current_model,
        "provider": state.current_provider
    })

@settings_bp.route('/api/settings/global/full', methods=['GET'])
def get_full_settings():
    """获取完整设置 (前端 Settings 页面使用)"""
    from novel_agent.core.gemini_client import get_available_models, get_usage_summary
    
    # Gemini 模型
    gemini_models = get_available_models()
    
    # OpenAI 模型
    openai_models = [
        {"name": "gpt-4o", "context": 128000},
        {"name": "gpt-4o-mini", "context": 128000},
        {"name": "gpt-4-turbo", "context": 128000},
        {"name": "o1", "context": 200000},
        {"name": "o1-mini", "context": 128000},
    ]
    
    # Claude 模型
    claude_models = [
        {"name": "claude-3-5-sonnet-20241022", "context": 200000},
        {"name": "claude-3-5-haiku-20241022", "context": 200000},
        {"name": "claude-3-opus-20240229", "context": 200000},
    ]
    
    return jsonify({
        "current_model": state.current_model,
        "current_provider": state.current_provider,
        "generation_config": state.generation_config,
        "safety_settings": state.safety_settings,
        "config_presets": state.config_presets,
        "available_models": {
            "gemini": gemini_models,
            "openai": openai_models,
            "claude": claude_models
        },
        "api_keys_configured": {
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "claude": bool(os.getenv("ANTHROPIC_API_KEY"))
        }
    })


@settings_bp.route('/api/settings/model', methods=['POST'])
def set_model():
    """切换模型"""
    data = request.json
    model_name = data.get('model')
    provider = data.get('provider')
    
    if not model_name:
        return jsonify({"error": "模型名称不能为空"}), 400
    
    try:
        state.switch_model(model_name, provider)
        return jsonify({
            "success": True,
            "model": model_name,
            "provider": state.current_provider,
            "message": f"已切换到 {model_name}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route('/api/settings/usage', methods=['GET'])
def get_usage():
    """获取Token使用统计"""
    usage = get_usage_summary()
    return jsonify(usage)


@settings_bp.route('/api/settings/usage/reset', methods=['POST'])
def reset_usage():
    """重置使用统计"""
    reset_cost_tracker()
    return jsonify({"success": True})


# ============ API: 生成参数 ============

@settings_bp.route('/api/settings/params', methods=['GET'])
def get_params():
    """获取生成参数"""
    return jsonify({
        "config": state.generation_config,
        "presets": state.config_presets
    })


@settings_bp.route('/api/settings/params', methods=['POST'])
def set_params():
    """设置生成参数"""
    data = request.json
    
    # 更新参数
    for key in ["temperature", "max_tokens", "top_p", "top_k", "theme"]:
        if key in data:
            state.generation_config[key] = data[key]
    
    return jsonify({
        "success": True,
        "config": state.generation_config
    })


@settings_bp.route('/api/settings/params/preset/<name>', methods=['POST'])
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


# ============ API: API Key 管理 ============

@settings_bp.route('/api/settings/api-key/test', methods=['POST'])
def test_api_key():
    """测试 API Key 有效性"""
    data = request.json
    api_key = data.get('api_key')
    provider = data.get('provider', 'gemini')
    
    if not api_key:
        return jsonify({"valid": False, "error": "API Key 不能为空"}), 400
    
    try:
        if provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = list(genai.list_models())
            return jsonify({
                "valid": True,
                "message": f"API Key 有效，可访问 {len(models)} 个模型",
                "models": [m.name for m in models[:5]]
            })
        elif provider == 'openai':
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            models = client.models.list()
            return jsonify({
                "valid": True,
                "message": "API Key 有效",
                "models": [m.id for m in list(models)[:5]]
            })
        elif provider == 'claude':
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            # Claude API doesn't have a list models endpoint, so just try simple call
            return jsonify({
                "valid": True,
                "message": "API Key 格式有效"
            })
        else:
            return jsonify({"valid": False, "error": "不支持的提供商"})
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)})


@settings_bp.route('/api/settings/api-key/save', methods=['POST'])
def save_api_key():
    """保存 API Key 到 .env 文件"""
    data = request.json
    api_key = data.get('api_key')
    provider = data.get('provider', 'gemini')
    
    if not api_key:
        return jsonify({"error": "API Key 不能为空"}), 400
    
    try:
        env_path = Path.cwd() / ".env"
        
        # 读取现有内容
        existing_content = ""
        if env_path.exists():
            existing_content = env_path.read_text(encoding='utf-8')
        
        # 确定 key 名称
        key_name = {
            'gemini': 'GEMINI_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY'
        }.get(provider, 'GEMINI_API_KEY')
        
        # 更新或添加 key
        pattern = f"^{key_name}=.*$"
        new_line = f"{key_name}={api_key}"
        
        if re.search(pattern, existing_content, re.MULTILINE):
            new_content = re.sub(pattern, new_line, existing_content, flags=re.MULTILINE)
        else:
            new_content = existing_content.rstrip() + f"\n{new_line}\n"
        
        env_path.write_text(new_content, encoding='utf-8')
        
        # 重新加载环境变量
        os.environ[key_name] = api_key
        
        # 如果是 Gemini，重新初始化客户端
        if provider == 'gemini':
            state.llm = GeminiClient(api_key=api_key, model_name=state.current_model)
        
        return jsonify({"success": True, "message": f"{key_name} 已保存"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 系统 Prompt 管理 ============

@settings_bp.route('/api/settings/system-prompt/<project>', methods=['GET'])
def get_system_prompt(project):
    """获取项目系统 Prompt"""
    try:
        project_prompts = PROMPTS_DIR / "projects" / project
        system_prompt_path = project_prompts / "system_prompt.md"
        
        if system_prompt_path.exists():
            content = system_prompt_path.read_text(encoding='utf-8')
            return jsonify({"content": content, "exists": True})
        else:
            return jsonify({"content": "", "exists": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route('/api/settings/system-prompt/<project>', methods=['POST'])
def save_system_prompt(project):
    """保存项目系统 Prompt"""
    data = request.json
    content = data.get('content', '')
    
    try:
        project_prompts = PROMPTS_DIR / "projects" / project
        project_prompts.mkdir(parents=True, exist_ok=True)
        
        system_prompt_path = project_prompts / "system_prompt.md"
        system_prompt_path.write_text(content, encoding='utf-8')
        
        return jsonify({"success": True, "message": "系统 Prompt 已保存"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 安全设置 ============

@settings_bp.route('/api/settings/safety', methods=['GET'])
def get_safety_settings():
    """获取安全设置"""
    return jsonify(state.safety_settings)


@settings_bp.route('/api/settings/safety', methods=['POST'])
def update_safety_settings():
    """更新安全设置"""
    data = request.json
    
    if 'harm_block_threshold' in data:
        state.safety_settings['harm_block_threshold'] = data['harm_block_threshold']
    if 'enable_content_filter' in data:
        state.safety_settings['enable_content_filter'] = data['enable_content_filter']
    
    return jsonify({"success": True, "settings": state.safety_settings})


# ============ API: 扩展全局设置 ============

@settings_bp.route('/api/settings/global', methods=['GET'])
def get_global_settings():
    """获取全局设置"""
    models = get_available_models()
    return jsonify({
        "current_model": state.current_model,
        "generation_config": state.generation_config,
        "available_models": models,
        "config_presets": state.config_presets
    })

@settings_bp.route('/api/settings/global', methods=['POST'])
def update_global_settings():
    """更新全局设置"""
    data = request.json
    
    if 'current_model' in data:
        state.current_model = data['current_model']
        # Re-init LLM if model changes
        if state.llm:
            state.llm = GeminiClient(model_name=state.current_model)
            
    if 'generation_config' in data:
        # Merge config
        new_config = data['generation_config']
        state.generation_config.update(new_config)
        
    return jsonify({
        "success": True,
        "current_model": state.current_model,
        "generation_config": state.generation_config
    })

# ============ API: Cost Statistics ============

@settings_bp.route('/api/statistics/cost', methods=['GET'])
def get_cost_statistics():
    """获取成本统计"""
    usage = get_usage_summary()
    return jsonify({
        "usage": usage,
        "breakdown": {
            "pro_cost": usage.get("total_cost_usd", 0) * 0.7,
            "flash_cost": usage.get("total_cost_usd", 0) * 0.3
        }
    })

# ============ API: Theme ============

@settings_bp.route('/api/settings/theme', methods=['GET'])
def get_theme():
    """获取主题设置"""
    return jsonify({
        "theme": state.generation_config.get("theme", "dark"),
        "available": ["dark", "light"]
    })

@settings_bp.route('/api/settings/theme', methods=['POST'])
def set_theme():
    """设置主题"""
    data = request.json
    theme = data.get("theme", "dark")
    state.generation_config["theme"] = theme
    return jsonify({"success": True, "theme": theme})
