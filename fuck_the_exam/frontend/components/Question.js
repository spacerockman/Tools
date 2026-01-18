'use client';

import { useState } from 'react';
import { submitAnswer, deleteQuestion, toggleFavorite, getKnowledgeDetail } from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Trash2, Star, BookOpen, Loader2 } from 'lucide-react';
import KnowledgeDetailModal from './KnowledgeDetailModal';

const Question = ({ question, onNext }) => {
  if (!question) return null;

  const [selectedOption, setSelectedOption] = useState(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFavorite, setIsFavorite] = useState(question?.is_favorite || false);
  const [showDetail, setShowDetail] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isRevealed, setIsRevealed] = useState(!question.is_review);
  const [srsQuality, setSrsQuality] = useState(null);

  const handleOptionChange = (value) => {
    if (!isSubmitted) {
      setSelectedOption(value);
    }
  };

  const handleSubmit = async (quality = null) => {
    if (!selectedOption || isSubmitted) return;

    setIsSubmitting(true);
    try {
      const res = await submitAnswer(question.id, selectedOption, quality);
      setResult(res);
      setIsSubmitted(true);
      if (quality) setSrsQuality(quality);
    } catch (error) {
      console.error("Failed to submit answer:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSrsFeedback = async (quality) => {
    setSrsQuality(quality);
    // If not submitted yet, submit with this info
    if (!isSubmitted) {
      // For pure flashcard, picking correct answer if we didn't pick any? 
      // Actually let's assume they picked an option or we auto-pick if they say "Good"
      await handleSubmit(quality);
    } else {
      // Re-submit quality if already submitted? 
      // Simplified: Just proceed to next. 
      // But let's actually make the buttons trigger the Next action for efficiency.
      await submitAnswer(question.id, selectedOption, quality);
      handleNext();
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

  const handleShowDetail = async () => {
    if (detailData) {
      setShowDetail(true);
      return;
    }

    setDetailLoading(true);
    try {
      const data = await getKnowledgeDetail(question.knowledge_point);
      setDetailData(data);
      setShowDetail(true);
    } catch (error) {
      console.error("Failed to fetch knowledge detail:", error);
    } finally {
      setDetailLoading(false);
    }
  };

  // Callback to parent when user is ready for next question
  const handleNext = () => {
    onNext({
      question_id: question.id,
      selected_answer: selectedOption,
      is_correct: result?.is_correct
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card className="border-2 shadow-lg overflow-hidden transition-all duration-300">
        <CardHeader className="bg-muted/30 pb-4">
          <div className="flex justify-between items-start">
            <div className="flex flex-col gap-2">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest bg-background/50 border px-2 py-0.5 rounded-full inline-flex items-center gap-1 w-fit">
                N1 • {question.knowledge_point || '常规'}
              </span>
              {question.is_review && (
                <div className="flex items-center gap-2 text-xs text-orange-600 dark:text-orange-400 font-medium">
                  <span className="flex h-2 w-2 rounded-full bg-orange-500 animate-pulse"></span>
                  复习模式 (间隔: {question.srs_interval || 1} 天)
                </div>
              )}
            </div>
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
          <CardTitle className="text-2xl leading-relaxed mt-6 font-serif tracking-tight">
            {question.content}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          {!isRevealed ? (
            <div className="py-12 flex flex-col items-center justify-center bg-accent/20 rounded-xl border-2 border-dashed border-accent">
              <p className="text-muted-foreground mb-6 text-sm">思考一下，然后点击揭晓</p>
              <Button
                onClick={() => setIsRevealed(true)}
                className="rounded-full px-8 py-6 h-auto text-lg hover:scale-105 transition-transform shadow-md"
              >
                👀 查看选项
              </Button>
            </div>
          ) : (
            <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {Object.entries(question.options).map(([key, value]) => {
                let optionClass = "w-full justify-start text-left h-auto py-4 px-4 border shadow-sm transition-all duration-200 hover:bg-accent group";

                if (isSubmitted) {
                  if (key === result?.correct_answer) {
                    optionClass += " bg-green-50 border-green-500 text-green-900 dark:bg-green-900/40 dark:text-green-100 hover:bg-green-50";
                  } else if (key === selectedOption && !result?.is_correct) {
                    optionClass += " bg-red-50 border-red-500 text-red-900 dark:bg-red-900/40 dark:text-red-100 hover:bg-red-50";
                  } else {
                    optionClass += " opacity-40 grayscale-[0.5]";
                  }
                } else if (selectedOption === key) {
                  optionClass += " border-primary ring-2 ring-primary bg-primary/5";
                }

                return (
                  <button
                    key={key}
                    disabled={isSubmitted}
                    onClick={() => handleOptionChange(key)}
                    className={`flex items-center rounded-xl border-2 ${optionClass}`}
                  >
                    <span className={`font-bold mr-4 w-7 h-7 flex items-center justify-center rounded-full border-2 transition-colors ${selectedOption === key ? 'bg-primary text-white border-primary' : 'border-muted-foreground/30 text-muted-foreground'
                      }`}>
                      {key}
                    </span>
                    <span className="text-base font-medium">{value}</span>
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {isRevealed && !isSubmitted && (
        <Button
          onClick={() => handleSubmit()}
          disabled={!selectedOption || isSubmitting}
          className="w-full text-lg h-14 rounded-2xl shadow-lg transition-all active:scale-[0.98]"
        >
          {isSubmitting ? <Loader2 className="animate-spin mr-2" /> : null}
          {isSubmitting ? '正在提交...' : '确认答案'}
        </Button>
      )}

      {isSubmitted && (
        <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
          <Card className={`border-none shadow-md overflow-hidden ${result?.is_correct ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
            <div className={`h-1.5 w-full ${result?.is_correct ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-4">
                <span className={`text-2xl ${result?.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                  {result?.is_correct ? '✓' : '✗'}
                </span>
                <h4 className={`font-bold text-xl ${result?.is_correct ? 'text-green-700' : 'text-red-700'}`}>
                  {result?.is_correct ? '正确! 🎉' : '不小心选错了 😅'}
                </h4>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-background/80 rounded-xl border">
                  <p className="font-bold text-xs text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-2">
                    📘 解析
                  </p>
                  <p className="text-base leading-relaxed whitespace-pre-wrap">{result?.explanation}</p>
                </div>

                {result?.memorization_tip && result?.memorization_tip !== result?.explanation && (
                  <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-xl">
                    <p className="font-bold text-yellow-700 dark:text-yellow-400 text-xs uppercase flex items-center gap-1 mb-2">
                      💡 记忆卡片
                    </p>
                    <p className="text-base text-yellow-900 dark:text-yellow-200 italic font-medium">
                      {result.memorization_tip}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* SRS Feedback Buttons (Shown if it was a review) */}
          {question.is_review && (
            <div className="space-y-3">
              <p className="text-center text-xs font-bold text-muted-foreground uppercase tracking-widest">
                记忆程度评估 (SRS)
              </p>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: '忘记', val: 1, color: 'bg-red-500 text-white', desc: '1天' },
                  { label: '困难', val: 2, color: 'bg-orange-500 text-white', desc: '较短' },
                  { label: '良好', val: 4, color: 'bg-green-600 text-white', desc: '适中' },
                  { label: '简单', val: 5, color: 'bg-blue-600 text-white', desc: '跳过' }
                ].map(opt => (
                  <button
                    key={opt.val}
                    onClick={() => handleSrsFeedback(opt.val)}
                    className={`flex flex-col items-center justify-center p-3 rounded-xl transition-all hover:scale-105 active:scale-95 shadow-sm ${opt.color}`}
                  >
                    <span className="font-bold text-sm">{opt.label}</span>
                    <span className="text-[10px] opacity-80">{opt.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            {!question.is_review && (
              <Button onClick={handleNext} className="flex-1 h-14 text-lg rounded-2xl shadow-lg" variant="default">
                下一题 →
              </Button>
            )}
            <Button
              onClick={handleShowDetail}
              variant="secondary"
              disabled={detailLoading}
              className={`h-14 rounded-2xl gap-2 ${question.is_review ? 'flex-1' : 'w-auto'}`}
            >
              {detailLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
              知识详情
            </Button>
          </div>
        </div>
      )}

      {showDetail && (
        <KnowledgeDetailModal
          detail={detailData}
          onClose={() => setShowDetail(false)}
        />
      )}
    </div>
  );
};

export default Question;
