'use client';

import { useState, useEffect } from 'react';
import { getWrongQuestions } from '../../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Link from 'next/link';

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

  if (loading) return <div className="text-center p-8">Loading review data...</div>;

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Wrong Questions Review</h1>
          <Link href="/">
            <Button variant="outline">← Back to Dashboard</Button>
          </Link>
        </div>

        {data.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <p className="text-muted-foreground mb-4">No wrong questions recorded yet. Keep practicing!</p>
              <Link href="/">
                <Button>Start a Quiz</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {data.map((item) => (
              <Card key={item.id} className="border-l-4 border-l-red-500">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold text-red-500 uppercase tracking-wider">
                      Missed {item.review_count} times
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {item.question.knowledge_point}
                    </span>
                  </div>
                  <CardTitle className="text-lg font-serif mt-2">{item.question.content}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-accent/50 p-4 rounded-md text-sm space-y-2">
                    <div className="flex justify-between">
                      <span className="font-semibold text-green-600">Correct Answer: {item.question.correct_answer}</span>
                    </div>
                    <p className="text-muted-foreground">{item.question.explanation}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
