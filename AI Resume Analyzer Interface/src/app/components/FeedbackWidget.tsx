import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { MessageSquareHeart, ThumbsUp, ThumbsDown, CheckCircle2, Loader2 } from 'lucide-react';
import {
  submitFeedback,
  ScoreRating,
  FeedbackSnapshot,
} from '../../utils/api';

interface FeedbackWidgetProps {
  historyId?: number | null;
  snapshot: FeedbackSnapshot;
}

/**
 * Inline feedback widget shown on the analysis results page.
 *
 * Signals captured:
 *   1. Score rating       — too high / accurate / too low
 *   2. Usefulness rating  — thumbs up / thumbs down mapped to 5 / 1
 *   3. Freeform comment   — optional, capped at 2000 chars by the backend
 *
 * At least one signal is required by the backend; the submit button stays
 * disabled until the user has provided one.
 */
export function FeedbackWidget({ historyId, snapshot }: FeedbackWidgetProps) {
  const [scoreRating, setScoreRating] = useState<ScoreRating | null>(null);
  const [thumb,       setThumb]       = useState<'up' | 'down' | null>(null);
  const [comment,     setComment]     = useState('');
  const [submitting,  setSubmitting]  = useState(false);
  const [submitted,   setSubmitted]   = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  const canSubmit =
    !submitting && (scoreRating !== null || thumb !== null || comment.trim().length > 0);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback({
        historyId: historyId ?? null,
        scoreRating,
        usefulness: thumb === 'up' ? 5 : thumb === 'down' ? 1 : null,
        comment: comment.trim() || undefined,
        snapshot,
      });
      setSubmitted(true);
    } catch (err: any) {
      setError(err?.message || 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <Card className="mb-6 border-green-200 bg-green-50">
        <CardContent className="py-6 flex items-center gap-3">
          <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
          <div>
            <p className="text-green-900 font-medium">Thanks for the feedback!</p>
            <p className="text-green-800 text-sm">
              Your signal helps us sharpen the matcher over time.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const ratingButton = (
    value: ScoreRating,
    label: string,
    tone: 'red' | 'green' | 'blue',
  ) => {
    const active = scoreRating === value;
    const toneClasses = {
      red:   active ? 'bg-red-600 text-white hover:bg-red-700'     : 'hover:bg-red-50 hover:border-red-300 hover:text-red-700',
      green: active ? 'bg-green-600 text-white hover:bg-green-700' : 'hover:bg-green-50 hover:border-green-300 hover:text-green-700',
      blue:  active ? 'bg-blue-600 text-white hover:bg-blue-700'   : 'hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700',
    }[tone];
    return (
      <Button
        type="button"
        variant="outline"
        onClick={() => setScoreRating(active ? null : value)}
        className={`flex-1 transition-colors ${toneClasses}`}
      >
        {label}
      </Button>
    );
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquareHeart className="w-5 h-5 text-pink-600" />
          Was this analysis helpful?
        </CardTitle>
        <CardDescription>
          Your feedback trains a better matcher. Rate the score, leave a comment,
          or both — all fields are optional.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Score rating */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Is the {snapshot.matchScore ?? '—'}% match score about right?
          </p>
          <div className="flex gap-2">
            {ratingButton('too_high', 'Too high',  'red')}
            {ratingButton('accurate', 'Accurate', 'green')}
            {ratingButton('too_low',  'Too low',   'blue')}
          </div>
        </div>

        {/* Thumbs usefulness */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Overall, was the analysis useful?
          </p>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setThumb(thumb === 'up' ? null : 'up')}
              className={`flex-1 transition-colors ${
                thumb === 'up'
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'hover:bg-green-50 hover:border-green-300 hover:text-green-700'
              }`}
            >
              <ThumbsUp className="w-4 h-4 mr-2" />
              Useful
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setThumb(thumb === 'down' ? null : 'down')}
              className={`flex-1 transition-colors ${
                thumb === 'down'
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'hover:bg-red-50 hover:border-red-300 hover:text-red-700'
              }`}
            >
              <ThumbsDown className="w-4 h-4 mr-2" />
              Not useful
            </Button>
          </div>
        </div>

        {/* Freeform comment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="feedback-comment">
            Anything else? <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <Textarea
            id="feedback-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value.slice(0, 2000))}
            placeholder="e.g. missed a skill I actually have, score should be higher because…"
            rows={3}
          />
          <p className="text-xs text-gray-400 mt-1">{comment.length}/2000</p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end">
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
          >
            {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Submit feedback
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
