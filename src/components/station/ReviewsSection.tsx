/* ================================================================
   Ev2Ev — Station Reviews Section
   Supabase-backed reviews with graceful fallback to bundled sample
   reviews when Supabase is unconfigured, errors, or has no rows.
   ================================================================ */

"use client";

import { useEffect, useState, type SubmitEvent } from "react";
import Link from "next/link";
import { Star } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { isSupabaseConfigured } from "@/lib/supabase/env";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Database } from "@/lib/supabase/database.types";

type ReviewRow = Database["public"]["Tables"]["reviews"]["Row"] & {
  profiles: {
    display_name: string;
    avatar_url: string | null;
  } | null;
};

interface DisplayReview {
  key: string;
  name: string;
  rating: number;
  text: string;
  time: string;
}

interface ReviewsSectionProps {
  stationSlug: string;
  /** Aggregate rating from the station record (reserved for future use). */
  avgRating: number;
  reviewCount: number;
}

/** Sample reviews shown when Supabase is unavailable or has no data. */
const SAMPLE_REVIEWS: DisplayReview[] = [
  { key: "sample-1", name: "Rahul S.", rating: 5, text: "Excellent charging station! Fast CCS2 charger, well-maintained, and the staff is helpful. Charged my Tata Nexon in 45 minutes.", time: "2 days ago" },
  { key: "sample-2", name: "Priya M.", rating: 4, text: "Good location with free parking. The charger worked fine. Only issue is the waiting during peak hours.", time: "1 week ago" },
  { key: "sample-3", name: "Amit K.", rating: 4, text: "Reliable station on the highway. There's a decent restaurant nearby. Waiting time was about 15 minutes.", time: "2 weeks ago" },
];

