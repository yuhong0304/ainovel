import React, { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    MessageCircle, Send, X, Loader2, User, Bot, Sparkles,
    Lightbulb, PenTool, BookOpen, Wand2
} from 'lucide-react';

export default function AIChatSidebar({ isOpen, onClose }) {
    const { projectId } = useParams();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // 快捷提示
    const quickPrompts = [
        { icon: Lightbulb, text: '给我一些角色创意' },
        { icon: PenTool, text: '帮我润色这段文字' },
        { icon: BookOpen, text: '分析当前大纲的问题' },
        { icon: Wand2, text: '生成一个精彩的开场' },
    ];

    // 自动滚动到底部
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // 聚焦输入框
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    const handleSend = async (text = input) => {
        if (!text.trim() || isLoading) return;

        const userMessage = { role: 'user', content: text };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // 调用 AI 聊天 API
            const { data } = await client.post('/api/chat', {
                project: projectId,
                message: text,
                history: messages.slice(-10) // 最近 10 条作为上下文
            });

            const assistantMessage = { role: 'assistant', content: data.response };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (e) {
            const errorMessage = {
                role: 'assistant',
                content: `抱歉，发生了错误: ${e.response?.data?.error || e.message}`,
                isError: true
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed right-0 top-0 h-screen w-96 bg-card border-l shadow-xl z-50 flex flex-col">
            {/* Header */}
            <div className="px-4 py-3 border-b flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-primary/10 rounded-lg">
                        <Sparkles className="w-4 h-4 text-primary" />
                    </div>
                    <span className="font-medium">AI 写作助手</span>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose}>
                    <X className="w-4 h-4" />
                </Button>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {messages.length === 0 && (
                        <div className="text-center py-8">
                            <Sparkles className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                            <p className="text-muted-foreground text-sm">
                                有什么我可以帮助你的？
                            </p>
                            <div className="mt-6 grid grid-cols-2 gap-2">
                                {quickPrompts.map((prompt, idx) => {
                                    const Icon = prompt.icon;
                                    return (
                                        <button
                                            key={idx}
                                            onClick={() => handleSend(prompt.text)}
                                            className="flex items-center gap-2 p-2 text-xs text-left rounded-lg border hover:bg-muted transition-colors"
                                        >
                                            <Icon className="w-3 h-3 text-primary" />
                                            {prompt.text}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                    <Bot className="w-4 h-4 text-primary" />
                                </div>
                            )}
                            <div
                                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${msg.role === 'user'
                                        ? 'bg-primary text-primary-foreground'
                                        : msg.isError
                                            ? 'bg-destructive/10 text-destructive'
                                            : 'bg-muted'
                                    }`}
                            >
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                            </div>
                            {msg.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                                    <User className="w-4 h-4" />
                                </div>
                            )}
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                                <Bot className="w-4 h-4 text-primary" />
                            </div>
                            <div className="bg-muted rounded-lg px-3 py-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-4 border-t">
                <div className="flex gap-2">
                    <Input
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="输入消息..."
                        disabled={isLoading}
                    />
                    <Button onClick={() => handleSend()} disabled={isLoading || !input.trim()}>
                        <Send className="w-4 h-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
