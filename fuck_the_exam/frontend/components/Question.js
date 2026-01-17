'use client';

import { useState } from 'react';
import { submitAnswer, deleteQuestion, toggleFavorite } from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Trash2, Star } from 'lucide-react';

const Question = ({ question, onNext }) => {
  const [selectedOption, setSelectedOption] = useState(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFavorite, setIsFavorite] = useState(question.is_favorite || false);

  const handleOptionChange = (value) => {
    if (!isSubmitted) {
      setSelectedOption(value);
    }
  };

  const handleSubmit = async () => {
    if (!selectedOption || isSubmitted) return;

    setIsSubmitting(true);
    try {
      const res = await submitAnswer(question.id, selectedOption);
      setResult(res);
      setIsSubmitted(true);
    } catch (error) {
      console.error("Failed to submit answer:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('确定要删除这道题目吗？此操作不可撤销。')) {
      try {
        await deleteQuestion(question.id);
        onNext({ skipped: true, deleted: true });
      } catch (error) {
        console.error("Failed to delete question:", error);
        alert('删除失败，请稍后重试。');
      }
    }
  };

  const handleToggleFavorite = async () => {
    try {
      await toggleFavorite(question.id);
      setIsFavorite(!isFavorite);
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    }
  };

  // Callback to parent when user is ready for next question
  const handleNext = () => {
    // Pass the result up so the session can track it
    onNext({
      question_id: question.id,
      selected_answer: selectedOption,
      is_correct: result?.is_correct
    });
    // Reset local state is handled by parent unmounting this component or key change, 
    // but if we reuse, we need to reset. 
    // Ideally parent handles the "Next" logic by changing the question prop.
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card className="border-2">
        <CardHeader>
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-secondary px-2 py-1 rounded">
              N1 • {question.knowledge_point || '常规'}
            </span>
            <div className="flex gap-1 -mr-2">
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 ${isFavorite ? 'text-yellow-500 fill-yellow-500' : 'text-muted-foreground'} hover:text-yellow-600`}
                onClick={handleToggleFavorite}
                title={isFavorite ? "取消标记" : "标记此题"}
              >
                <Star className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                onClick={handleDelete}
                title="删除此题"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <CardTitle className="text-xl leading-relaxed mt-4 font-serif">
            {question.content}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(question.options).map(([key, value]) => {
            let optionClass = "w-full justify-start text-left h-auto py-4 px-4 border shadow-sm hover:bg-accent";

            if (isSubmitted) {
              if (key === result?.correct_answer) {
                optionClass += " bg-green-100 border-green-500 text-green-900 hover:bg-green-100";
              } else if (key === selectedOption && !result?.is_correct) {
                optionClass += " bg-red-100 border-red-500 text-red-900 hover:bg-red-100";
              } else {
                optionClass += " opacity-50";
              }
            } else if (selectedOption === key) {
              optionClass += " border-primary ring-1 ring-primary bg-accent";
            }

            return (
              <button
                key={key}
                disabled={isSubmitted}
                onClick={() => handleOptionChange(key)}
                className={`flex items-center rounded-lg transition-all ${optionClass}`}
              >
                <span className="font-bold mr-4 w-6 h-6 flex items-center justify-center rounded-full border border-current opacity-70 text-xs">
                  {key}
                </span>
                <span className="text-base">{value}</span>
              </button>
            );
          })}
        </CardContent>
      </Card>

      {!isSubmitted ? (
        <Button
          onClick={handleSubmit}
          disabled={!selectedOption || isSubmitting}
          className="w-full text-lg h-12"
        >
          {isSubmitting ? '正在提交...' : '确认答案'}
        </Button>
      ) : (
        <div className="space-y-4 animate-accordion-down">
          <Card className={`border-l-4 ${result?.is_correct ? 'border-l-green-500' : 'border-l-red-500'}`}>
            <CardContent className="pt-6">
              <h4 className={`font-bold text-lg mb-2 ${result?.is_correct ? 'text-green-700' : 'text-red-700'}`}>
                {result?.is_correct ? '正确! 🎉' : '再想想 😅'}
              </h4>
              <div className="space-y-2 text-sm text-foreground/80">
                <p className="font-semibold text-foreground">解析:</p>
                <p className="leading-relaxed">{result?.explanation}</p>
              </div>
            </CardContent>
          </Card>
          <Button onClick={handleNext} className="w-full" variant="outline">
            下一题 →
          </Button>
        </div>
      )}
    </div>
  );
};

export default Question;
