
import logging
import time
from typing import List, Dict, Any, Optional
from ..pipeline.stage_2_volume import VolumeOutlineGenerator
from ..pipeline.stage_3_chapter import ChapterOutlineGenerator
from ..core.context import ContextManager

logger = logging.getLogger(__name__)

class BatchStructureGenerator:
    """
    批量结构生成器
    
    功能:
    - 级联生成: 总纲 -> 卷纲 -> 章纲
    - 自动保存所有生成的文件
    """
    
    def __init__(self, llm_client, context_manager: ContextManager):
        self.llm = llm_client
        self.context_manager = context_manager
        self.vol_gen = VolumeOutlineGenerator(llm_client, context_manager=context_manager)
        self.chap_gen = ChapterOutlineGenerator(llm_client, context_manager=context_manager)

    def generate_full_structure(self, master_outline: str, volume_count: int = 4) -> Dict[str, Any]:
        """
        执行全量结构生成
        此操作耗时较长，建议在后台线程运行 (目前为同步)
        """
        results = {
            "volumes": [],
            "chapters": []
        }
        
        # 1. 保存总纲 (如果尚未保存，但通常由上层调用者处理)
        # self.context_manager.write_file(master_outline, "master_outline.md")
        
        # 2. 生成卷纲
        volume_outlines = self.vol_gen.generate_all(
            master_outline=master_outline,
            volume_count=volume_count
        )
        
        for i, vol_content in enumerate(volume_outlines):
            vol_num = i + 1
            
            # 保存卷纲
            self.vol_gen.save_outline(vol_content, vol_num)
            results["volumes"].append(f"Volume {vol_num} generated")
            
            # 3. 解析卷纲生成章纲 (默认每卷3个剧本，每个剧本3章)
            # 这里简化逻辑: 我们直接调用 ChapterOutlineGenerator.generate_for_volume
            # 它会解析卷纲中的剧本结构
            
            # 假设卷纲格式遵循标准 Prompt 输出，我们尝试解析出剧本数
            # 如果解析失败，默认生成3个剧本
            script_count = 3
            if "剧本4" in vol_content: script_count = 4
            if "剧本5" in vol_content: script_count = 5
            
            chapter_outlines = self.chap_gen.generate_for_volume(
                volume_outline=vol_content,
                script_count=script_count,
                start_chapter=(vol_num - 1) * (script_count * 3) + 1 # 估算起始章节
            )
            
            for j, chap_content in enumerate(chapter_outlines):
                script_num = j + 1
                self.chap_gen.save_outline(chap_content, vol_num, script_num)
                results["chapters"].append(f"V{vol_num}S{script_num} generated")
                
        return results
