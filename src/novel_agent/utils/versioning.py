"""
版本历史管理模块
支持内容版本管理和回滚
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


@dataclass
class Version:
    """版本记录"""
    version_id: str
    file_path: str
    content_hash: str
    timestamp: str
    message: str
    word_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Version':
        return cls(**data)


class VersionManager:
    """
    版本管理器
    
    功能:
    - 自动保存文件版本
    - 查看历史版本
    - 版本对比
    - 回滚到指定版本
    """
    
    MAX_VERSIONS_PER_FILE = 50  # 每个文件最多保存的版本数
    
    def __init__(self, project_path: Path):
        """
        初始化版本管理器
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
        self.versions_dir = self.project_path / ".versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        self.index_file = self.versions_dir / "index.json"
        self._index: Dict[str, List[Version]] = {}
        self._load_index()
    
    def _load_index(self):
        """加载版本索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for file_path, versions in data.items():
                        self._index[file_path] = [Version.from_dict(v) for v in versions]
            except Exception as e:
                logger.error(f"加载版本索引失败: {e}")
    
    def _save_index(self):
        """保存版本索引"""
        try:
            data = {
                fp: [v.to_dict() for v in versions]
                for fp, versions in self._index.items()
            }
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存版本索引失败: {e}")
    
    def _hash_content(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
    
    def _count_words(self, content: str) -> int:
        """统计字数"""
        import re
        # 中文字符
        chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
        # 英文单词
        english = len(re.findall(r'[a-zA-Z]+', content))
        return chinese + english
    
    def _generate_version_id(self) -> str:
        """生成版本ID"""
        import uuid
        return datetime.now().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4())[:4]
    
    def save_version(
        self,
        file_path: str,
        content: str,
        message: str = "自动保存"
    ) -> Version:
        """
        保存文件版本
        
        Args:
            file_path: 相对项目的文件路径
            content: 文件内容
            message: 版本说明
        """
        content_hash = self._hash_content(content)
        
        # 检查是否与最新版本相同
        if file_path in self._index and self._index[file_path]:
            latest = self._index[file_path][-1]
            if latest.content_hash == content_hash:
                logger.debug(f"内容未变化，跳过版本保存: {file_path}")
                return latest
        
        # 创建版本
        version_id = self._generate_version_id()
        version = Version(
            version_id=version_id,
            file_path=file_path,
            content_hash=content_hash,
            timestamp=datetime.now().isoformat(),
            message=message,
            word_count=self._count_words(content)
        )
        
        # 保存内容文件
        version_file = self.versions_dir / f"{version_id}.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 更新索引
        if file_path not in self._index:
            self._index[file_path] = []
        self._index[file_path].append(version)
        
        # 清理旧版本
        self._cleanup_old_versions(file_path)
        
        self._save_index()
        logger.info(f"保存版本: {file_path} -> {version_id}")
        
        return version
    
    def _cleanup_old_versions(self, file_path: str):
        """清理旧版本"""
        if file_path not in self._index:
            return
        
        versions = self._index[file_path]
        if len(versions) <= self.MAX_VERSIONS_PER_FILE:
            return
        
        # 删除最旧的版本
        to_delete = versions[:-self.MAX_VERSIONS_PER_FILE]
        for v in to_delete:
            version_file = self.versions_dir / f"{v.version_id}.txt"
            if version_file.exists():
                version_file.unlink()
        
        self._index[file_path] = versions[-self.MAX_VERSIONS_PER_FILE:]
    
    def get_versions(self, file_path: str) -> List[Version]:
        """获取文件的所有版本"""
        return self._index.get(file_path, [])
    
    def get_version_content(self, version_id: str) -> Optional[str]:
        """获取指定版本的内容"""
        version_file = self.versions_dir / f"{version_id}.txt"
        if version_file.exists():
            return version_file.read_text(encoding='utf-8')
        return None
    
    def restore_version(self, file_path: str, version_id: str) -> bool:
        """
        恢复到指定版本
        
        Args:
            file_path: 文件路径
            version_id: 版本ID
        """
        content = self.get_version_content(version_id)
        if content is None:
            logger.error(f"版本内容不存在: {version_id}")
            return False
        
        # 保存当前版本
        target_file = self.project_path / file_path
        if target_file.exists():
            current_content = target_file.read_text(encoding='utf-8')
            self.save_version(file_path, current_content, f"回滚前备份 (恢复到 {version_id})")
        
        # 恢复内容
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 记录恢复版本
        self.save_version(file_path, content, f"恢复自版本 {version_id}")
        
        logger.info(f"已恢复: {file_path} -> {version_id}")
        return True
    
    def diff_versions(self, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """
        比较两个版本的差异
        
        Returns:
            包含差异信息的字典
        """
        content1 = self.get_version_content(version_id_1)
        content2 = self.get_version_content(version_id_2)
        
        if content1 is None or content2 is None:
            return {"error": "版本内容不存在"}
        
        import difflib
        
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=version_id_1,
            tofile=version_id_2,
            lineterm=''
        ))
        
        return {
            "version_1": version_id_1,
            "version_2": version_id_2,
            "word_count_1": self._count_words(content1),
            "word_count_2": self._count_words(content2),
            "word_diff": self._count_words(content2) - self._count_words(content1),
            "diff": diff
        }
    
    def get_all_files(self) -> List[str]:
        """获取所有有版本记录的文件"""
        return list(self._index.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取版本统计信息"""
        total_versions = sum(len(v) for v in self._index.values())
        total_files = len(self._index)
        
        # 计算存储空间
        total_size = 0
        for f in self.versions_dir.glob("*.txt"):
            total_size += f.stat().st_size
        
        return {
            "total_files": total_files,
            "total_versions": total_versions,
            "storage_size_mb": round(total_size / (1024 * 1024), 2)
        }
