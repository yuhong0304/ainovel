import React, { useEffect } from 'react';
import { NavLink, useNavigate, useParams } from 'react-router-dom';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    LayoutDashboard,
    BookOpen,
    PenTool,
    Globe,
    Settings,
    LogOut,
    ChevronsUpDown,
    Plus,
    Download,
    Zap,
    BarChart3
} from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import useProjectStore from '@/store/useProjectStore';

export default function Sidebar() {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const { projects, currentProject, fetchProjects, setCurrentProject } = useProjectStore();

    useEffect(() => {
        fetchProjects();
    }, []);

    const handleSwitchProject = (projectName) => {
        navigate(`/project/${projectName}`);
    };

    return (
        <div className="flex h-screen w-64 flex-col border-r bg-card text-card-foreground">
            {/* Project Switcher Header */}
            <div className="p-4 border-b">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" className="w-full justify-between h-12 px-3">
                            <div className="flex flex-col items-start truncate">
                                <span className="text-xs text-muted-foreground">当前项目</span>
                                <span className="font-bold truncate w-32 text-left">
                                    {currentProject?.name || projectId || "选择项目"}
                                </span>
                            </div>
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56">
                        <DropdownMenuLabel>切换项目</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {projects.map((p) => (
                            <DropdownMenuItem
                                key={p.name}
                                onSelect={() => handleSwitchProject(p.name)}
                                className={cn(p.name === projectId && "bg-accent")}
                            >
                                <span>{p.name}</span>
                                {p.title && <span className="ml-2 text-xs text-muted-foreground truncate">- {p.title}</span>}
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onSelect={() => navigate('/')}>
                            <Plus className="mr-2 h-4 w-4" />
                            创建新项目
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            {/* Navigation Links */}
            <nav className="flex-1 p-4 space-y-2">
                <NavItem to={`/project/${projectId}`} end icon={<LayoutDashboard />}>概览</NavItem>
                <NavItem to={`/project/${projectId}/write`} icon={<PenTool />}>写作工作室</NavItem>
                <NavItem to={`/project/${projectId}/world`} icon={<Globe />}>世界观</NavItem>

                <div className="py-2">
                    <div className="border-t border-border" />
                </div>

                <NavItem to={`/project/${projectId}/export`} icon={<Download />}>导出</NavItem>
                <NavItem to={`/project/${projectId}/batch`} icon={<Zap />}>批量生成</NavItem>
                <NavItem to={`/project/${projectId}/stats`} icon={<BarChart3 />}>统计</NavItem>
                <NavItem to={`/project/${projectId}/settings`} icon={<Settings />}>设置</NavItem>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t space-y-2">
                <ThemeToggle />
                <Button variant="ghost" className="w-full justify-start text-muted-foreground" onClick={() => navigate('/')}>
                    <LogOut className="mr-2 h-4 w-4" />
                    返回主页
                </Button>
            </div>
        </div>
    );
}

function NavItem({ to, icon, children, end = false }) {
    return (
        <NavLink
            to={to}
            end={end}
            className={({ isActive }) => cn(
                "flex items-center px-3 py-2 rounded-md transition-colors hover:bg-accent hover:text-accent-foreground",
                isActive ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground"
            )}
        >
            {React.cloneElement(icon, { className: "mr-3 h-4 w-4" })}
            <span>{children}</span>
        </NavLink>
    );
}

// 主题切换组件
function ThemeToggle() {
    const [isDark, setIsDark] = React.useState(true);

    const toggleTheme = () => {
        const newDark = !isDark;
        setIsDark(newDark);
        document.documentElement.classList.toggle('dark', newDark);
    };

    return (
        <Button variant="ghost" className="w-full justify-start text-muted-foreground" onClick={toggleTheme}>
            {isDark ? (
                <>
                    <span className="mr-2">☀️</span>
                    切换亮色
                </>
            ) : (
                <>
                    <span className="mr-2">🌙</span>
                    切换暗色
                </>
            )}
        </Button>
    );
}

