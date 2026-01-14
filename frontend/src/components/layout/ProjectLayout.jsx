import React, { useEffect, useState } from 'react';
import { Outlet, useParams, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import AIChatSidebar from '@/components/AIChatSidebar';
import useProjectStore from '@/store/useProjectStore';
import { Button } from "@/components/ui/button";
import { Loader2, MessageCircle } from "lucide-react";

export default function ProjectLayout() {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const { loadProject, currentProject, isLoading, error } = useProjectStore();
    const [isChatOpen, setIsChatOpen] = useState(false);

    useEffect(() => {
        if (projectId) {
            loadProject(projectId);
        }
    }, [projectId]);

    if (isLoading && !currentProject) {
        return (
            <div className="h-screen w-screen flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-screen w-screen flex flex-col items-center justify-center space-y-4">
                <div className="text-destructive font-bold text-lg">无法加载项目</div>
                <div className="text-muted-foreground">{error}</div>
                <button onClick={() => navigate('/')} className="underline">返回首页</button>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-auto bg-muted/10 relative">
                <Outlet />

                {/* AI Chat Toggle Button */}
                <Button
                    onClick={() => setIsChatOpen(true)}
                    className="fixed bottom-6 right-6 rounded-full w-14 h-14 shadow-lg z-40"
                    size="icon"
                >
                    <MessageCircle className="w-6 h-6" />
                </Button>
            </main>

            {/* AI Chat Sidebar */}
            <AIChatSidebar
                isOpen={isChatOpen}
                onClose={() => setIsChatOpen(false)}
            />
        </div>
    );
}

