'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Link from 'next/link';
import { Trash2, AlertTriangle, Sparkles, Loader2, Play, Info, X, Zap } from 'lucide-react';
import { useGeneration } from '../../contexts/GenerationContext';
import { getAllQuestions, getSuggestions, deleteKnowledge, getKnowledgeDetail } from '../../lib/api';
import KnowledgeDetailModal from '../../components/KnowledgeDetailModal';

export default function KnowledgePage() {

    const router = useRouter();
    const { isGenerating, setIsGenerating, startGeneration, generationStatus } = useGeneration();
    const [questions, setQuestions] = useState([]);
    const [knowledgePoints, setKnowledgePoints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [practiceLoading, setPracticeLoading] = useState(null); // Track which point is being prepped for practice
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [genTarget, setGenTarget] = useState(null);
    const [genCount, setGenCount] = useState(10);
    const [selectedDetail, setSelectedDetail] = useState(null);
    const [detailLoading, setDetailLoading] = useState(null);
    const [batchStatus, setBatchStatus] = useState(null); // { current, total, topic }

    useEffect(() => {
        async function fetchData() {
            try {
                // 1. Fetch suggestions (the master list from MD files)
                const suggestions = await getSuggestions();

                // 2. Fetch all questions (to get counts)
                const allQs = await getAllQuestions();
                setQuestions(allQs);

                // 3. Extract counts from questions
                const countsMap = new Map();
                allQs.forEach(q => {
                    const point = q.knowledge_point || '未分类';
                    countsMap.set(point, (countsMap.get(point) || 0) + 1);
                });

                // 4. Build the final list
                // Start with suggestions from MD
                const masterList = suggestions.map(s => ({
                    name: s.point,
                    description: s.description,
                    questionCount: countsMap.get(s.point) || 0,
                    source: s.source_file
                }));

                // Add any points that exist in DB but NOT in MD
                const mdPointNames = new Set(suggestions.map(s => s.point));
                countsMap.forEach((count, name) => {
                    if (!mdPointNames.has(name)) {
                        masterList.push({
                            name: name,
                            description: '数据库中存在的记录',
                            questionCount: count,
                            source: 'Database'
                        });
                    }
                });

                // Sort: Most questions first, then alphabetical
                masterList.sort((a, b) => {
                    if (b.questionCount !== a.questionCount) {
                        return b.questionCount - a.questionCount;
                    }
                    return a.name.localeCompare(b.name);
                });

                setKnowledgePoints(masterList);
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
            await deleteKnowledge(name);
            setKnowledgePoints(prev => prev.filter(p => p.name !== name));
            setQuestions(prev => prev.filter(q => q.knowledge_point !== name));
            setDeleteConfirm(null);
        } catch (e) {
            console.error('Failed to delete knowledge point', e);
        }
    };

    const handleBatchGenerate = async () => {
        const emptyPoints = knowledgePoints.filter(p => p.questionCount === 0);
        if (emptyPoints.length === 0) return;

        if (!window.confirm(`确认要为 ${emptyPoints.length} 个知识点一键生成题目吗？\n这将由于 AI 处理量大而耗费较多时间，请保持浏览器窗口开启。`)) return;

        setIsGenerating(true);
        try {
            for (let i = 0; i < emptyPoints.length; i++) {
                const point = emptyPoints[i];
                setBatchStatus({ current: i + 1, total: emptyPoints.length, topic: point.name });
                try {
                    await startGeneration(point.name, 10, true);
                } catch (e) {
                    console.error(`Batch failed for ${point.name}`, e);
                }
            }
            setBatchStatus(null);
            alert('批量补全完成！页面将刷新同步数据。');
            window.location.reload();
        } finally {
            setIsGenerating(false);
            setBatchStatus(null);
        }
    };

    const handleQuickGenerate = (topicName) => {
        if (isGenerating) return;
        startGeneration(topicName, 10);
    };

    const handlePractice = async (topicName) => {
        setPracticeLoading(topicName);
        try {
            const topicQuestions = await getAllQuestions(topicName);
            if (topicQuestions.length > 0) {
                localStorage.setItem('currentQuestions', JSON.stringify(topicQuestions));
                localStorage.setItem('currentTopic', topicName);
                router.push('/quiz/session');
            } else {
                // If no questions, redirect to generator with topic pre-filled
                router.push(`/?topic=${encodeURIComponent(topicName)}`);
            }
        } catch (e) {
            console.error('Failed to start practice', e);
            router.push(`/?topic=${encodeURIComponent(topicName)}`);
        } finally {
            setPracticeLoading(null);
        }
    };

    const handleShowDetail = async (name) => {
        setDetailLoading(name);
        try {
            const detail = await getKnowledgeDetail(name);
            setSelectedDetail(detail);
        } catch (e) {
            console.error('Failed to load detail', e);
            // Fallback for user created or uncategorized
            setSelectedDetail({
                point: name,
                description: '暂无详细解析内容，可能是手动添加或未分类的知识点。'
            });
        } finally {
            setDetailLoading(null);
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
        <div className="min-h-screen bg-background p-4 md:p-8">
            <div className="max-w-6xl mx-auto space-y-8">

                <header className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">📚 知识点库</h1>
                            {isGenerating && (
                                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded-full animate-pulse border border-primary/20">
                                    <Loader2 className="w-2.5 h-2.5 animate-spin" />
                                    {generationStatus || 'AI 正在出题...'}
                                </div>
                            )}
                        </div>
                        <p className="text-sm text-muted-foreground">查看所有已收录的考点和知识点</p>
                        {batchStatus && (
                            <div className="mt-2 flex items-center gap-3 bg-primary/5 border border-primary/20 p-2 rounded-lg max-w-md animate-pulse">
                                <div className="text-primary font-bold text-xs">
                                    批量任务: {batchStatus.current} / {batchStatus.total}
                                </div>
                                <div className="text-muted-foreground text-[10px] truncate">
                                    正在生成: {batchStatus.topic}
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {knowledgePoints.some(p => p.questionCount === 0) && (
                            <Button
                                onClick={handleBatchGenerate}
                                variant="outline"
                                className="border-primary/50 text-primary hover:bg-primary/5 gap-2"
                                disabled={isGenerating || batchStatus !== null}
                            >
                                <Zap className="w-4 h-4 fill-primary" />
                                补全所有 0 题考点 (每项10题)
                            </Button>
                        )}
                        <Link href="/" className="sm:self-center flex-shrink-0">
                            <Button variant="outline" className="whitespace-nowrap w-full sm:w-auto">← 返回首页</Button>
                        </Link>
                    </div>
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
                                <Button
                                    variant="outline"
                                    className="ml-2 border-primary/20 text-primary hover:bg-primary/5"
                                    onClick={() => {
                                        const empty = knowledgePoints.find(p => p.questionCount === 0);
                                        if (empty) handleQuickGenerate(empty.name);
                                    }}
                                    disabled={isGenerating || !knowledgePoints.some(p => p.questionCount === 0)}
                                >
                                    <Zap className="w-3.5 h-3.5 mr-1" />
                                    补全一例
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {knowledgePoints.map((point, idx) => (
                                    <div
                                        key={idx}
                                        className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-muted/50 rounded-lg hover:bg-muted transition gap-3"
                                    >
                                        <div className="flex items-center gap-3 sm:gap-4 overflow-hidden">
                                            <div className="w-8 h-8 rounded-full bg-primary/10 flex-shrink-0 flex items-center justify-center text-sm font-bold text-primary">
                                                {idx + 1}
                                            </div>
                                            <div className="overflow-hidden">
                                                <div className="font-medium truncate text-sm sm:text-base" title={point.name}>
                                                    {point.name}
                                                </div>
                                                <div className="text-xs text-muted-foreground">{point.questionCount} 道题目</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
                                            <div className="hidden lg:block w-24 bg-secondary rounded-full h-2">
                                                <div
                                                    className="bg-primary h-2 rounded-full transition-all duration-500"
                                                    style={{ width: `${Math.min((point.questionCount / questions.length) * 100 * 5, 100)}%` }}
                                                ></div>
                                            </div>
                                            <div className="flex gap-2 flex-shrink-0">
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    className="h-8 gap-1 text-primary hover:bg-primary/10 whitespace-nowrap"
                                                    onClick={() => handleShowDetail(point.name)}
                                                    disabled={detailLoading !== null || isGenerating}
                                                >
                                                    {detailLoading === point.name ? (
                                                        <Loader2 className="w-3 h-3 animate-spin" />
                                                    ) : (
                                                        <Info className="w-3.5 h-3.5" />
                                                    )}
                                                    语法详细
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant={point.questionCount === 0 ? "ghost" : "outline"}
                                                    className={`h-8 gap-1 transition-colors whitespace-nowrap ${point.questionCount === 0 ? 'text-muted-foreground/30' : 'hover:bg-primary/5 hover:text-primary'}`}
                                                    onClick={() => handlePractice(point.name)}
                                                    disabled={practiceLoading !== null || isGenerating || point.questionCount === 0}
                                                >
                                                    {practiceLoading === point.name ? (
                                                        <Loader2 className="w-3 h-3 animate-spin" />
                                                    ) : (
                                                        <Play className={`w-3 h-3 ${point.questionCount === 0 ? 'opacity-20' : 'fill-current'}`} />
                                                    )}
                                                    练习
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant={point.questionCount === 0 ? "secondary" : "outline"}
                                                    className={`h-8 gap-1 whitespace-nowrap flex-shrink-0 ${point.questionCount === 0 ? 'bg-primary/10 text-primary hover:bg-primary/20 border-primary/20' : 'border-primary/20 text-primary hover:bg-primary/5'}`}
                                                    disabled={isGenerating}
                                                    onClick={() => point.questionCount === 0 ? handleQuickGenerate(point.name) : setGenTarget(point.name)}
                                                >
                                                    <Sparkles className={`w-3.5 h-3.5 ${point.questionCount === 0 ? 'animate-pulse' : ''}`} />
                                                    {point.questionCount === 0 ? '一键补全' : '生成'}
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive flex-shrink-0"
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

            {/* Knowledge Detail Modal */}
            <KnowledgeDetailModal
                detail={selectedDetail}
                onClose={() => setSelectedDetail(null)}
            />
        </div>
    );
}
