'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Link from 'next/link';
import { Trash2, AlertTriangle, Sparkles, Loader2 } from 'lucide-react';
import { useGeneration } from '../../contexts/GenerationContext';

export default function KnowledgePage() {
    const { isGenerating, startGeneration, generationStatus } = useGeneration();
    const [questions, setQuestions] = useState([]);
    const [knowledgePoints, setKnowledgePoints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [genTarget, setGenTarget] = useState(null);
    const [genCount, setGenCount] = useState(10);

    useEffect(() => {
        async function fetchData() {
            try {
                // Fetch all questions to get unique knowledge points
                const questionsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/questions`);
                if (questionsRes.ok) {
                    const data = await questionsRes.json();
                    setQuestions(data);

                    // Extract unique knowledge points
                    const pointsMap = new Map();
                    data.forEach(q => {
                        const point = q.knowledge_point || '未分类';
                        if (!pointsMap.has(point)) {
                            pointsMap.set(point, { count: 0, topics: new Set() });
                        }
                        const entry = pointsMap.get(point);
                        entry.count++;
                    });

                    const pointsList = Array.from(pointsMap.entries()).map(([point, info]) => ({
                        name: point,
                        questionCount: info.count,
                    })).sort((a, b) => b.questionCount - a.questionCount);

                    setKnowledgePoints(pointsList);
                }

                // Also try to fetch knowledge base files
                const suggestionsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/suggestions`);
                if (suggestionsRes.ok) {
                    // This would be parsed knowledge from markdown files
                }
            } catch (e) {
                console.error('Failed to load knowledge data', e);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const handleDelete = async (name) => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/knowledge?name=${encodeURIComponent(name)}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                setKnowledgePoints(prev => prev.filter(p => p.name !== name));
                setQuestions(prev => prev.filter(q => q.knowledge_point !== name));
                setDeleteConfirm(null);
            }
        } catch (e) {
            console.error('Failed to delete knowledge point', e);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-6xl mx-auto space-y-8">

                <header className="flex justify-between items-center">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <h1 className="text-3xl font-bold tracking-tight">📚 知识点库</h1>
                            {isGenerating && (
                                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded-full animate-pulse border border-primary/20">
                                    <Loader2 className="w-2.5 h-2.5 animate-spin" />
                                    {generationStatus || 'AI 正在出题...'}
                                </div>
                            )}
                        </div>
                        <p className="text-muted-foreground">查看所有已收录的考点和知识点</p>
                    </div>
                    <Link href="/">
                        <Button variant="outline">← 返回首页</Button>
                    </Link>
                </header>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium opacity-90">题目总数</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-4xl font-bold">{questions.length}</div>
                            <p className="text-xs opacity-80 mt-1">已入库题目</p>
                        </CardContent>
                    </Card>

                    <Card className="bg-gradient-to-br from-green-500 to-emerald-600 text-white">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium opacity-90">知识点数</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-4xl font-bold">{knowledgePoints.length}</div>
                            <p className="text-xs opacity-80 mt-1">不同考点类别</p>
                        </CardContent>
                    </Card>

                    <Card className="bg-gradient-to-br from-purple-500 to-pink-600 text-white">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium opacity-90">平均题量</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-4xl font-bold">
                                {knowledgePoints.length > 0 ? Math.round(questions.length / knowledgePoints.length) : 0}
                            </div>
                            <p className="text-xs opacity-80 mt-1">每个知识点</p>
                        </CardContent>
                    </Card>
                </div>

                {/* Knowledge Points List */}
                <Card>
                    <CardHeader>
                        <CardTitle>知识点详情</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {knowledgePoints.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground">
                                <p className="mb-4">暂无知识点数据</p>
                                <Link href="/">
                                    <Button>去生成题目</Button>
                                </Link>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {knowledgePoints.map((point, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center justify-between p-4 bg-muted/50 rounded-lg hover:bg-muted transition"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
                                                {idx + 1}
                                            </div>
                                            <div>
                                                <div className="font-medium">{point.name}</div>
                                                <div className="text-xs text-muted-foreground">{point.questionCount} 道题目</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="hidden sm:block w-24 bg-secondary rounded-full h-2">
                                                <div
                                                    className="bg-primary h-2 rounded-full transition-all duration-500"
                                                    style={{ width: `${Math.min((point.questionCount / questions.length) * 100 * 5, 100)}%` }}
                                                ></div>
                                            </div>
                                            <div className="flex gap-1">
                                                <Link href={`/?topic=${encodeURIComponent(point.name)}`}>
                                                    <Button size="sm" variant="outline" className="h-8">练习</Button>
                                                </Link>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-8 gap-1 border-primary/20 text-primary hover:bg-primary/5"
                                                    disabled={isGenerating}
                                                    onClick={() => setGenTarget(point.name)}
                                                >
                                                    <Sparkles className="w-3.5 h-3.5" />
                                                    生成
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                                                    onClick={() => setDeleteConfirm(point.name)}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Generate More Questions Modal */}
                {genTarget && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <Card className="max-w-md w-full shadow-2xl border-primary/20 animate-in zoom-in-95 duration-200">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-primary" />
                                    补充题目库
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="p-4 bg-primary/5 border border-primary/10 rounded-lg">
                                    <p className="text-foreground font-medium mb-1 line-clamp-1">
                                        针对考点：<span className="text-primary">“{genTarget}”</span>
                                    </p>
                                    <p className="text-muted-foreground text-xs leading-relaxed">
                                        新题目将严格遵循 N1 实战难度，包含强力干扰项，并自动同步至你的学习计划。
                                    </p>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-sm font-bold">选择生成数量</label>
                                    <div className="flex flex-wrap gap-2">
                                        {[5, 10, 15, 20].map(count => (
                                            <button
                                                key={count}
                                                onClick={() => setGenCount(count)}
                                                className={`px-4 py-2 rounded-md border text-sm font-medium transition ${genCount === count
                                                    ? 'bg-primary text-primary-foreground border-primary'
                                                    : 'bg-background border-input hover:bg-accent'
                                                    }`}
                                            >
                                                {count} 题
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex justify-end gap-3 pt-2">
                                    <Button variant="outline" onClick={() => setGenTarget(null)}>
                                        取消
                                    </Button>
                                    <Button onClick={() => {
                                        startGeneration(genTarget, genCount);
                                        setGenTarget(null);
                                    }}>
                                        立即生成
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Delete Confirmation Dialog */}
                {deleteConfirm && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <Card className="max-w-md w-full shadow-2xl border-destructive/20 animate-in zoom-in-95 duration-200">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-destructive">
                                    <AlertTriangle className="w-5 h-5 text-destructive" />
                                    确认彻底移除？
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="p-4 bg-destructive/5 border border-destructive/10 rounded-lg">
                                    <p className="text-foreground font-medium mb-1">
                                        确定要删除知识点 <span className="underline decoration-destructive">“{deleteConfirm}”</span> 吗？
                                    </p>
                                    <p className="text-muted-foreground text-xs leading-relaxed">
                                        此操作将**从数据库中永久移除该考点关联的所有题目**，并销毁相应的本地 JSON 缓存。相关的做题记录、错题本数据也将一并清除，且不可撤销。
                                    </p>
                                </div>
                                <div className="flex justify-end gap-3 pt-2">
                                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
                                        取消
                                    </Button>
                                    <Button variant="destructive" onClick={() => handleDelete(deleteConfirm)}>
                                        确认删除
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Link href="/stats" className="block">
                        <Card className="hover:bg-accent/50 transition cursor-pointer h-full">
                            <CardContent className="flex items-center gap-4 p-6">
                                <div className="text-4xl">📈</div>
                                <div>
                                    <h3 className="font-bold">查看统计</h3>
                                    <p className="text-sm text-muted-foreground">分析错题规律和进步趋势</p>
                                </div>
                            </CardContent>
                        </Card>
                    </Link>
                    <Link href="/wrong-questions" className="block">
                        <Card className="hover:bg-accent/50 transition cursor-pointer h-full">
                            <CardContent className="flex items-center gap-4 p-6">
                                <div className="text-4xl">📖</div>
                                <div>
                                    <h3 className="font-bold">错题复习</h3>
                                    <p className="text-sm text-muted-foreground">重温做错的题目</p>
                                </div>
                            </CardContent>
                        </Card>
                    </Link>
                </div>

            </div>
        </div>
    );
}
