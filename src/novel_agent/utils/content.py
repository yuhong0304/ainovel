
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class ContentManager:
    """
    正文内容管理器
    
    功能:
    - 管理正文文件 (content/chapter_XXXX.md)
    - 关联正文与大纲 (vXX_sXX.md)
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.content_dir = project_path / "content"
        self.chapters_dir = project_path / "chapters"
        
        # Ensure dirs exist
        if not self.content_dir.exists():
            self.content_dir.mkdir(parents=True, exist_ok=True)

    def list_chapters(self) -> List[Dict[str, Any]]:
        """
        列出所有章节
        
        返回:
        [
            {
                "chapter_num": 1,
                "title": "...",
                "has_content": True,
                "word_count": 3000,
                "outline_file": "v01_s01.md" (关联的细纲)
            },
            ...
        ]
        """
        chapters_map = {}
        
        # 1. Scan generated content
        if self.content_dir.exists():
            for f in self.content_dir.glob("chapter_*.md"):
                try:
                    # chapter_0001.md
                    num = int(f.stem.split('_')[1])
                    content = f.read_text(encoding='utf-8')
                    title = self._extract_title(content)
                    
                    chapters_map[num] = {
                        "chapter_num": num,
                        "title": title,
                        "has_content": True,
                        "word_count": len(content),
                        "filename": f.name
                    }
                except Exception as e:
                    print(f"Error reading {f}: {e}")
                    continue
        
        # 2. Scan outlines to find potential chapters (if not yet generated)
        # 这是一个难点：细纲 (Script) 通常包含 3 个章节。
        # 我们这里暂时只列出 "已生成的内容" 或 "预期存在的章节"
        # 简单起见，我们目前只列出 *文件系统里存在的正文文件*
        # 但为了让用户能 "新建" 章节，我们需要一种方式知道总共有多少章。
        # 暂时策略：只返回已存在的，前端负责 "新建" (即调用生成或新建文件)
        
        # Convert to sorted list
        result = sorted(chapters_map.values(), key=lambda x: x['chapter_num'])
        
        return result

    def get_chapter_content(self, chapter_num: int) -> str:
        """获取章节内容"""
        f = self.content_dir / f"chapter_{chapter_num:04d}.md"
        if f.exists():
            return f.read_text(encoding='utf-8')
        return ""
    
    def save_chapter_content(self, chapter_num: int, content: str) -> str:
        """保存章节内容"""
        filename = f"chapter_{chapter_num:04d}.md"
        f = self.content_dir / filename
        f.write_text(content, encoding='utf-8')
        return filename

    def _extract_title(self, content: str) -> str:
        """从内容提取标题 (# Title)"""
        first_line = content.split('\n')[0].strip()
        if first_line.startswith('# '):
            return first_line.replace('# ', '')
        return f"Chapter {content[:10]}..."
