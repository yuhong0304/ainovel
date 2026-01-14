"""
风格分析器
用于分析文本风格，确保写作风格一致性
"""

import re
import math
from typing import Dict, List, Optional
from collections import Counter

class StyleAnalyzer:
    """
    风格分析器
    
    分析维度：
    1. 句子长度分布 (节奏)
    2. 对话/旁白比例
    3. 标点符号使用习惯
    4. 常用词/成语密度 (简易版)
    """
    
    def __init__(self, text: str = ""):
        self.text = text
        self.metrics = self._analyze() if text else {}
        
    def analyze_text(self, text: str) -> Dict:
        """分析新文本"""
        self.text = text
        self.metrics = self._analyze()
        return self.metrics
    
    def _analyze(self) -> Dict:
        """执行分析"""
        if not self.text:
            return {}
            
        paragraphs = [p for p in self.text.split('\n') if p.strip()]
        sentences = re.split(r'[。！？!?]', self.text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 1. 句子长度 (Rhythm)
        lengths = [len(s) for s in sentences]
        avg_len = sum(lengths) / len(lengths) if lengths else 0
        short_sents = len([l for l in lengths if l < 10])
        long_sents = len([l for l in lengths if l > 30])
        
        # 2. 对话比例
        dialogue_chars = sum(len(m) for m in re.findall(r'“.*?”', self.text))
        dialogue_ratio = dialogue_chars / len(self.text) if len(self.text) > 0 else 0
        
        # 3. 标点特征 (Exclamation density)
        exclamations = self.text.count('！') + self.text.count('!')
        exclamation_density = exclamations / len(sentences) if sentences else 0
        
        return {
            "avg_sentence_length": round(avg_len, 1),
            "short_sentence_ratio": round(short_sents / len(sentences), 2) if sentences else 0,
            "long_sentence_ratio": round(long_sents / len(sentences), 2) if sentences else 0,
            "dialogue_ratio": round(dialogue_ratio, 2),
            "exclamation_density": round(exclamation_density, 2),
            "paragraph_count": len(paragraphs),
            "avg_paragraph_len": round(len(self.text) / len(paragraphs), 1) if paragraphs else 0
        }
        
    def compare(self, other_metrics: Dict) -> Dict:
        """
        对比风格差异
        
        Returns:
            Dict: 差异报告 (diff key: value)
        """
        if not self.metrics or not other_metrics:
            return {}
            
        diffs = {}
        
        # 阈值定义 (超过多少算显著差异)
        thresholds = {
            "avg_sentence_length": 5.0, # 均长差5字
            "dialogue_ratio": 0.15,     # 对话比差15%
            "exclamation_density": 0.2  # 感叹号密度差0.2
        }
        
        for key, threshold in thresholds.items():
            val1 = self.metrics.get(key, 0)
            val2 = other_metrics.get(key, 0)
            delta = val1 - val2
            
            if abs(delta) > threshold:
                trend = "higher" if delta > 0 else "lower"
                diffs[key] = {
                    "current": val1,
                    "target": val2,
                    "trend": trend,
                    "delta": round(delta, 2)
                }
                
        return diffs
    
    def generate_style_prompt(self, diffs: Dict) -> str:
        """根据差异生成修正Prompt"""
        if not diffs:
            return ""
            
        suggestions = []
        
        if "avg_sentence_length" in diffs:
            d = diffs["avg_sentence_length"]
            if d["trend"] == "higher":
                suggestions.append("当前文风略显拖沓，请尝试使用更多短句，加快叙事节奏。")
            else:
                suggestions.append("当前节奏过快，请适当增加描写和长句，舒缓节奏。")
                
        if "dialogue_ratio" in diffs:
            d = diffs["dialogue_ratio"]
            if d["trend"] == "higher":
                suggestions.append("对话占比过高，请增加旁白和心理描写。")
            else:
                suggestions.append("对话占比过低，请通过人物对话来推动情节，减少枯燥叙述。")
                
        if "exclamation_density" in diffs:
            d = diffs["exclamation_density"]
            if d["trend"] == "higher":
                suggestions.append("感叹号使用过多，情绪显得过于激动，请克制语气。")
        
        return "\n".join(suggestions)
