"""
上下文/状态管理器
管理小说项目的状态、进度和记忆
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field, asdict


@dataclass
class ChapterInfo:
    """章节信息"""
    number: int
    title: str = ""
    status: str = "pending"  # pending | outline | drafted | polished | final
    word_count: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class VolumeInfo:
    """卷信息"""
    number: int
    title: str = ""
    chapters: List[ChapterInfo] = field(default_factory=list)
    status: str = "pending"  # pending | outlined | in_progress | completed


@dataclass
class CharacterInfo:
    """角色信息"""
    name: str
    role: str = ""  # protagonist | antagonist | supporting | minor
    description: str = ""
    traits: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectConfig:
    """项目配置"""
    name: str
    title: str = ""
    genre: str = ""
    target_words: int = 0
    words_per_chapter: int = 3000
    current_stage: str = "master_outline"  # master_outline | volume | chapter | content
    current_volume: int = 1
    current_chapter: int = 1
    created_at: str = ""
    updated_at: str = ""
    
    # 内容摘要（用于长篇记忆）
    summary: str = ""
    
    # 结构信息
    volumes: List[VolumeInfo] = field(default_factory=list)
    characters: List[CharacterInfo] = field(default_factory=list)
    
    # 自定义元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    上下文/状态管理器
    
    功能:
    - 管理项目配置和进度
    - 追踪角色和剧情摘要（长篇记忆）
    - 读写项目状态文件
    """
    
    def __init__(self, projects_dir: str):
        """
        初始化上下文管理器
        
        Args:
            projects_dir: 项目存储目录
        """
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_project: Optional[ProjectConfig] = None
        self._current_project_path: Optional[Path] = None
        
        # 初始化RAG管理器
        try:
            from .rag import RAGManager
            self.rag = RAGManager(persistence_dir=str(self.projects_dir))
        except Exception as e:
            print(f"RAG初始化失败: {e}")
            self.rag = None
    
    def list_projects(self) -> List[str]:
        """列出所有项目"""
        projects = []
        for path in self.projects_dir.iterdir():
            if path.is_dir() and (path / "config.json").exists():
                projects.append(path.name)
        return projects
    
    # ... (Keep existing methods until get_context_for_generation) ...
    
    def get_context_for_generation(self) -> Dict[str, Any]:
        """
        获取用于生成的上下文信息 (增强版)
        
        Returns:
            包含所有相关上下文的字典
        """
        if not self._current_project:
            return {}
        
        base_context = {
            "project_name": self._current_project.name,
            "title": self._current_project.title,
            "genre": self._current_project.genre,
            "current_volume": self._current_project.current_volume,
            "current_chapter": self._current_project.current_chapter,
            "summary": self._current_project.summary,
            "characters": self.get_characters_summary(),
            "words_per_chapter": self._current_project.words_per_chapter
        }
        
        # RAG 增强
        if self.rag:
            # 构造查询 query (通常是当前章节意图，这里简单使用标题或摘要)
            query = f"{self._current_project.title} 卷{self._current_project.current_volume} 章{self._current_project.current_chapter}"
            relevant_docs = self.rag.query(query, n_results=3)
            if relevant_docs:
                base_context["rag_context"] = "\n".join(relevant_docs)
        
        return base_context

    def index_current_project(self):
        """索引当前项目的所有数据"""
        if not self._current_project or not self.rag:
            return
            
        docs = []
        metas = []
        ids = []
        
        # 1. 索引人物
        for char in self._current_project.characters:
            text = f"角色: {char.name}\n特征: {char.description}\n性格: {', '.join(char.traits)}"
            docs.append(text)
            metas.append({"type": "character", "name": char.name})
            ids.append(f"char_{char.name}")
            
        # 2. 索引摘要
        if self._current_project.summary:
            docs.append(f"剧情摘要: {self._current_project.summary}")
            metas.append({"type": "summary"})
            ids.append("summary_main")
            
        # 3. 索引已生成章节 (前文)
        content_dir = self.projects_dir / self._current_project.name / "content"
        if content_dir.exists():
            for content_file in content_dir.glob("*.md"):
                # 排除非章节文件
                if not content_file.name.startswith("ch"):
                    continue
                    
                chapter_content = content_file.read_text(encoding="utf-8")
                # 简单分块或整章存入 (这里整章存入，依赖 Chroma 分块或 LLM 上下文处理)
                # 更好的方式是按场景分块，但这里先实现基础功能
                docs.append(f"章节文件 {content_file.name}:\n{chapter_content}")
                metas.append({
                    "type": "chapter_content", 
                    "filename": content_file.name,
                    "project": self._current_project.name
                })
                ids.append(f"content_{self._current_project.name}_{content_file.stem}")
        
        if docs:
            self.rag.add_documents(docs, metas, ids)
            print(f"Index updated: {len(docs)} documents indexed for project {self._current_project.name}")

    
    def create_project(self, name: str, **kwargs) -> ProjectConfig:
        """
        创建新项目
        
        Args:
            name: 项目名称（用作文件夹名）
            **kwargs: 其他配置项
        """
        project_path = self.projects_dir / name
        if project_path.exists():
            raise ValueError(f"项目已存在: {name}")
        
        # 创建项目目录结构
        project_path.mkdir(parents=True)
        (project_path / "volumes").mkdir()
        (project_path / "chapters").mkdir()
        (project_path / "content").mkdir()
        
        # 创建配置
        now = datetime.now().isoformat()
        config = ProjectConfig(
            name=name,
            created_at=now,
            updated_at=now,
            **kwargs
        )
        
        # 保存配置
        self._save_config(project_path, config)
        
        self._current_project = config
        self._current_project_path = project_path
        
        return config
    
    def load_project(self, name: str) -> ProjectConfig:
        """
        加载项目
        
        Args:
            name: 项目名称
        """
        project_path = self.projects_dir / name
        if not project_path.exists():
            raise ValueError(f"项目不存在: {name}")
        
        config_path = project_path / "config.json"
        if not config_path.exists():
            raise ValueError(f"项目配置文件不存在: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 重建数据类
        config = self._dict_to_config(data)
        
        self._current_project = config
        self._current_project_path = project_path
        
        return config
    
    def save_project(self) -> None:
        """保存当前项目"""
        if self._current_project is None or self._current_project_path is None:
            raise ValueError("没有加载的项目")
        
        self._current_project.updated_at = datetime.now().isoformat()
        self._save_config(self._current_project_path, self._current_project)
    
    def _save_config(self, project_path: Path, config: ProjectConfig) -> None:
        """保存配置到文件"""
        config_path = project_path / "config.json"
        data = self._config_to_dict(config)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _config_to_dict(self, config: ProjectConfig) -> Dict:
        """将配置转换为字典"""
        data = asdict(config)
        return data
    
    def _dict_to_config(self, data: Dict) -> ProjectConfig:
        """将字典转换为配置"""
        # 处理嵌套的数据类
        volumes = []
        for v in data.get("volumes", []):
            chapters = [ChapterInfo(**c) for c in v.get("chapters", [])]
            v["chapters"] = chapters
            volumes.append(VolumeInfo(**v))
        data["volumes"] = volumes
        
        characters = [CharacterInfo(**c) for c in data.get("characters", [])]
        data["characters"] = characters
        
        return ProjectConfig(**data)
    
    @property
    def current(self) -> Optional[ProjectConfig]:
        """当前项目配置"""
        return self._current_project
    
    @property
    def project_path(self) -> Optional[Path]:
        """当前项目路径"""
        return self._current_project_path
    
    # === 文件操作 ===
    
    def get_file_path(self, *parts: str) -> Path:
        """获取项目内文件路径"""
        if self._current_project_path is None:
            raise ValueError("没有加载的项目")
        return self._current_project_path.joinpath(*parts)
    
    def read_file(self, *parts: str) -> str:
        """读取项目内文件"""
        path = self.get_file_path(*parts)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
    
    def write_file(self, content: str, *parts: str) -> Path:
        """写入项目内文件"""
        path = self.get_file_path(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
    
    # === 进度追踪 ===
    
    def update_stage(self, stage: str) -> None:
        """更新当前阶段"""
        if self._current_project:
            self._current_project.current_stage = stage
            self.save_project()
    
    def update_progress(self, volume: int = None, chapter: int = None) -> None:
        """更新当前进度"""
        if self._current_project:
            if volume is not None:
                self._current_project.current_volume = volume
            if chapter is not None:
                self._current_project.current_chapter = chapter
            self.save_project()
    
    # === 角色管理 ===
    
    def add_character(self, character: CharacterInfo) -> None:
        """添加角色"""
        if self._current_project:
            self._current_project.characters.append(character)
            self.save_project()
    
    def get_character(self, name: str) -> Optional[CharacterInfo]:
        """获取角色"""
        if self._current_project:
            for char in self._current_project.characters:
                if char.name == name:
                    return char
        return None
    
    def get_characters_summary(self) -> str:
        """获取角色摘要（用于Prompt）"""
        if not self._current_project or not self._current_project.characters:
            return ""
        
        lines = ["## 主要角色"]
        for char in self._current_project.characters:
            lines.append(f"- **{char.name}** ({char.role}): {char.description}")
            if char.traits:
                lines.append(f"  性格: {', '.join(char.traits)}")
        
        return "\n".join(lines)
    
    # === 内容摘要（长篇记忆） ===
    
    def update_summary(self, summary: str) -> None:
        """更新剧情摘要"""
        if self._current_project:
            self._current_project.summary = summary
            self.save_project()
    