/** Formats an ISO timestamp into a relative "x days ago" style string. */
function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes === 1 ? "1 minute ago" : `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return days === 1 ? "1 day ago" : `${days} days ago`;
  const weeks = Math.floor(days / 7);
  if (days < 30) return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return months === 1 ? "1 month ago" : `${months} months ago`;
  const years = Math.floor(days / 365);
  return years <= 1 ? "1 year ago" : `${years} years ago`;
}

function toDisplayReview(row: ReviewRow): DisplayReview {
  return {
    key: row.id,
    name: row.profiles?.display_name || "EV Driver",
    rating: row.rating,
    text: row.body,
    time: relativeTime(row.created_at),
  };
}

export default function ReviewsSection({
  stationSlug,
  reviewCount,
}: ReviewsSectionProps) {
  const { user } = useAuth();
  const configured = isSupabaseConfigured();

  // null → no DB data (use sample fallback); array → live reviews from Supabase
  const [dbReviews, setDbReviews] = useState<DisplayReview[] | null>(null);

  const [formOpen, setFormOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [body, setBody] = useState("");
  const [waitingMinutes, setWaitingMinutes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState(false);

  useEffect(() => {
    if (!configured) return;
    let active = true;
    const supabase = createClient();

    supabase
      .from("reviews")
      .select("*, profiles(display_name, avatar_url)")
      .eq("station_slug", stationSlug)
      .eq("status", "approved")
      .order("created_at", { ascending: false })
      .then(({ data, error }) => {
        if (!active) return;
        if (error || !data || data.length === 0) {
          setDbReviews(null); // fall back to sample reviews
          return;
        }
        setDbReviews((data as ReviewRow[]).map(toDisplayReview));
      });

    return () => {
      active = false;
    };
  }, [configured, stationSlug]);

  const reviews = dbReviews ?? SAMPLE_REVIEWS;
  const displayCount = dbReviews ? dbReviews.length : reviewCount;

  const resetForm = () => {
    setRating(0);
    setHoverRating(0);
    setBody("");
    setWaitingMinutes("");
    setFormError(null);
  };

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!user) return;
    setFormError(null);

    if (rating < 1 || rating > 5) {
      setFormError("Please select a star rating.");
      return;
    }
    if (!body.trim()) {
      setFormError("Please write a few words about your experience.");
      return;
    }
    if (!configured) {
      setFormError("Reviews are not available right now. Please try again later.");
      return;
    }

    setSubmitting(true);
    const supabase = createClient();
    const waiting = waitingMinutes.trim() === "" ? null : Number(waitingMinutes);
    const { data, error } = await supabase
      .from("reviews")
      .insert({
        user_id: user.id,
        station_slug: stationSlug,
        rating,
        body: body.trim(),
        waiting_minutes: waiting !== null && Number.isFinite(waiting) ? waiting : null,
      })
      .select("*, profiles(display_name, avatar_url)")
      .single();
    setSubmitting(false);

    if (error) {
      if (error.code === "23505") {
        setFormError("You've already reviewed this station. Thanks for sharing your experience!");
      } else {
        setFormError("Couldn't submit your review. Please try again.");
      }
      return;
    }

    const newReview: DisplayReview = data
      ? toDisplayReview(data as ReviewRow)
      : {
          key: `local-${Date.now()}`,
          name: user.email?.split("@")[0] || "You",
          rating,
          text: body.trim(),
          time: "just now",
        };

    setDbReviews((prev) => [newReview, ...(prev ?? [])]);
    resetForm();
    setFormOpen(false);
    setFormSuccess(true);
  };

  return (
    <div className="card p-6" id="reviews-section">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Star className="w-5 h-5 text-amber-400" /> Reviews ({displayCount})
        </h2>
        {user ? (
          <button
            className="text-sm font-semibold text-[var(--accent)] hover:underline"
            onClick={() => {
              setFormOpen((open) => !open);
              setFormSuccess(false);
            }}
          >
            {formOpen ? "Cancel" : "Write a Review"}
          </button>
        ) : (
          <Link
            href="/login"
            className="text-sm font-semibold text-[var(--accent)] hover:underline"
          >
            Log in to write a review
          </Link>
        )}
      </div>

      {formSuccess && (
        <div className="mb-4 p-3 rounded-xl bg-[var(--bg-secondary)] text-sm text-[var(--accent)] font-medium">
          Thanks! Your review has been posted.
        </div>
      )}

      {/* Write a Review form */}
      {formOpen && user && (
        <form
          onSubmit={handleSubmit}
          className="mb-4 p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-primary)] space-y-3"
        >
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
              Your rating
            </label>
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }).map((_, i) => {
                const value = i + 1;
                const filled = value <= (hoverRating || rating);
                return (
                  <button
                    key={i}
                    type="button"
                    aria-label={`Rate ${value} star${value > 1 ? "s" : ""}`}
                    className="p-0.5"
                    onClick={() => setRating(value)}
                    onMouseEnter={() => setHoverRating(value)}
                    onMouseLeave={() => setHoverRating(0)}
                  >
                    <Star
                      className={`w-6 h-6 transition-colors ${filled ? "text-amber-400" : "text-[var(--border-secondary)]"}`}
                      fill={filled ? "currentColor" : "none"}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label htmlFor="review-body" className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
              Your review
            </label>
            <textarea
              id="review-body"
              rows={3}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Share your charging experience at this station…"
              className="w-full px-3 py-2 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-primary)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)] resize-y"
            />
          </div>

          <div>
            <label htmlFor="review-waiting" className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
              Waiting time in minutes <span className="text-[var(--text-tertiary)] font-normal">(optional)</span>
            </label>
            <input
              id="review-waiting"
              type="number"
              min={0}
              max={600}
              value={waitingMinutes}
              onChange={(e) => setWaitingMinutes(e.target.value)}
              placeholder="e.g. 15"
              className="w-32 px-3 py-2 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-primary)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]"
            />
          </div>

          {formError && (
            <p className="text-sm text-red-500">{formError}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2.5 rounded-xl text-sm font-semibold gradient-accent text-white shadow-glow hover:shadow-glow-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {submitting ? "Submitting…" : "Submit Review"}
          </button>
        </form>
      )}

      {/* Reviews list */}
      {reviews.map((review, i) => (
        <div key={review.key} className={`py-4 ${i > 0 ? "border-t border-[var(--border-primary)]" : ""}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-sm font-bold">
                {review.name[0]}
              </div>
              <span className="font-semibold text-sm text-[var(--text-primary)]">{review.name}</span>
            </div>
            <span className="text-xs text-[var(--text-tertiary)]">{review.time}</span>
          </div>
          <div className="flex items-center gap-0.5 mt-2">
            {Array.from({ length: 5 }).map((_, j) => (
              <Star
                key={j}
                className={`w-3.5 h-3.5 ${j < review.rating ? "text-amber-400" : "text-[var(--border-secondary)]"}`}
                fill={j < review.rating ? "currentColor" : "none"}
              />
            ))}
          </div>
          <p className="text-sm text-[var(--text-secondary)] mt-2 leading-relaxed">{review.text}</p>
        </div>
      ))}
    </div>
  );
}
