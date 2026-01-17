'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Link from 'next/link';

export default function KnowledgePage() {
    const [questions, setQuestions] = useState([]);
    const [knowledgePoints, setKnowledgePoints] = useState([]);
    const [loading, setLoading] = useState(true);

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
                        <h1 className="text-3xl font-bold tracking-tight">📚 知识点库</h1>
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
                                            <div className="w-24 bg-secondary rounded-full h-2">
                                                <div
                                                    className="bg-primary h-2 rounded-full"
                                                    style={{ width: `${Math.min((point.questionCount / questions.length) * 100 * 5, 100)}%` }}
                                                ></div>
                                            </div>
                                            <Link href={`/?topic=${encodeURIComponent(point.name)}`}>
                                                <Button size="sm" variant="outline">练习</Button>
                                            </Link>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

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
