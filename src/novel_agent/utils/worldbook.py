"""
角色与世界观卡片管理模块
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class CardType(Enum):
    """卡片类型"""
    CHARACTER = "character"  # 角色
    LOCATION = "location"    # 地点
    ITEM = "item"           # 道具
    FACTION = "faction"     # 势力
    EVENT = "event"         # 事件
    CONCEPT = "concept"     # 概念/设定
    CUSTOM = "custom"       # 自定义


@dataclass
class WorldCard:
    """世界观卡片"""
    id: str
    name: str
    card_type: CardType
    description: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        d = asdict(self)
        d['card_type'] = self.card_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorldCard':
        """从字典创建"""
        data['card_type'] = CardType(data['card_type'])
        return cls(**data)
    
    def to_context_string(self) -> str:
        """转换为上下文字符串（用于RAG）"""
        parts = [f"【{self.card_type.value.upper()}】{self.name}"]
        parts.append(self.description)
        
        if self.attributes:
            attr_str = "；".join(f"{k}: {v}" for k, v in self.attributes.items())
            parts.append(f"属性: {attr_str}")
        
        if self.tags:
            parts.append(f"标签: {', '.join(self.tags)}")
        
        if self.relations:
            rel_str = "；".join(f"{r['type']}: {r['target']}" for r in self.relations)
            parts.append(f"关系: {rel_str}")
        
        return "\n".join(parts)


@dataclass
class CharacterCard(WorldCard):
    """角色卡片（扩展）"""
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        gender: str = "",
        age: str = "",
        appearance: str = "",
        personality: str = "",
        background: str = "",
        abilities: List[str] = None,
        **kwargs
    ) -> 'CharacterCard':
        """创建角色卡片"""
        attributes = {
            "gender": gender,
            "age": age,
            "appearance": appearance,
            "personality": personality,
            "background": background,
            "abilities": abilities or []
        }
        # 移除空值
        attributes = {k: v for k, v in attributes.items() if v}
        
        return cls(
            id=str(uuid.uuid4())[:8],
            name=name,
            card_type=CardType.CHARACTER,
            description=description,
            attributes=attributes,
            **kwargs
        )


class WorldManager:
    """
    世界观管理器
    
    功能:
    - 管理角色卡片
    - 管理世界观设定
    - 自动索引到RAG
    - 支持关系网络
    """
    
    def __init__(self, project_path: Path, rag_manager=None):
        """
        初始化世界观管理器
        
        Args:
            project_path: 项目路径
            rag_manager: RAG管理器（可选）
        """
        self.project_path = Path(project_path)
        self.world_dir = self.project_path / "worldbuilding"
        self.world_dir.mkdir(exist_ok=True)
        
        self.cards_file = self.world_dir / "cards.json"
        self.rag = rag_manager
        
        self._cards: Dict[str, WorldCard] = {}
        self._load_cards()
    
    def _load_cards(self):
        """加载所有卡片"""
        if self.cards_file.exists():
            try:
                with open(self.cards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for card_data in data.get('cards', []):
                        card = WorldCard.from_dict(card_data)
                        self._cards[card.id] = card
                logger.info(f"已加载 {len(self._cards)} 张卡片")
            except Exception as e:
                logger.error(f"加载卡片失败: {e}")
    
    def _save_cards(self):
        """保存所有卡片"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'cards': [card.to_dict() for card in self._cards.values()]
            }
            with open(self.cards_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存卡片失败: {e}")
    
    def add_card(self, card: WorldCard, index_to_rag: bool = True) -> WorldCard:
        """
        添加卡片
        
        Args:
            card: 卡片对象
            index_to_rag: 是否索引到RAG
        """
        self._cards[card.id] = card
        self._save_cards()
        
        if index_to_rag and self.rag:
            self._index_card(card)
        
        logger.info(f"添加卡片: {card.name} ({card.card_type.value})")
        return card
    
    def update_card(self, card_id: str, updates: Dict[str, Any]) -> Optional[WorldCard]:
        """更新卡片"""
        if card_id not in self._cards:
            return None
        
        card = self._cards[card_id]
        for key, value in updates.items():
            if hasattr(card, key):
                setattr(card, key, value)
        
        card.updated_at = datetime.now().isoformat()
        self._save_cards()
        
        if self.rag:
            self._index_card(card)
        
        return card
    
    def delete_card(self, card_id: str) -> bool:
        """删除卡片"""
        if card_id in self._cards:
            del self._cards[card_id]
            self._save_cards()
            return True
        return False
    
    def get_card(self, card_id: str) -> Optional[WorldCard]:
        """获取单个卡片"""
        return self._cards.get(card_id)
    
    def get_cards(
        self,
        card_type: Optional[CardType] = None,
        tags: Optional[List[str]] = None
    ) -> List[WorldCard]:
        """
        获取卡片列表
        
        Args:
            card_type: 按类型过滤
            tags: 按标签过滤
        """
        cards = list(self._cards.values())
        
        if card_type:
            cards = [c for c in cards if c.card_type == card_type]
        
        if tags:
            cards = [c for c in cards if any(t in c.tags for t in tags)]
        
        return cards
    
    def get_characters(self) -> List[WorldCard]:
        """获取所有角色"""
        return self.get_cards(card_type=CardType.CHARACTER)
    
    def get_locations(self) -> List[WorldCard]:
        """获取所有地点"""
        return self.get_cards(card_type=CardType.LOCATION)
    
    def search_cards(self, query: str) -> List[WorldCard]:
        """搜索卡片"""
        query = query.lower()
        results = []
        
        for card in self._cards.values():
            if (query in card.name.lower() or 
                query in card.description.lower() or
                any(query in tag.lower() for tag in card.tags)):
                results.append(card)
        
        return results
    
    def _index_card(self, card: WorldCard):
        """将卡片索引到RAG"""
        if not self.rag:
            return
        
        try:
            self.rag.add_documents(
                documents=[card.to_context_string()],
                metadatas=[{
                    "type": "world_card",
                    "card_type": card.card_type.value,
                    "card_id": card.id,
                    "card_name": card.name
                }],
                ids=[f"world_card_{card.id}"]
            )
        except Exception as e:
            logger.error(f"索引卡片到RAG失败: {e}")
    
    def index_all_cards(self):
        """将所有卡片索引到RAG"""
        for card in self._cards.values():
            self._index_card(card)
        logger.info(f"已索引 {len(self._cards)} 张卡片到RAG")
    
    def export_worldbook(self, format: str = "json") -> str:
        """
        导出世界书
        
        Args:
            format: 导出格式 (json, markdown)
        """
        if format == "markdown":
            return self._export_markdown()
        else:
            return json.dumps(
                [card.to_dict() for card in self._cards.values()],
                ensure_ascii=False,
                indent=2
            )
    
    def _export_markdown(self) -> str:
        """导出为Markdown格式"""
        lines = ["# 世界书\n"]
        
        # 按类型分组
        by_type: Dict[CardType, List[WorldCard]] = {}
        for card in self._cards.values():
            if card.card_type not in by_type:
                by_type[card.card_type] = []
            by_type[card.card_type].append(card)
        
        type_names = {
            CardType.CHARACTER: "角色",
            CardType.LOCATION: "地点",
            CardType.ITEM: "道具",
            CardType.FACTION: "势力",
            CardType.EVENT: "事件",
            CardType.CONCEPT: "设定",
            CardType.CUSTOM: "其他"
        }
        
        for card_type, cards in by_type.items():
            lines.append(f"\n## {type_names.get(card_type, card_type.value)}\n")
            
            for card in cards:
                lines.append(f"### {card.name}\n")
                lines.append(f"{card.description}\n")
                
                if card.attributes:
                    lines.append("\n**属性:**\n")
                    for k, v in card.attributes.items():
                        if isinstance(v, list):
                            v = ", ".join(str(i) for i in v)
                        lines.append(f"- {k}: {v}")
                    lines.append("")
                
                if card.tags:
                    lines.append(f"\n*标签: {', '.join(card.tags)}*\n")
        
        return "\n".join(lines)
    
    def create_character(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> WorldCard:
        """快捷方法：创建角色"""
        card = CharacterCard.create(name, description, **kwargs)
        return self.add_card(card)
    
    def create_location(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> WorldCard:
        """快捷方法：创建地点"""
        card = WorldCard(
            id=str(uuid.uuid4())[:8],
            name=name,
            card_type=CardType.LOCATION,
            description=description,
            **kwargs
        )
        return self.add_card(card)
