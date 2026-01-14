"""
Utils module - 工具函数
"""

from .common import *

# 延迟导入新模块以避免依赖问题
def __getattr__(name):
    """延迟加载模块"""
    if name == "NovelExporter":
        from .exporter import NovelExporter
        return NovelExporter
    elif name in ("BatchGenerator", "BatchJob", "BatchTask", "BatchStatus"):
        from .batch import BatchGenerator, BatchJob, BatchTask, BatchStatus
        return {"BatchGenerator": BatchGenerator, "BatchJob": BatchJob, 
                "BatchTask": BatchTask, "BatchStatus": BatchStatus}[name]
    elif name in ("WorldManager", "WorldCard", "CharacterCard", "CardType"):
        from .worldbook import WorldManager, WorldCard, CharacterCard, CardType
        return {"WorldManager": WorldManager, "WorldCard": WorldCard,
                "CharacterCard": CharacterCard, "CardType": CardType}[name]
    elif name in ("VersionManager", "Version"):
        from .versioning import VersionManager, Version
        return {"VersionManager": VersionManager, "Version": Version}[name]
    elif name in ("StatsCollector", "GlobalStatsTracker", "ProjectStats"):
        from .stats import StatsCollector, GlobalStatsTracker, ProjectStats
        return {"StatsCollector": StatsCollector, "GlobalStatsTracker": GlobalStatsTracker,
                "ProjectStats": ProjectStats}[name]
    elif name == "StructureManager":
        from .structure import StructureManager
        return StructureManager
    elif name == "BatchStructureGenerator":
        from .batch_structure import BatchStructureGenerator
        return BatchStructureGenerator
    elif name == "ContentManager":
        from .content import ContentManager
        return ContentManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # 导出器
    "NovelExporter",
    
    # 批量生成
    "BatchGenerator",
    "BatchJob",
    "BatchTask",
    "BatchStatus",
    
    # 世界观管理
    "WorldManager",
    "WorldCard",
    "CharacterCard",
    "CardType",
    
    # 版本管理
    "VersionManager",
    "Version",
    
    # 统计
    "StatsCollector",
    "GlobalStatsTracker",
    "ProjectStats",
    
    # 结构管理
    "StructureManager",
    "BatchStructureGenerator",
    "ContentManager"
]
