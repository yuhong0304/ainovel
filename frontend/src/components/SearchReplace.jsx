import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { X, Search, Replace, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';

export default function SearchReplace({
    isOpen,
    onClose,
    content = '',
    onReplace
}) {
    const [searchText, setSearchText] = useState('');
    const [replaceText, setReplaceText] = useState('');
    const [showReplace, setShowReplace] = useState(false);
    const [matches, setMatches] = useState([]);
    const [currentMatch, setCurrentMatch] = useState(0);
    const [caseSensitive, setCaseSensitive] = useState(false);
    const searchInputRef = useRef(null);

    // 聚焦搜索输入框
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => searchInputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    // 搜索逻辑
    useEffect(() => {
        if (!searchText.trim()) {
            setMatches([]);
            return;
        }

        const flags = caseSensitive ? 'g' : 'gi';
        const regex = new RegExp(escapeRegex(searchText), flags);
        const foundMatches = [];
        let match;

        while ((match = regex.exec(content)) !== null) {
            foundMatches.push({
                index: match.index,
                text: match[0]
            });
        }

        setMatches(foundMatches);
        setCurrentMatch(foundMatches.length > 0 ? 0 : -1);
    }, [searchText, content, caseSensitive]);

    const escapeRegex = (str) => {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    };

    const goToNext = () => {
        if (matches.length > 0) {
            setCurrentMatch((prev) => (prev + 1) % matches.length);
        }
    };

    const goToPrev = () => {
        if (matches.length > 0) {
            setCurrentMatch((prev) => (prev - 1 + matches.length) % matches.length);
        }
    };

    const handleReplaceCurrent = () => {
        if (matches.length === 0 || currentMatch < 0) return;

        const match = matches[currentMatch];
        const newContent =
            content.substring(0, match.index) +
            replaceText +
            content.substring(match.index + match.text.length);

        onReplace?.(newContent);
    };

    const handleReplaceAll = () => {
        if (!searchText.trim()) return;

        const flags = caseSensitive ? 'g' : 'gi';
        const regex = new RegExp(escapeRegex(searchText), flags);
        const newContent = content.replace(regex, replaceText);

        onReplace?.(newContent);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            goToNext();
        } else if (e.key === 'Escape') {
            onClose?.();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="absolute top-4 right-4 z-50 w-80 bg-card border rounded-lg shadow-xl p-3 space-y-2">
            {/* 搜索行 */}
            <div className="flex items-center gap-2">
                <div className="relative flex-1">
                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        ref={searchInputRef}
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="搜索..."
                        className="pl-8 pr-16"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2">
                        <Badge variant="outline" className="text-xs">
                            {matches.length > 0 ? `${currentMatch + 1}/${matches.length}` : '0'}
                        </Badge>
                    </div>
                </div>

                <Button size="icon" variant="ghost" onClick={goToPrev} disabled={matches.length === 0}>
                    <ChevronUp className="w-4 h-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={goToNext} disabled={matches.length === 0}>
                    <ChevronDown className="w-4 h-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={onClose}>
                    <X className="w-4 h-4" />
                </Button>
            </div>

            {/* 替换行 */}
            <div className="flex items-center gap-2">
                <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowReplace(!showReplace)}
                    className="gap-1"
                >
                    <Replace className="w-3 h-3" />
                    替换
                </Button>

                <Button
                    size="sm"
                    variant={caseSensitive ? 'default' : 'outline'}
                    onClick={() => setCaseSensitive(!caseSensitive)}
                    className="text-xs"
                >
                    Aa
                </Button>
            </div>

            {/* 替换输入 */}
            {showReplace && (
                <div className="space-y-2 pt-2 border-t">
                    <Input
                        value={replaceText}
                        onChange={(e) => setReplaceText(e.target.value)}
                        placeholder="替换为..."
                    />
                    <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={handleReplaceCurrent} disabled={matches.length === 0}>
                            替换
                        </Button>
                        <Button size="sm" variant="outline" onClick={handleReplaceAll} disabled={matches.length === 0}>
                            全部替换
                        </Button>
                        <Badge variant="secondary" className="ml-auto">
                            {matches.length} 处匹配
                        </Badge>
                    </div>
                </div>
            )}
        </div>
    );
}
