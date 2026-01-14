
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class StructureManager:
    """
    结构管理器
    
    功能:
    - 聚合项目的所有结构文件 (Total Outline, Volume, Chapter)
    - 提供统一的树状结构数据供前端展示
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.volumes_dir = project_path / "volumes"
        self.chapters_dir = project_path / "chapters"
    
    def get_full_structure(self) -> Dict[str, Any]:
        """获取完整项目结构树"""
        
        # 1. 基础信息 from config (assumed loaded elsewhere, or we read master outline)
        master_content = self._read_file("master_outline.md")
        
        # 2. 扫描卷 (volumes/volume_XX.md)
        volumes = []
        if self.volumes_dir.exists():
            vol_files = sorted(self.volumes_dir.glob("volume_*.md"))
            for vf in vol_files:
                vol_num = self._extract_number(vf.name)
                content = vf.read_text(encoding="utf-8")
                
                # 扫描该卷下的剧本/章节 (chapters/vXX_sXX.md)
                scripts = self._get_volume_scripts(vol_num)
                
                volumes.append({
                    "vol_num": vol_num,
                    "filename": vf.name,
                    "title": self._extract_title(content) or f"第{vol_num}卷",
                    "content": content,
                    "scripts": scripts
                })
        
        return {
            "master_outline": master_content,
            "volumes": volumes
        }
    
    def _get_volume_scripts(self, vol_num: int) -> List[Dict]:
        """获取指定卷的剧本/细纲列表"""
        scripts = []
        if self.chapters_dir.exists():
            # Pattern: vXX_sXX.md (Volume XX, Script XX)
            pattern = f"v{vol_num:02d}_s*.md"
            script_files = sorted(self.chapters_dir.glob(pattern))
            
            for sf in script_files:
                # v01_s01.md -> script_num = 1
                script_num = self._extract_script_number(sf.name)
                content = sf.read_text(encoding="utf-8")
                
                scripts.append({
                    "script_num": script_num,
                    "filename": sf.name,
                    "title": self._extract_title(content) or f"剧本 {script_num}",
                    "content": content
                })
        return scripts

    def _read_file(self, filename: str) -> str:
        f = self.project_path / filename
        if f.exists():
            return f.read_text(encoding="utf-8")
        return ""

    def _extract_number(self, filename: str) -> int:
        """extract number from volume_01.md"""
        try:
            # volume_01.md -> 01
            return int(re.search(r'\d+', filename).group())
        except:
            return 0
            
    def _extract_script_number(self, filename: str) -> int:
        """extract script number from v01_s02.md -> 2"""
        try:
            match = re.search(r's(\d+)', filename)
            if match:
                return int(match.group(1))
            return 0
        except:
            return 0

    def _extract_title(self, content: str) -> str:
        """Try to extract first header as title"""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line.replace('# ', '').strip()
            if line.startswith('## '): # Fallback
                 return line.replace('## ', '').strip()
        return ""
