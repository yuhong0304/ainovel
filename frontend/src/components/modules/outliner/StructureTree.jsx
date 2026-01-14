import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronRight, ChevronDown, FileText, Folder, Book } from 'lucide-react';

export default function StructureTree({ structure, onSelect, selectedId }) {
    const [expanded, setExpanded] = useState({});

    const toggleExpand = (id, e) => {
        e.stopPropagation();
        setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
    };

    // Auto-expand first volume on load
    React.useEffect(() => {
        if (structure?.volumes?.length > 0) {
            const firstVolId = `vol_${structure.volumes[0].vol_num}`;
            setExpanded(prev => ({ ...prev, [firstVolId]: true }));
        }
    }, [structure]);

    const TreeItem = ({ id, label, icon: Icon, level = 0, hasChildren = false, children }) => {
        const isExpanded = expanded[id];
        const isSelected = selectedId === id;

        return (
            <div>
                <div
                    className={cn(
                        "flex items-center py-1 px-2 cursor-pointer hover:bg-accent rounded-sm text-sm transition-colors",
                        isSelected && "bg-primary/20 text-primary font-medium"
                    )}
                    style={{ paddingLeft: `${level * 12 + 8}px` }}
                    onClick={() => onSelect(id)}
                >
                    {hasChildren ? (
                        <div
                            className="p-1 -ml-1 hover:bg-muted rounded-sm mr-1"
                            onClick={(e) => toggleExpand(id, e)}
                        >
                            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        </div>
                    ) : <div className="w-4 mr-1" />}

                    <Icon className="w-4 h-4 mr-2 opacity-70" />
                    <span className="truncate">{label}</span>
                </div>

                {isExpanded && children}
            </div>
        );
    };

    if (!structure) return <div className="p-4 text-sm text-muted-foreground">加载中...</div>;

    return (
        <div className="w-64 border-r bg-card h-full overflow-y-auto py-2">
            <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                小说结构
            </div>

            {/* Master Outline Node */}
            <TreeItem
                id="master"
                label="总纲 (Master Outline)"
                icon={Book}
                onSelect={() => onSelect('master')}
            />

            {/* Volumes */}
            {(structure.volumes || []).map(vol => (
                <TreeItem
                    key={vol.vol_num}
                    id={`vol_${vol.vol_num}`}
                    label={`${vol.title}`}
                    icon={Folder}
                    hasChildren={vol.scripts && vol.scripts.length > 0}
                >
                    {/* Scripts within Volume */}
                    {(vol.scripts || []).map(script => (
                        <TreeItem
                            key={script.script_num}
                            id={`vol_${vol.vol_num}_script_${script.script_num}`}
                            label={script.title}
                            icon={FileText}
                            level={1}
                        />
                    ))}
                </TreeItem>
            ))}
        </div>
    );
}
