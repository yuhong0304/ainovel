from flask import Blueprint, request, jsonify, Response
import queue
import threading
import json
import uuid
from datetime import datetime
from ..state import state, PROJECTS_DIR
from novel_agent.pipeline.stage_4_content import ContentGenerator

gen_bp = Blueprint('generation', __name__)

# ============ API: 通用生成 (Generation) ============

@gen_bp.route('/api/generate/stream', methods=['POST'])
def generate_stream():
    """流式生成（SSE） - 修复版 (合并了原 app.py 中的两个定义)"""
    data = request.json
    project = data.get('project')
    stage = data.get('stage', 'content')  # 默认为 content
    params = data.get('params', {})
    
    # 兼容简单的Prompt模式 (如果是旧的前端调用)
    if 'prompt' in params and 'outline' not in params:
        params['outline'] = params['prompt']

    # 创建进度队列
    queue_id = f"{project}_{stage}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:6]}"
    progress_queue = queue.Queue()
    state.progress_queues[queue_id] = progress_queue
    
    # 启动后台生成
    def generate_task():
        try:
            progress_queue.put({"type": "start", "message": f"开始{stage}生成..."})
            
            # 确保项目已加载
            state.context_manager.load_project(project)
            
            if stage == "content":
                content_gen = ContentGenerator(
                    state.llm, state.prompt_manager, state.context_manager, state.rag_manager
                )
                
                # 流式生成
                full_content = ""
                # outline 可能是直接传的 content，也可能是为了防止为空做的 fallback
                outline = params.get('outline', '')
                
                for chunk in content_gen.generate_stream(
                    chapter_outline=outline,
                    previous_summary=params.get('previous_summary', ''),
                    character_status=params.get('character_status', '')
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
            
            elif stage == "chat":
                 # 简单的聊天生成
                 prompt = params.get('message', '')
                 full_content = ""
                 for chunk in state.llm.generate_stream(prompt, config=state.get_llm_config()):
                     full_content += chunk
                     progress_queue.put({
                        "type": "chunk",
                        "content": chunk
                     })
                 progress_queue.put({"type": "complete", "content": full_content})

            else:
                # 其他阶段暂时使用通用生成 (TODO: 适配 Meta/Master/Volume Generator)
                # 暂时报错或者fallback
                progress_queue.put({"type": "error", "message": f"暂不支持流式生成的阶段: {stage}"})
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            progress_queue.put({"type": "error", "message": str(e)})
        finally:
            progress_queue.put({"type": "done"})
    
    thread = threading.Thread(target=generate_task)
    thread.start()
    
    return jsonify({"queue_id": queue_id})


@gen_bp.route('/api/generate/progress/<queue_id>')
def get_progress(queue_id):
    """获取生成进度（SSE）"""
    def event_stream():
        if queue_id not in state.progress_queues:
            yield f"data: {json.dumps({'type': 'error', 'message': '无效的队列ID'})}\n\n"
            return
        
        progress_queue = state.progress_queues[queue_id]
        
        while True:
            try:
                # 阻塞等待消息
                event = progress_queue.get(timeout=60)
                yield f"data: {json.dumps(event)}\n\n"
                
                if event.get('type') in ['done', 'error']:
                    # 清理 (稍微延迟一下防止前端没收到 done?) 
                    # 其实这里 break 后函数结束，也不需要额外清理，
                    # 但为了 map 不无限增长，需要 del
                    # 可以在外层做个定时清理，这里先同步删
                    # del state.progress_queues[queue_id] # 可能会导致重连失败，暂保留由定期清理或前端断开处理
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no' # Nginx buffering off
        }
    )


# ============ API: 同步生成 endpoints ============

@gen_bp.route('/api/generate/meta', methods=['POST'])
def generate_meta():
    """生成元数据/灵感分析 (同步)"""
    # 逻辑移入 api/project.py 的 genesis，或者保留在这里供非Wizard使用
    # 这里暂时保留为空，或者复用 MetaPromptGenerator
    return jsonify({"error": "请使用 /api/genesis 相关接口"}), 400

@gen_bp.route('/api/chat', methods=['POST'])
def chat():
    """AI 助手对话"""
    data = request.json
    message = data.get('message')
    history = data.get('history', [])
    project = data.get('project')
    
    if not message:
        return jsonify({"error": "消息不能为空"}), 400
        
    try:
        if project:
            state.context_manager.load_project(project)
            
        # 简单构建对话 Prompt
        # TODO: 使用 ContextManager 构建更丰富的上下文
        prompt = f"用户: {message}\n\nAI:"
        
        # 简单生成
        result = state.llm.generate(prompt, config=state.get_llm_config())
        
        return jsonify({"reply": result.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API: 批量生成 (Batch) ============

@gen_bp.route('/api/batch/create', methods=['POST'])
def batch_create():
    """创建批量任务"""
    data = request.json
    project = data.get('project')
    start_chapter = int(data.get('start', 1))
    end_chapter = int(data.get('end', 1))
    titles = data.get('titles', [])
    
    try:
        state.context_manager.load_project(project)
        
        from novel_agent.utils.batch import BatchGenerator
        batch_gen = BatchGenerator(
            state.llm, state.prompt_manager, state.context_manager,
            PROJECTS_DIR / project
        )
        
        job = batch_gen.create_job(start_chapter, end_chapter, titles)
        
        state.batch_jobs[job.job_id] = {
            "job": job,
            "generator": batch_gen
        }
        
        return jsonify({
            "success": True,
            "job_id": job.job_id,
            "job": batch_gen._job_to_dict(job)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gen_bp.route('/api/batch/progress/<job_id>', methods=['GET'])
def batch_progress(job_id):
    """批量生成进度 (SSE)"""
    if job_id not in state.batch_jobs:
        # Initial check, might be race condition if just created
        # But usually Create returns ID then FE connects
        return jsonify({"error": "任务不存在"}), 404
        
    job_info = state.batch_jobs[job_id]
    job = job_info['job']
    generator = job_info['generator']
    
    def generate():
        try:
             # Run generator.run_job() which yields updates
             # Note: run_job is a generator that executes one step per yield
             # This blocks the thread, so Flask threaded=True is needed (which is default)
            for update in generator.run_job(job):
                yield f"data: {json.dumps(update)}\n\n"
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
