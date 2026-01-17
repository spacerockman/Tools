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

  if (loading) return <div className="text-center p-8">Loading review data...</div>;

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Wrong Questions Review</h1>
          <div className="flex gap-2">
            <Link href="/stats">
              <Button variant="outline">📊 Stats</Button>
            </Link>
            <Link href="/">
              <Button variant="outline">← Back</Button>
            </Link>
          </div>
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
