import { Card, CardContent } from "./ui/card";
import { Lightbulb, BookOpen, CheckCircle, XCircle } from "lucide-react";

export default function WrongQuestionCard({ question }) {
  const options = typeof question.options === 'string'
    ? JSON.parse(question.options)
    : question.options;

  return (
    <Card className="mb-4 border-l-4 border-l-red-500 shadow-sm hover:shadow-md transition-all">
      <CardContent className="pt-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-medium leading-snug mb-2">{question.content}</h3>
            <div className="flex flex-col gap-2 mt-3">
              {Object.entries(options).map(([key, val]) => {
                const isCorrect = key === question.correct_answer;
                // We don't know user's specific wrong answer here easily unless passed, 
                // but we can highlight the correct one.
                return (
                  <div
                    key={key}
                    className={`text-sm px-3 py-2 rounded border ${isCorrect
                        ? "bg-green-50 border-green-200 text-green-800 dark:bg-green-900/30 dark:border-green-800 dark:text-green-300"
                        : "bg-background border-input text-muted-foreground"
                      }`}
                  >
                    <span className="font-bold mr-2">{key}.</span> {val}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Knowledge & Explanation */}
        <div className="mt-4 space-y-3">
          <div className="flex gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="bg-secondary px-2 py-1 rounded flex items-center gap-1">
              <BookOpen className="w-3 h-3" />
              {question.knowledge_point || "General"}
            </span>
            <span className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 px-2 py-1 rounded flex items-center gap-1">
              Review Count: {question.review_count || 0}
            </span>
          </div>

          <div className="bg-muted/50 p-4 rounded-lg text-sm">
            <p className="font-semibold mb-1 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" /> Explanation
            </p>
            <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {question.explanation || "No explanation available."}
            </p>
          </div>

          {question.memorization_tip && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-100 dark:border-yellow-800 p-4 rounded-lg text-sm">
              <p className="font-bold text-yellow-700 dark:text-yellow-400 mb-1 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" /> Memorization Tip
              </p>
              <p className="text-yellow-800 dark:text-yellow-300 italic">
                {question.memorization_tip}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
