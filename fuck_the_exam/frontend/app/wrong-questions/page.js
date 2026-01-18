'use client';

import { useState, useEffect } from 'react';
import { getWrongQuestions } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Link from 'next/link';
import WrongQuestionCard from '../../components/WrongQuestionCard';

export default function WrongQuestions() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getWrongQuestions();
        setData(res);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="text-center p-8">正在加载复习数据...</div>;

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center mb-8 gap-4">
          <h1 className="text-2xl sm:text-3xl font-bold">错题集复习</h1>
          <div className="flex gap-2 flex-shrink-0">
            {data.length > 0 && (
              <Button
                onClick={() => {
                  const qs = data.map(item => ({ ...item.question, is_review: true }));
                  localStorage.setItem('currentQuestions', JSON.stringify(qs));
                  localStorage.setItem('currentTopic', '错题专项练习');
                  window.location.href = '/quiz/session';
                }}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                🔥 进入卡片刷题模式
              </Button>
            )}
            <Link href="/stats">
              <Button variant="outline" className="whitespace-nowrap">📊 统计结果</Button>
            </Link>
            <Link href="/">
              <Button variant="outline" className="whitespace-nowrap">← 返回</Button>
            </Link>
          </div>
        </div>

        {data.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <p className="text-muted-foreground mb-4">暂无错题记录。继续加油！</p>
              <Link href="/">
                <Button>开始测试</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {data.map((item) => (
              <WrongQuestionCard
                key={item.id}
                question={{
                  ...item.question,
                  review_count: item.review_count
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
