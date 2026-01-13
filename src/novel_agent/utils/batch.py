"""
批量生成模块
支持一键生成多章节内容
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Generator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """批量任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTask:
    """批量任务项"""
    id: str
    chapter_num: int
    title: str
    status: BatchStatus = BatchStatus.PENDING
    progress: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


@dataclass
class BatchJob:
    """批量生成任务"""
    job_id: str
    project_name: str
    total_chapters: int
    start_chapter: int
    tasks: List[BatchTask] = field(default_factory=list)
    status: BatchStatus = BatchStatus.PENDING
    current_task_index: int = 0
    created_at: float = field(default_factory=time.time)
    
    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == BatchStatus.COMPLETED)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == BatchStatus.FAILED)
    
    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        return self.completed_count / len(self.tasks) * 100


class BatchGenerator:
    """
    批量生成器
    
    功能:
    - 一键生成多章节
    - 支持断点续传
    - 进度回调
    - 失败重试
    """
    
    def __init__(
        self,
        llm_client,
        prompt_manager,
        context_manager,
        project_path: Path
    ):
        """
        初始化批量生成器
        
        Args:
            llm_client: LLM客户端
            prompt_manager: Prompt管理器
            context_manager: 上下文管理器
            project_path: 项目路径
        """
        self.llm = llm_client
        self.prompt_manager = prompt_manager
        self.context_manager = context_manager
        self.project_path = Path(project_path)
        self.content_dir = self.project_path / "content"
        self.content_dir.mkdir(exist_ok=True)
        
        self._cancelled = False
        self._current_job: Optional[BatchJob] = None
        
    def create_job(
        self,
        start_chapter: int,
        end_chapter: int,
        chapter_titles: Optional[List[str]] = None
    ) -> BatchJob:
        """
        创建批量生成任务
        
        Args:
            start_chapter: 起始章节号
            end_chapter: 结束章节号
            chapter_titles: 可选的章节标题列表
        """
        import uuid
        
        job_id = str(uuid.uuid4())[:8]
        total = end_chapter - start_chapter + 1
        
        tasks = []
        for i, ch_num in enumerate(range(start_chapter, end_chapter + 1)):
            title = chapter_titles[i] if chapter_titles and i < len(chapter_titles) else f"第{ch_num}章"
            tasks.append(BatchTask(
                id=f"{job_id}-{ch_num}",
                chapter_num=ch_num,
                title=title
            ))
        
        job = BatchJob(
            job_id=job_id,
            project_name=self.project_path.name,
            total_chapters=total,
            start_chapter=start_chapter,
            tasks=tasks
        )
        
        return job
    
    def run_job(
        self,
        job: BatchJob,
        on_progress: Optional[Callable[[BatchJob, BatchTask], None]] = None,
        retry_failed: bool = True,
        max_retries: int = 2
    ) -> Generator[Dict[str, Any], None, None]:
        """
        执行批量生成任务
        
        Args:
            job: 批量任务
            on_progress: 进度回调
            retry_failed: 是否重试失败的任务
            max_retries: 最大重试次数
            
        Yields:
            每个任务的状态更新
        """
        self._current_job = job
        self._cancelled = False
        job.status = BatchStatus.RUNNING
        
        yield {"type": "job_started", "job": self._job_to_dict(job)}
        
        for task in job.tasks:
            if self._cancelled:
                task.status = BatchStatus.CANCELLED
                yield {"type": "task_cancelled", "task": self._task_to_dict(task)}
                continue
            
            task.status = BatchStatus.RUNNING
            task.started_at = time.time()
            yield {"type": "task_started", "task": self._task_to_dict(task)}
            
            retries = 0
            success = False
            
            while not success and retries <= max_retries:
                try:
                    # 生成章节内容
                    content = self._generate_chapter(task.chapter_num, task.title)
                    
                    # 保存内容
                    self._save_chapter(task.chapter_num, task.title, content)
                    
                    task.result = content
                    task.status = BatchStatus.COMPLETED
                    task.progress = 100.0
                    success = True
                    
                except Exception as e:
                    retries += 1
                    logger.error(f"章节 {task.chapter_num} 生成失败 (尝试 {retries}/{max_retries}): {e}")
                    
                    if retries > max_retries or not retry_failed:
                        task.status = BatchStatus.FAILED
                        task.error = str(e)
                    else:
                        time.sleep(2)  # 重试前等待
            
            task.finished_at = time.time()
            job.current_task_index += 1
            
            if on_progress:
                on_progress(job, task)
            
            yield {
                "type": "task_completed" if success else "task_failed",
                "task": self._task_to_dict(task),
                "job_progress": job.progress
            }
        
        # 任务完成
        job.status = BatchStatus.COMPLETED if job.failed_count == 0 else BatchStatus.FAILED
        self._current_job = None
        
        yield {
            "type": "job_completed",
            "job": self._job_to_dict(job),
            "summary": {
                "total": len(job.tasks),
                "completed": job.completed_count,
                "failed": job.failed_count
            }
        }
    
    def cancel(self):
        """取消当前任务"""
        self._cancelled = True
        if self._current_job:
            self._current_job.status = BatchStatus.CANCELLED
    
    def _generate_chapter(self, chapter_num: int, title: str) -> str:
        """生成单个章节内容"""
        # 获取上下文
        context = self.context_manager.get_context_for_chapter(chapter_num) if self.context_manager else ""
        
        # 获取prompt
        prompt = self.prompt_manager.get_prompt(
            "content_write",
            chapter_num=chapter_num,
            chapter_title=title,
            context=context
        )
        
        # 调用LLM生成
        result = self.llm.generate(prompt)
        return result.text
    
    def _save_chapter(self, chapter_num: int, title: str, content: str):
        """保存章节内容"""
        filename = f"chapter_{chapter_num:04d}.md"
        filepath = self.content_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(content)
        
        logger.info(f"已保存章节: {filename}")
    
    def _job_to_dict(self, job: BatchJob) -> Dict:
        """转换Job为字典"""
        return {
            "job_id": job.job_id,
            "project_name": job.project_name,
            "total_chapters": job.total_chapters,
            "start_chapter": job.start_chapter,
            "status": job.status.value,
            "progress": job.progress,
            "completed_count": job.completed_count,
            "failed_count": job.failed_count
        }
    
    def _task_to_dict(self, task: BatchTask) -> Dict:
        """转换Task为字典"""
        return {
            "id": task.id,
            "chapter_num": task.chapter_num,
            "title": task.title,
            "status": task.status.value,
            "progress": task.progress,
            "error": task.error
        }
