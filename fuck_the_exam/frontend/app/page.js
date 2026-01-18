'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { getStudySession, getStats, getGapQuiz } from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useGeneration } from '../contexts/GenerationContext';

export default function Dashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isGenerating, startGeneration } = useGeneration();

  const [topic, setTopic] = useState('');
  const [numQuestions, setNumQuestions] = useState(10);
  const [isStudyLoading, setIsStudyLoading] = useState(false);
  const [feedback, setFeedback] = useState({ type: '', message: '' });
  const [stats, setStats] = useState(null);

  // Handle auto-fill from query params (from Training Suggestions)
  useEffect(() => {
    const topicParam = searchParams.get('topic');
    if (topicParam) {
      setTopic(topicParam);
    }

    // Fetch real stats
    const fetchStats = async () => {
      try {
        const data = await getStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      }
    };
    fetchStats();
  }, [searchParams]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setFeedback({ type: 'error', message: '请输入一个 N1 考点！' });
      return;
    }

    // Start background generation - user can navigate away
    startGeneration(topic, numQuestions);
    setFeedback({ type: 'info', message: '✅ 已开始后台生成，你可以继续浏览其他页面！' });
  };

  const handleStudy = async () => {
    setIsStudyLoading(true);
    setFeedback({ type: '', message: '' });
    try {
      // Limit to 10 new and 10 review (Total 20)
      const response = await getStudySession(10, 10);
      if (response.length === 0) {
        setFeedback({ type: 'info', message: '暂无待复习题目或新题，请先生成一些题目！' });
        setIsStudyLoading(false);
        return;
      }
      localStorage.setItem('currentQuestions', JSON.stringify(response));
      localStorage.setItem('currentTopic', 'Daily Study Session');
      router.push('/quiz/session');
    } catch (error) {
      console.error(error);
      setFeedback({ type: 'error', message: '获取复习计划失败。' });
    } finally {
      setIsStudyLoading(false);
    }
  };

  const handleGapQuiz = async () => {
    setIsStudyLoading(true);
    setFeedback({ type: '', message: '' });
    try {
      let response = await getGapQuiz(2);
      if (response.length === 0) {
        setFeedback({ type: 'info', message: '暂无题目可供排查，请先生成一些题目！' });
        setIsStudyLoading(false);
        return;
      }

      // Limit to 20 questions
      if (response.length > 20) {
        // Shuffle and take 20
        response = response.sort(() => 0.5 - Math.random()).slice(0, 20);
      }

      localStorage.setItem('currentQuestions', JSON.stringify(response));
      localStorage.setItem('currentTopic', 'Knowledge Gap Test');
      router.push('/quiz/session');
    } catch (error) {
      console.error(error);
      setFeedback({ type: 'error', message: '获取排查计划失败。' });
    } finally {
      setIsStudyLoading(false);
    }
  };

  const quickTopics = ["N1 语法: ～ざるを得ない", "N1 阅读: 哲学", "N1 词汇: 同义词"];
  const questionCounts = [5, 10, 15, 20, 25];

  // Calculate today's stats from daily_stats
  const todayStr = new Date().toISOString().split('T')[0];
  const todayStats = stats?.daily_stats?.find(s => s.date === todayStr) || { correct: 0, wrong: 0 };
  const todayTotal = todayStats.correct + todayStats.wrong;
  const accuracy = todayTotal > 0 ? Math.round((todayStats.correct / todayTotal) * 100) : 0;

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <header className="mb-8 md:mb-12 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight mb-2">日语 N1 学习中心</h1>
          <p className="text-sm text-muted-foreground">坚持不懈，久久为功。</p>
        </div>
        <div className="flex gap-2 sm:gap-4 overflow-x-auto pb-2 sm:pb-0">
          <Link href="/knowledge" className="flex-shrink-0">
            <Button variant="outline" className="whitespace-nowrap">📚 知识库</Button>
          </Link>
          <Link href="/stats" className="flex-shrink-0">
            <Button variant="outline" className="whitespace-nowrap">📊 学习统计</Button>
          </Link>
          <div className="h-10 w-10 rounded-full bg-secondary flex-shrink-0 hidden sm:block"></div>
        </div>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">

        {/* Left Column: Generator */}
        <div className="md:col-span-2 space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>⚡️ 快速开始测试</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800 p-6 rounded-lg border border-blue-100 dark:border-slate-700">
                <h3 className="font-bold text-lg mb-2">📅 每日学习课（SRS）</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  基于艾宾浩斯记忆曲线复习错题 + 学习新考点。
                </p>
                <Button onClick={handleStudy} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" disabled={isStudyLoading || isGenerating}>
                  {isStudyLoading ? '正在加载...' : '开始我的每日复习'}
                </Button>

                <div className="mt-4 pt-4 border-t border-blue-200 dark:border-slate-700">
                  <h4 className="text-sm font-semibold mb-2">🔍 知识漏洞排查</h4>
                  <p className="text-xs text-muted-foreground mb-3">从每个知识点随机抽题，全方位检测薄弱环节。</p>
                  <Button onClick={handleGapQuiz} variant="secondary" className="w-full" disabled={isStudyLoading || isGenerating}>
                    💡 开始随机排查测试
                  </Button>
                </div>
              </div>

              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">或者生成新题目</span>
                </div>
              </div>

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">目标考点</label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="例如：语法：～なしに"
                    className="w-full flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={isGenerating}
                  />
                </div>

                <div className="flex flex-wrap gap-2">
                  {quickTopics.map(t => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTopic(t)}
                      className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded hover:bg-secondary/80 transition"
                    >
                      {t}
                    </button>
                  ))}
                </div>

                {/* Question Count Selector */}
                <div>
                  <label className="block text-sm font-medium mb-2">生成题目数量</label>
                  <div className="flex flex-wrap gap-2">
                    {questionCounts.map(count => (
                      <button
                        key={count}
                        type="button"
                        onClick={() => setNumQuestions(count)}
                        className={`px-4 py-2 rounded-md border text-sm font-medium transition ${numQuestions === count
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-background border-input hover:bg-accent'
                          }`}
                      >
                        {count}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2">
                  <Button type="submit" className="w-full" disabled={isGenerating}>
                    {isGenerating ? '🔄 后台生成中...' : `立即生成 ${numQuestions} 道题`}
                  </Button>
                </div>

                {feedback.message && (
                  <p className={`text-sm ${feedback.type === 'error' ? 'text-destructive' : 'text-green-600'}`}>
                    {feedback.message}
                  </p>
                )}
              </form>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link href="/wrong-questions" className="block">
              <Card className="hover:bg-accent/50 transition cursor-pointer h-full">
                <CardHeader>
                  <CardTitle className="text-lg">📖 错题复习</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm">精准打击薄弱环节。重复是学习之母。</p>
                </CardContent>
              </Card>
            </Link>
            <Link href="/stats" className="block">
              <Card className="hover:bg-accent/50 transition cursor-pointer h-full">
                <CardHeader>
                  <CardTitle className="text-lg">📊 查看统计</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm">追踪你的进度，识别薄弱环节。</p>
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>

        {/* Right Column: Stats & Logs */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">今日进度</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-1">{todayTotal} 道题</div>
              <p className="text-xs text-muted-foreground">
                今日正确率: {accuracy}% ({todayStats.correct} 正确 / {todayStats.wrong} 错误)
              </p>
              <div className="mt-4 h-2 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-primary transition-all" style={{ width: `${accuracy}%` }}></div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">最近记录</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {stats?.daily_stats?.slice(0, 5).map((s, idx) => (
                  <li key={idx} className="flex justify-between items-center text-sm">
                    <span className="truncate max-w-[150px] font-medium">{s.date} 练习</span>
                    <span className="text-muted-foreground">{s.correct + s.wrong} 题</span>
                  </li>
                ))}
                {(!stats?.daily_stats || stats.daily_stats.length === 0) && (
                  <li className="text-sm text-muted-foreground py-4 text-center italic">暂无记录</li>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

      </main>
    </div>
  );
}
