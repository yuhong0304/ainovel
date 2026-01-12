"""
通用工具函数
"""

import re
from typing import Tuple


def count_chinese_chars(text: str) -> int:
    """
    统计中文字符数量
    
    Args:
        text: 输入文本
        
    Returns:
        int: 中文字符数量
    """
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    return len(chinese_pattern.findall(text))


def count_words(text: str) -> int:
    """
    统计字数（中文按字符，英文按单词）
    
    Args:
        text: 输入文本
        
    Returns:
        int: 字数
    """
    # 中文字符
    chinese_count = count_chinese_chars(text)
    
    # 移除中文后统计英文单词
    text_without_chinese = re.sub(r'[\u4e00-\u9fff]', '', text)
    english_words = len(text_without_chinese.split())
    
    return chinese_count + english_words


def split_into_chapters(text: str, target_words: int = 3000) -> list:
    """
    将长文本切分为章节
    
    Args:
        text: 长文本
        target_words: 目标每章字数
        
    Returns:
        list: 章节列表
    """
    paragraphs = text.split('\n\n')
    chapters = []
    current_chapter = []
    current_count = 0
    
    for para in paragraphs:
        para_count = count_words(para)
        
        if current_count + para_count > target_words and current_chapter:
            # 当前章节已达目标，开始新章节
            chapters.append('\n\n'.join(current_chapter))
            current_chapter = [para]
            current_count = para_count
        else:
            current_chapter.append(para)
            current_count += para_count
    
    # 添加最后一章
    if current_chapter:
        chapters.append('\n\n'.join(current_chapter))
    
    return chapters


def extract_chapter_title(content: str) -> Tuple[str, str]:
    """
    从章节内容中提取标题
    
    Args:
        content: 章节内容
        
    Returns:
        Tuple[标题, 正文]
    """
    lines = content.strip().split('\n')
    
    # 尝试匹配常见的章节标题格式
    title_patterns = [
        r'^#+\s*(.+)$',           # Markdown标题
        r'^第.+章[：:]\s*(.+)$',   # 第X章：标题
        r'^第.+章\s+(.+)$',        # 第X章 标题
        r'^Chapter\s*\d+[：:]\s*(.+)$',  # Chapter X: Title
    ]
    
    title = ""
    body_start = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        for pattern in title_patterns:
            match = re.match(pattern, line)
            if match:
                title = match.group(1) if match.groups() else line
                body_start = i + 1
                break
        
        if title:
            break
        elif i == 0:
            # 第一行作为标题
            title = line
            body_start = 1
            break
    
    body = '\n'.join(lines[body_start:]).strip()
    return title, body


def clean_markdown(text: str) -> str:
    """
    清理Markdown格式，提取纯文本
    
    Args:
        text: Markdown文本
        
    Returns:
        str: 纯文本
    """
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 移除行内代码
    text = re.sub(r'`[^`]+`', '', text)
    # 移除标题标记
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 移除加粗/斜体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # 移除链接
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    return text.strip()


def format_chapter_number(num: int, style: str = "chinese") -> str:
    """
    格式化章节编号
    
    Args:
        num: 章节数字
        style: 格式样式 ("chinese" | "arabic" | "roman")
        
    Returns:
        str: 格式化后的编号
    """
    if style == "chinese":
        chinese_nums = "零一二三四五六七八九十"
        if num <= 10:
            return f"第{chinese_nums[num]}章"
        elif num < 20:
            return f"第十{chinese_nums[num-10]}章"
        elif num < 100:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return f"第{chinese_nums[tens]}十章"
            return f"第{chinese_nums[tens]}十{chinese_nums[ones]}章"
        else:
            return f"第{num}章"
    elif style == "arabic":
        return f"第{num}章"
    elif style == "roman":
        # 简单的罗马数字转换
        roman_map = [
            (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
        ]
        result = ""
        for value, numeral in roman_map:
            while num >= value:
                result += numeral
                num -= value
        return f"Chapter {result}"
    
    return f"第{num}章"


def sanitize_filename(name: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        name: 原始名称
        
    Returns:
        str: 安全的文件名
    """
    # 移除非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    name = re.sub(illegal_chars, '', name)
    # 移除首尾空格
    name = name.strip()
    # 限制长度
    if len(name) > 100:
        name = name[:100]
    return name or "untitled"
