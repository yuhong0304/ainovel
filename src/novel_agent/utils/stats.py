"""
统计仪表板模块
提供项目统计数据和可视化
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


@dataclass
class ProjectStats:
    """项目统计数据"""
    project_name: str
    total_words: int
    total_chapters: int
    total_characters: int
    total_locations: int
    last_updated: str
    created_at: str
    
    # 详细统计
    words_per_chapter: List[int] = None
    generation_history: List[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class StatsCollector:
    """
    统计收集器
    
    功能:
    - 字数统计
    - 生成历史记录
    - 成本追踪
    - 趋势分析
    """
    
    def __init__(self, project_path: Path):
        """
        初始化统计收集器
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
        self.stats_file = self.project_path / ".stats.json"
        self._stats: Dict[str, Any] = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """加载统计数据"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载统计数据失败: {e}")
        
        return {
            "project_name": self.project_path.name,
            "created_at": datetime.now().isoformat(),
            "generation_history": [],
            "daily_words": {},
            "cost_history": [],
            "session_stats": []
        }
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    def _count_words(self, text: str) -> int:
        """统计字数"""
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english
    
    def record_generation(
        self,
        stage: str,
        content: str,
        tokens_used: int = 0,
        cost: float = 0.0,
        model: str = ""
    ):
        """
        记录一次生成
        
        Args:
            stage: 生成阶段 (master, volume, chapter, content, polish)
            content: 生成的内容
            tokens_used: 使用的token数
            cost: 花费成本
            model: 使用的模型
        """
        word_count = self._count_words(content)
        today = datetime.now().strftime("%Y-%m-%d")
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "word_count": word_count,
            "tokens_used": tokens_used,
            "cost": cost,
            "model": model
        }
        
        self._stats["generation_history"].append(record)
        
        # 更新每日字数
        if today not in self._stats["daily_words"]:
            self._stats["daily_words"][today] = 0
        self._stats["daily_words"][today] += word_count
        
        # 记录成本
        if cost > 0:
            self._stats["cost_history"].append({
                "date": today,
                "cost": cost,
                "tokens": tokens_used,
                "model": model
            })
        
        self._save_stats()
    
    def get_project_stats(self) -> ProjectStats:
        """获取项目统计概览"""
        content_dir = self.project_path / "content"
        worldbook_dir = self.project_path / "worldbuilding"
        
        # 统计章节和字数
        total_words = 0
        words_per_chapter = []
        chapter_count = 0
        
        if content_dir.exists():
            for chapter_file in sorted(content_dir.glob("chapter_*.md")):
                content = chapter_file.read_text(encoding='utf-8')
                word_count = self._count_words(content)
                total_words += word_count
                words_per_chapter.append(word_count)
                chapter_count += 1
        
        # 统计角色和地点
        character_count = 0
        location_count = 0
        
        cards_file = worldbook_dir / "cards.json" if worldbook_dir.exists() else None
        if cards_file and cards_file.exists():
            try:
                with open(cards_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f).get('cards', [])
                    for card in cards:
                        if card.get('card_type') == 'character':
                            character_count += 1
                        elif card.get('card_type') == 'location':
                            location_count += 1
            except:
                pass
        
        return ProjectStats(
            project_name=self.project_path.name,
            total_words=total_words,
            total_chapters=chapter_count,
            total_characters=character_count,
            total_locations=location_count,
            last_updated=datetime.now().isoformat(),
            created_at=self._stats.get("created_at", ""),
            words_per_chapter=words_per_chapter,
            generation_history=self._stats.get("generation_history", [])[-20:]
        )
    
    def get_daily_words(self, days: int = 30) -> Dict[str, int]:
        """获取每日字数统计"""
        daily = self._stats.get("daily_words", {})
        
        # 过滤最近N天
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return {
            date: count for date, count in daily.items()
            if date >= cutoff
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """获取成本摘要"""
        history = self._stats.get("cost_history", [])
        
        if not history:
            return {
                "total_cost": 0,
                "total_tokens": 0,
                "by_model": {},
                "by_date": {}
            }
        
        total_cost = sum(h["cost"] for h in history)
        total_tokens = sum(h.get("tokens", 0) for h in history)
        
        by_model = defaultdict(float)
        by_date = defaultdict(float)
        
        for h in history:
            by_model[h.get("model", "unknown")] += h["cost"]
            by_date[h.get("date", "")] += h["cost"]
        
        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_model": dict(by_model),
            "by_date": dict(by_date)
        }
    
    def get_generation_trends(self) -> Dict[str, Any]:
        """获取生成趋势"""
        history = self._stats.get("generation_history", [])
        
        by_stage = defaultdict(int)
        by_date = defaultdict(int)
        
        for h in history:
            by_stage[h.get("stage", "unknown")] += 1
            date = h.get("timestamp", "")[:10]
            if date:
                by_date[date] += h.get("word_count", 0)
        
        return {
            "generations_by_stage": dict(by_stage),
            "words_by_date": dict(by_date),
            "total_generations": len(history)
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板全部数据"""
        stats = self.get_project_stats()
        
        return {
            "overview": stats.to_dict(),
            "daily_words": self.get_daily_words(),
            "cost_summary": self.get_cost_summary(),
            "trends": self.get_generation_trends(),
            "recent_activity": self._stats.get("generation_history", [])[-10:]
        }


class GlobalStatsTracker:
    """
    全局统计追踪器
    跨项目统计
    """
    
    def __init__(self, projects_dir: Path):
        """
        初始化全局追踪器
        
        Args:
            projects_dir: 项目根目录
        """
        self.projects_dir = Path(projects_dir)
    
    def get_all_projects_stats(self) -> List[Dict[str, Any]]:
        """获取所有项目统计"""
        stats = []
        
        if not self.projects_dir.exists():
            return stats
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                try:
                    collector = StatsCollector(project_dir)
                    project_stats = collector.get_project_stats()
                    stats.append(project_stats.to_dict())
                except Exception as e:
                    logger.error(f"获取项目 {project_dir.name} 统计失败: {e}")
        
        return stats
    
    def get_global_summary(self) -> Dict[str, Any]:
        """获取全局摘要"""
        all_stats = self.get_all_projects_stats()
        
        return {
            "total_projects": len(all_stats),
            "total_words": sum(s.get("total_words", 0) for s in all_stats),
            "total_chapters": sum(s.get("total_chapters", 0) for s in all_stats),
            "total_characters": sum(s.get("total_characters", 0) for s in all_stats),
            "projects": all_stats
        }
