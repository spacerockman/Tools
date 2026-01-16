'use client';

import { useState } from 'react';
import { submitAnswer } from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';

const Question = ({ question, onNext }) => {
  const [selectedOption, setSelectedOption] = useState(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
              N1 • {question.knowledge_point || 'General'}
            </span>
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
          {isSubmitting ? 'Checking...' : 'Check Answer'}
        </Button>
      ) : (
        <div className="space-y-4 animate-accordion-down">
          <Card className={`border-l-4 ${result?.is_correct ? 'border-l-green-500' : 'border-l-red-500'}`}>
            <CardContent className="pt-6">
              <h4 className={`font-bold text-lg mb-2 ${result?.is_correct ? 'text-green-700' : 'text-red-700'}`}>
                {result?.is_correct ? 'Correct! 🎉' : 'Incorrect 😅'}
              </h4>
              <div className="space-y-2 text-sm text-foreground/80">
                <p className="font-semibold text-foreground">Explanation:</p>
                <p className="leading-relaxed">{result?.explanation}</p>
              </div>
            </CardContent>
          </Card>
          <Button onClick={handleNext} className="w-full" variant="outline">
            Next Question →
          </Button>
        </div>
      )}
    </div>
  );
};

export default Question;
