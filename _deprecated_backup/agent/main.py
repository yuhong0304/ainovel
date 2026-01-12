"""
番茄小说Agent - 命令行主入口
半自动化小说生成系统
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 添加agent目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from agent.gemini_client import GeminiClient, get_usage_summary, get_available_models, get_model_by_name
from agent.prompt_manager import PromptManager
from agent.context_manager import ContextManager
from agent.pipeline import (
    MetaPromptGenerator,
    MasterOutlineGenerator,
    VolumeOutlineGenerator,
    ChapterOutlineGenerator,
    ContentGenerator,
    PolishProcessor,
    RuleLearner
)
from agent.utils import count_words

# 加载环境变量
load_dotenv()

# Rich控制台
console = Console()

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
PROJECTS_DIR = BASE_DIR / "projects"


class NovelAgent:
    """小说生成Agent主类"""
    
    def __init__(self):
        self.console = console
        self.llm: Optional[GeminiClient] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.context_manager: Optional[ContextManager] = None
        
        # 流水线模块
        self.meta_generator: Optional[MetaPromptGenerator] = None
        self.master_generator: Optional[MasterOutlineGenerator] = None
        self.volume_generator: Optional[VolumeOutlineGenerator] = None
        self.chapter_generator: Optional[ChapterOutlineGenerator] = None
        self.content_generator: Optional[ContentGenerator] = None
        self.polish_processor: Optional[PolishProcessor] = None
        self.rule_learner: Optional[RuleLearner] = None
    
    def initialize(self) -> bool:
        """初始化Agent"""
        self.console.print("\n[bold cyan]🚀 番茄小说Agent 启动中...[/bold cyan]\n")
        
        # 检查API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.console.print("[bold red]❌ 错误: 未找到 GEMINI_API_KEY 环境变量[/bold red]")
            self.console.print("请设置环境变量或在项目根目录创建 .env 文件:")
            self.console.print("  GEMINI_API_KEY=your_api_key_here")
            return False
        
        try:
            # 初始化LLM客户端
            model_name = os.getenv("GEMINI_MODEL")  # 从环境变量读取模型
            self.llm = GeminiClient(api_key=api_key, model_name=model_name)
            self.console.print(f"[green]✓[/green] Gemini API 连接成功 (模型: {self.llm.model_name})")
            
            # 确保目录存在
            PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
            PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
            (PROMPTS_DIR / "system").mkdir(exist_ok=True)
            (PROMPTS_DIR / "stages").mkdir(exist_ok=True)
            (PROMPTS_DIR / "learned").mkdir(exist_ok=True)
            
            # 初始化管理器
            self.prompt_manager = PromptManager(str(PROMPTS_DIR))
            self.context_manager = ContextManager(str(PROJECTS_DIR))
            self.console.print("[green]✓[/green] 管理器初始化完成")
            
            # 初始化流水线模块
            self._init_pipeline()
            self.console.print("[green]✓[/green] 流水线模块就绪")
            
            return True
            
        except Exception as e:
            self.console.print(f"[bold red]❌ 初始化失败: {e}[/bold red]")
            return False
    
    def _init_pipeline(self):
        """初始化流水线模块"""
        self.meta_generator = MetaPromptGenerator(self.llm)
        self.master_generator = MasterOutlineGenerator(
            self.llm, self.prompt_manager, self.context_manager
        )
        self.volume_generator = VolumeOutlineGenerator(
            self.llm, self.prompt_manager, self.context_manager
        )
        self.chapter_generator = ChapterOutlineGenerator(
            self.llm, self.prompt_manager, self.context_manager
        )
        self.content_generator = ContentGenerator(
            self.llm, self.prompt_manager, self.context_manager
        )
        self.polish_processor = PolishProcessor(
            self.llm, self.prompt_manager, self.context_manager
        )
        self.rule_learner = RuleLearner(
            self.llm, self.prompt_manager, self.context_manager
        )
    
    def run(self):
        """主运行循环"""
        if not self.initialize():
            return
        
        self.show_welcome()
        
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == "1":
                    self.create_new_novel()
                elif choice == "2":
                    self.continue_novel()
                elif choice == "3":
                    self.show_settings()
                elif choice == "q":
                    # 显示Token使用摘要
                    usage = get_usage_summary()
                    if usage["call_count"] > 0:
                        self.console.print("\n[bold]📊 本次Token使用统计:[/bold]")
                        self.console.print(f"  调用次数: {usage['call_count']}")
                        self.console.print(f"  输入Token: {usage['total_input_tokens']:,}")
                        self.console.print(f"  输出Token: {usage['total_output_tokens']:,}")
                        self.console.print(f"  预估成本: ${usage['total_cost_usd']:.4f}")
                    self.console.print("\n[cyan]👋 再见！祝创作愉快！[/cyan]\n")
                    break
                else:
                    self.console.print("[yellow]无效选项，请重新选择[/yellow]")
                    
            except KeyboardInterrupt:
                self.console.print("\n\n[cyan]👋 再见！[/cyan]\n")
                break
            except Exception as e:
                self.console.print(f"[red]发生错误: {e}[/red]")
    
    def show_welcome(self):
        """显示欢迎信息"""
        welcome = """
