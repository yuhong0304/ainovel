from flask import Blueprint, request, jsonify, Response, send_from_directory
import zipfile
import io
from ..state import state, PROJECTS_DIR
from novel_agent.utils import NovelExporter

export_bp = Blueprint('export', __name__)

# ============ API: 导出 ============

@export_bp.route('/api/export/<project>/zip', methods=['GET'])
def export_zip(project):
    """打包导出ZIP"""
    project_path = PROJECTS_DIR / project
    
    if not project_path.exists():
        return jsonify({"error": "项目不存在"}), 404
    
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

@export_bp.route('/api/export/txt', methods=['POST'])
def export_txt():
    """导出为 TXT"""
    data = request.json
    project = data.get('project')
    
    try:
        exporter = NovelExporter(PROJECTS_DIR / project)
        path = exporter.export_txt()
        
        filename = path.name
        return jsonify({
            "success": True,
            "url": f"/api/download/{project}/{filename}",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@export_bp.route('/api/export/docx', methods=['POST'])
def export_docx():
    """导出为 DOCX"""
    data = request.json
    project = data.get('project')
    
    try:
        exporter = NovelExporter(PROJECTS_DIR / project)
        path = exporter.export_docx()
        
        filename = path.name
        return jsonify({
            "success": True,
            "url": f"/api/download/{project}/{filename}",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@export_bp.route('/api/export/epub', methods=['POST'])
def export_epub():
    """导出为 EPUB"""
    data = request.json
    project = data.get('project')
    
    try:
        exporter = NovelExporter(PROJECTS_DIR / project)
        path = exporter.export_epub()
        
        filename = path.name
        return jsonify({
            "success": True,
            "url": f"/api/download/{project}/{filename}",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@export_bp.route('/api/export/<project>/merge', methods=['POST'])
def export_merged(project):
    """合并导出章节"""
    data = request.json
    chapters = data.get("chapters", [])  # 章节列表
    format_type = data.get("format", "txt")  # txt/md
    
    project_path = PROJECTS_DIR / project
    content_dir = project_path / "content"
    
    merged = ""
    # 简单过滤
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

@export_bp.route('/api/download/<project>/<filename>')
@export_bp.route('/api/export/<project>/download/<filename>') # Alias for frontend match
def download_file(project, filename):
    """下载导出文件"""
    # Exporter usually saves to {project}/export or {project}/exports
    # Check both or configure Exporter to standard location
    # NovelExporter default is usually just inside project or subdirectory
    
    # Assuming "exports" folder based on previous app.py
    export_dir = PROJECTS_DIR / project / "exports"
    if not export_dir.exists():
         # Fallback to "export" or base dir
         if (PROJECTS_DIR / project / "export").exists():
              export_dir = PROJECTS_DIR / project / "export"
         else:
              export_dir = PROJECTS_DIR / project
              
    return send_from_directory(export_dir, filename, as_attachment=True)
