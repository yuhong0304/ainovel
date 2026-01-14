import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '@/api/client';
import StructureTree from './outliner/StructureTree';
import StructureEditor from './outliner/StructureEditor';
import { Loader2 } from 'lucide-react';

export default function Outliner() {
    const { projectId } = useParams();
    const [structure, setStructure] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState('master');

    // New state for generation
    const [isGenerating, setIsGenerating] = useState(false);

    // Fetch structure
    useEffect(() => {
        async function fetchStructure() {
            try {
                setLoading(true);
                const { data } = await client.get(`/api/project/${projectId}/structure`);
                setStructure(data);
            } catch (err) {
                console.error("Failed to fetch structure:", err);
            } finally {
                setLoading(false);
            }
        }
        if (projectId) fetchStructure();
    }, [projectId]);

    const handleSelect = (id) => {
        setSelectedId(id);
    };

    // Helper to find content based on selectedId
    const getSelectedContent = () => {
        if (!structure) return "";

        if (selectedId === 'master') {
            return structure.master_outline || "";
        }

        if (selectedId.startsWith('vol_')) {
            const parts = selectedId.split('_');
            // vol_1
            const volNum = parseInt(parts[1]);
            const vol = structure.volumes.find(v => v.vol_num === volNum);

            if (parts.includes('script')) {
                // vol_1_script_2
                const scriptNum = parseInt(parts[3]);
                const script = vol?.scripts?.find(s => s.script_num === scriptNum);
                return script?.content || "";
            }

            return vol?.content || "";
        }

        return "";
    };

    const handleSave = async (content) => {
        try {
            let type = '';
            let filename = '';

            if (selectedId === 'master') {
                type = 'master';
            } else if (selectedId.startsWith('vol_')) {
                const parts = selectedId.split('_');
                const volNum = parseInt(parts[1]);
                const vol = structure.volumes.find(v => v.vol_num === volNum);

                if (parts.includes('script')) {
                    type = 'script';
                    const scriptNum = parseInt(parts[3]);
                    const script = vol?.scripts?.find(s => s.script_num === scriptNum);
                    filename = script?.filename;
                } else {
                    type = 'volume';
                    filename = vol?.filename;
                }
            }

            if (!type) return;

            await client.post(`/api/project/${projectId}/structure/node`, {
                type,
                filename,
                content
            });

            // Update local state without full refresh to keep cursor/ui stable
            // Deep clone structure to modify
            const newStructure = JSON.parse(JSON.stringify(structure));
            if (type === 'master') {
                newStructure.master_outline = content;
            } else if (type === 'volume') {
                // find and update
                const parts = selectedId.split('_');
                const volNum = parseInt(parts[1]);
                const v = newStructure.volumes.find(v => v.vol_num === volNum);
                if (v) v.content = content;
            } else if (type === 'script') {
                const parts = selectedId.split('_');
                const volNum = parseInt(parts[1]);
                const scriptNum = parseInt(parts[3]);
                const v = newStructure.volumes.find(v => v.vol_num === volNum);
                const s = v?.scripts?.find(s => s.script_num === scriptNum);
                if (s) s.content = content;
            }
            setStructure(newStructure);

            // alert("保存成功"); // Optional: toast would be better
        } catch (err) {
            console.error(err);
            alert("保存失败: " + err.message);
        }
    };

    const handleGenerate = async () => {
        if (!structure?.master_outline) {
            alert("请先填写总纲内容并保存");
            return;
        }

        // const volCount = prompt("预计生成多少卷？(建议 4 卷)", "4");
        // Use simple window prompt for now, can be replaced by Dialog later
        // Adding a small delay to ensure UI renders
        await new Promise(r => setTimeout(r, 100));
        const volCount = window.prompt("预计生成多少卷？(建议 4 卷)", "4");

        if (!volCount) return;

        try {
            setIsGenerating(true);

            const { data } = await client.post(`/api/project/${projectId}/structure/generate`, {
                master_outline: structure.master_outline,
                volume_count: parseInt(volCount)
            });

            alert(data.message);
            // Refresh
            const res = await client.get(`/api/project/${projectId}/structure`);
            setStructure(res.data);

        } catch (err) {
            alert("生成失败: " + (err.response?.data?.error || err.message));
        } finally {
            setIsGenerating(false);
        }
    };

    if (loading) {
        return <div className="h-full flex items-center justify-center"><Loader2 className="animate-spin" /></div>;
    }

    return (
        <div className="flex h-full border-t border-l">
            <StructureTree
                structure={structure}
                onSelect={handleSelect}
                selectedId={selectedId}
            />
            <div className="flex-1 h-full overflow-hidden">
                <StructureEditor
                    key={selectedId} // Force re-render on switch
                    content={getSelectedContent()}
                    onSave={handleSave}
                    canGenerate={selectedId === 'master'}
                    onGenerate={handleGenerate}
                    isGenerating={isGenerating}
                />
            </div>
        </div>
    );
}