# 📚 番茄小说Agent

一个半自动化的网文创作系统

**功能特点**:
- 🎯 从灵感到成稿的完整流水线
- 🤖 AI生成 + 人工审核的半自动模式  
- 📖 3000字/章的标准切分
- ✨ 自动学习你的润色风格
        """
        self.console.print(Panel(Markdown(welcome), border_style="cyan"))
    
    def show_main_menu(self) -> str:
        """显示主菜单"""
        self.console.print("\n[bold]请选择操作:[/bold]")
        self.console.print("  [cyan]1.[/cyan] 创建新小说")
        self.console.print("  [cyan]2.[/cyan] 继续现有项目")
        self.console.print("  [cyan]3.[/cyan] 设置")
        self.console.print("  [cyan]q.[/cyan] 退出")
        
        return Prompt.ask("\n选择", default="1")
    
    def create_new_novel(self):
        """创建新小说"""
        self.console.print("\n[bold cyan]📝 创建新小说[/bold cyan]\n")
        
        # 获取项目名称
        name = Prompt.ask("项目名称（用于文件夹，英文/数字）")
        if not name:
            return
        
        # 检查是否已存在
        if (PROJECTS_DIR / name).exists():
            self.console.print(f"[yellow]项目 '{name}' 已存在[/yellow]")
            if not Confirm.ask("是否覆盖？"):
                return
        
        # 获取小说灵感
        self.console.print("\n[bold]请描述你的小说灵感/想法:[/bold]")
        self.console.print("[dim]（越详细越好：题材、主角设定、核心冲突等）[/dim]\n")
        
        inspiration = Prompt.ask("灵感")
        if not inspiration:
            return
        
        # 创建项目
        try:
            project = self.context_manager.create_project(name, title=name)
            self.console.print(f"\n[green]✓[/green] 项目创建成功: {name}")
        except Exception as e:
            self.console.print(f"[red]创建失败: {e}[/red]")
            return
        
        # 开始生成流程
        self._generate_with_meta(inspiration)
    
    def _generate_with_meta(self, inspiration: str):
        """使用元提示生成全套内容"""
        
        # Step 1: 分析灵感，生成配置
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("分析灵感中...", total=None)
            config = self.meta_generator.analyze_inspiration(inspiration)
        
        # 显示配置
        self.console.print("\n[bold]📊 小说配置:[/bold]")
        self.console.print(Panel(Markdown(config), title="定制化配置"))
        
        # 确认或修改
        if not Confirm.ask("\n配置是否满意？"):
            feedback = Prompt.ask("请输入修改意见")
            config = self.meta_generator.refine_config(config, feedback)
            self.console.print(Panel(Markdown(config), title="修改后配置"))
        
        # 保存配置
        if self.context_manager.project_path:
            config_path = self.context_manager.project_path / "novel_config.yaml"
            config_path.write_text(config, encoding="utf-8")
            self.console.print(f"[green]✓[/green] 配置已保存")
        
        # Step 2: 生成总纲
        if Confirm.ask("\n是否生成总纲？"):
            self._generate_master_outline(config)
    
    def _generate_master_outline(self, context: str = ""):
        """生成总纲"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("生成总纲中...", total=None)
            
            inspiration = Prompt.ask("补充任何想法（可留空）", default="")
            outline = self.master_generator.generate(
                user_input=inspiration or "根据配置生成",
                additional_context=context
            )
        
        # 显示结果
        self.console.print("\n[bold]📖 总纲:[/bold]")
        self.console.print(Panel(Markdown(outline), title="小说总纲"))
        
        # 迭代修改
        while True:
            action = Prompt.ask(
                "\n操作",
                choices=["accept", "modify", "regenerate"],
                default="accept"
            )
            
            if action == "accept":
                # 保存
                path = self.master_generator.save_outline(outline)
                self.console.print(f"[green]✓[/green] 总纲已保存: {path}")
                
                # 询问是否继续
                if Confirm.ask("是否继续生成粗纲？"):
                    self._generate_volume_outline(outline)
                break
                
            elif action == "modify":
                feedback = Prompt.ask("修改意见")
                outline = self.master_generator.refine(outline, feedback)
                self.console.print(Panel(Markdown(outline), title="修改后总纲"))
                
            elif action == "regenerate":
                outline = self.master_generator.generate(
                    user_input=inspiration or "重新生成",
                    additional_context=context
                )
                self.console.print(Panel(Markdown(outline), title="重新生成的总纲"))
    
    def _generate_volume_outline(self, master_outline: str):
        """生成粗纲"""
        volume_num = int(Prompt.ask("生成第几卷粗纲", default="1"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"生成第{volume_num}卷粗纲...", total=None)
            outline = self.volume_generator.generate(
                master_outline=master_outline,
                volume_number=volume_num
            )
        
        self.console.print(f"\n[bold]📖 第{volume_num}卷粗纲:[/bold]")
        self.console.print(Panel(Markdown(outline), title=f"第{volume_num}卷"))
        
        if Confirm.ask("保存此粗纲？"):
            path = self.volume_generator.save_outline(outline, volume_num)
            self.console.print(f"[green]✓[/green] 已保存: {path}")
    
    def continue_novel(self):
        """继续现有项目"""
        projects = self.context_manager.list_projects()
        
        if not projects:
            self.console.print("[yellow]暂无项目，请先创建新小说[/yellow]")
            return
        
        self.console.print("\n[bold]现有项目:[/bold]")
        for i, name in enumerate(projects, 1):
            self.console.print(f"  [cyan]{i}.[/cyan] {name}")
        
        choice = Prompt.ask("选择项目编号")
        try:
            idx = int(choice) - 1
            project_name = projects[idx]
        except (ValueError, IndexError):
            self.console.print("[yellow]无效选择[/yellow]")
            return
        
        # 加载项目
        project = self.context_manager.load_project(project_name)
        self.console.print(f"\n[green]✓[/green] 已加载: {project_name}")
        self.console.print(f"  当前阶段: {project.current_stage}")
        self.console.print(f"  进度: 第{project.current_volume}卷 第{project.current_chapter}章")
        
        # 显示项目菜单
        self._show_project_menu()
    
    def _show_project_menu(self):
        """项目操作菜单"""
        while True:
            self.console.print("\n[bold]项目操作:[/bold]")
            self.console.print("  [cyan]1.[/cyan] 生成/修改总纲")
            self.console.print("  [cyan]2.[/cyan] 生成粗纲")
            self.console.print("  [cyan]3.[/cyan] 生成细纲")
            self.console.print("  [cyan]4.[/cyan] 生成正文")
            self.console.print("  [cyan]5.[/cyan] 润色正文")
            self.console.print("  [cyan]6.[/cyan] 学习规则")
            self.console.print("  [cyan]b.[/cyan] 返回主菜单")
            
            choice = Prompt.ask("选择")
            
            if choice == "1":
                # 读取现有总纲
                existing = self.context_manager.read_file("master_outline.md")
                if existing:
                    self.console.print(Panel(Markdown(existing), title="现有总纲"))
                    if Confirm.ask("是否修改？"):
                        feedback = Prompt.ask("修改意见")
                        new_outline = self.master_generator.refine(existing, feedback)
                        self.console.print(Panel(Markdown(new_outline)))
                        if Confirm.ask("保存？"):
                            self.master_generator.save_outline(new_outline)
                else:
                    self._generate_master_outline()
                    
            elif choice == "2":
                master = self.context_manager.read_file("master_outline.md")
                if master:
                    self._generate_volume_outline(master)
                else:
                    self.console.print("[yellow]请先生成总纲[/yellow]")
                    
            elif choice == "4":
                self._generate_content()
                
            elif choice == "5":
                self._polish_content()
                
            elif choice == "6":
                self._learn_rules()
                
            elif choice == "b":
                break
    
    def _generate_content(self):
        """生成正文"""
        chapter_num = int(Prompt.ask("章节号", default="1"))
        
        # 尝试读取细纲
        outline_content = Prompt.ask("输入章节细纲（或留空使用保存的）")
        
        if not outline_content:
            self.console.print("[yellow]请提供章节细纲[/yellow]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("生成正文中...", total=None)
            content = self.content_generator.generate(
                chapter_outline=outline_content
            )
        
        word_count = count_words(content)
        self.console.print(f"\n[bold]第{chapter_num}章 ({word_count}字):[/bold]")
        self.console.print(Panel(content[:2000] + "...\n[dim](显示前2000字)[/dim]"))
        
        if Confirm.ask("保存此章节？"):
            path = self.content_generator.save_content(content, chapter_num, "raw")
            self.console.print(f"[green]✓[/green] 已保存: {path}")
            
            if Confirm.ask("是否立即润色？"):
                self._polish_chapter(content, chapter_num)
    
    def _polish_chapter(self, content: str, chapter_num: int):
        """润色单章"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("润色中...", total=None)
            polished = self.polish_processor.polish(content)
        
        word_count = count_words(polished)
        self.console.print(f"\n[bold]润色后 ({word_count}字):[/bold]")
        self.console.print(Panel(polished[:2000] + "..."))
        
        # 保存版本
        paths = self.polish_processor.save_versions(content, polished, chapter_num)
        self.console.print(f"[green]✓[/green] 版本已保存")
        self.console.print(f"  原始版: {paths['raw']}")
        self.console.print(f"  润色版: {paths['polished']}")
        
        self.console.print("\n[dim]如需人工修改，请编辑润色版文件后保存为 ch{:03d}_final.md[/dim]".format(chapter_num))
    
    def _polish_content(self):
        """润色正文"""
        chapter_num = int(Prompt.ask("章节号", default="1"))
        
        # 读取原始版
        raw_content = self.context_manager.read_file(
            "content", f"ch{chapter_num:03d}_raw.md"
        )
        
        if not raw_content:
            self.console.print("[yellow]未找到该章节的原始版[/yellow]")
            return
        
        self._polish_chapter(raw_content, chapter_num)
    
    def _learn_rules(self):
        """学习规则"""
        self.console.print("\n[bold]规则学习[/bold]")
        self.console.print("扫描所有章节，从人工修改中学习规则...\n")
        
        learned = self.rule_learner.learn_from_all_chapters()
        
        if learned:
            self.console.print(f"[green]✓[/green] 学习到 {len(learned)} 条新规则")
            for chapter, rules in learned.items():
                self.console.print(f"\n[cyan]第{chapter}章:[/cyan]")
                self.console.print(rules[:500] + "...")
        else:
            self.console.print("[yellow]未发现需要学习的修改[/yellow]")
            self.console.print("[dim]请先对润色版进行人工修改并保存为 _final.md[/dim]")
    
    def show_settings(self):
        """显示设置菜单"""
        while True:
            self.console.print("\n[bold]⚙️ 设置[/bold]")
            model_info = get_model_by_name(self.llm.model_name)
            self.console.print(f"  当前模型: [cyan]{self.llm.model_name}[/cyan] ({model_info['desc']})")
            self.console.print(f"  项目目录: {PROJECTS_DIR}")
            
            # 统计信息
            projects = self.context_manager.list_projects()
            learned = self.prompt_manager.get_learned_rules()
            rule_count = learned.count("## 规则") if learned else 0
            self.console.print(f"  项目数量: {len(projects)}")
            self.console.print(f"  已学习规则数: {rule_count}")
            
            # Token 使用
            usage = get_usage_summary()
            if usage["call_count"] > 0:
                self.console.print(f"  本次Token: {usage['total_tokens']:,} (${usage['total_cost_usd']:.4f})")
            
            self.console.print("\n[bold]操作:[/bold]")
            self.console.print("  [cyan]1.[/cyan] 切换模型")
            self.console.print("  [cyan]2.[/cyan] 项目管理")
            self.console.print("  [cyan]3.[/cyan] 查看所有项目")
            self.console.print("  [cyan]4.[/cyan] 删除项目")
            self.console.print("  [cyan]b.[/cyan] 返回主菜单")
            
            choice = Prompt.ask("选择")
            
            if choice == "1":
                self._select_model()
            elif choice == "2":
                self._manage_projects()
            elif choice == "3":
                self._list_all_projects()
            elif choice == "4":
                self._delete_project()
            elif choice == "b":
                break
    
    def _select_model(self):
        """选择模型"""
        self.console.print("\n[bold]🤖 可用模型:[/bold]")
        models = get_available_models()
        
        for i, model in enumerate(models, 1):
            tier_color = "green" if model["tier"] == "pro" else "yellow"
            self.console.print(f"  [cyan]{i}.[/cyan] [{tier_color}]{model['name']}[/{tier_color}]")
            self.console.print(f"      {model['desc']}")
        
        choice = Prompt.ask("\n选择模型编号 (留空取消)", default="")
        if not choice:
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                new_model = models[idx]["name"]
                # 重新创建客户端
                self.llm = GeminiClient(model_name=new_model)
                self._init_pipeline()  # 重新初始化流水线
                self.console.print(f"[green]✓[/green] 已切换到: {new_model}")
            else:
                self.console.print("[yellow]无效选择[/yellow]")
        except ValueError:
            self.console.print("[yellow]请输入数字[/yellow]")
    
    def _list_all_projects(self):
        """列出所有项目详情"""
        projects = self.context_manager.list_projects()
        
        if not projects:
            self.console.print("[yellow]暂无项目[/yellow]")
            return
        
        self.console.print("\n[bold]📚 所有项目:[/bold]\n")
        
        for name in projects:
            project_path = PROJECTS_DIR / name
            config_path = project_path / "config.json"
            
            if config_path.exists():
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.console.print(f"[cyan]{name}[/cyan]")
                self.console.print(f"  阶段: {config.get('current_stage', '未知')}")
                self.console.print(f"  进度: 第{config.get('current_volume', 1)}卷 第{config.get('current_chapter', 1)}章")
                self.console.print(f"  创建: {config.get('created_at', '未知')[:10]}")
                
                # 统计文件
                content_dir = project_path / "content"
                if content_dir.exists():
                    chapter_count = len(list(content_dir.glob("*.md")))
                    self.console.print(f"  已生成章节: {chapter_count}")
                self.console.print()
    
    def _manage_projects(self):
        """项目管理"""
        projects = self.context_manager.list_projects()
        
        if not projects:
            self.console.print("[yellow]暂无项目[/yellow]")
            return
        
        self.console.print("\n[bold]项目列表:[/bold]")
        for i, name in enumerate(projects, 1):
            current = " [当前]" if (self.context_manager.current_config and 
                                   self.context_manager.current_config.name == name) else ""
            self.console.print(f"  [cyan]{i}.[/cyan] {name}{current}")
        
        choice = Prompt.ask("\n选择要切换的项目编号")
        try:
            idx = int(choice) - 1
            project_name = projects[idx]
            project = self.context_manager.load_project(project_name)
            self.console.print(f"[green]✓[/green] 已切换到: {project_name}")
        except (ValueError, IndexError):
            self.console.print("[yellow]无效选择[/yellow]")
    
    def _delete_project(self):
        """删除项目"""
        import shutil
        
        projects = self.context_manager.list_projects()
        
        if not projects:
            self.console.print("[yellow]暂无项目[/yellow]")
            return
        
        self.console.print("\n[bold red]⚠️ 删除项目[/bold red]")
        for i, name in enumerate(projects, 1):
            self.console.print(f"  [cyan]{i}.[/cyan] {name}")
        
        choice = Prompt.ask("\n选择要删除的项目编号 (此操作不可恢复!)")
        try:
            idx = int(choice) - 1
            project_name = projects[idx]
            
            if Confirm.ask(f"[red]确定要删除项目 '{project_name}' 吗？[/red]"):
                project_path = PROJECTS_DIR / project_name
                shutil.rmtree(project_path)
                self.console.print(f"[green]✓[/green] 已删除: {project_name}")
        except (ValueError, IndexError):
            self.console.print("[yellow]无效选择[/yellow]")


def main():
    """主函数"""
    agent = NovelAgent()
    agent.run()


if __name__ == "__main__":
    main()
