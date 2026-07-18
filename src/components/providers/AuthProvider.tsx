/* ================================================================
   Ev2Ev — Auth Provider (client)
   Wraps the app in a Supabase auth context: exposes the current user,
   session, loading state, and auth actions. Consumed via useAuth().
   ================================================================ */

"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Session, User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { isSupabaseConfigured } from "@/lib/supabase/env";

interface AuthResult {
  error: string | null;
}

interface AuthContextValue {
  user: User | null;
  session: Session | null;
  /** True until the initial session has been resolved. */
  loading: boolean;
  /** True when Supabase env vars are present (auth can actually work). */
  configured: boolean;
  signInWithPassword: (email: string, password: string) => Promise<AuthResult>;
  signUp: (
    email: string,
    password: string,
    displayName?: string
  ) => Promise<AuthResult>;
  signInWithOtp: (phone: string) => Promise<AuthResult>;
  verifyOtp: (phone: string, token: string) => Promise<AuthResult>;
  signInWithGoogle: () => Promise<AuthResult>;
  resetPassword: (email: string) => Promise<AuthResult>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function siteUrl(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
}

function toMessage(error: unknown): string {
  if (error && typeof error === "object" && "message" in error) {
    return String((error as { message: unknown }).message);
  }
  return "Something went wrong. Please try again.";
}

const NOT_CONFIGURED: AuthResult = {
  error:
    "Authentication is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local.",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const configured = isSupabaseConfigured();
  const supabase = useMemo(() => (configured ? createClient() : null), [configured]);

  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    let active = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      setSession(data.session);
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setUser(nextSession?.user ?? null);
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  const value = useMemo<AuthContextValue>(() => {
    return {
      user,
      session,
      loading,
      configured,

      async signInWithPassword(email, password) {
        if (!supabase) return NOT_CONFIGURED;
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        return { error: error ? toMessage(error) : null };
      },

      async signUp(email, password, displayName) {
        if (!supabase) return NOT_CONFIGURED;
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: displayName ? { full_name: displayName } : undefined,
            emailRedirectTo: `${siteUrl()}/auth/callback`,
          },
        });
        return { error: error ? toMessage(error) : null };
      },

      async signInWithOtp(phone) {
        if (!supabase) return NOT_CONFIGURED;
        const { error } = await supabase.auth.signInWithOtp({
          phone: `+91${phone.replace(/\D/g, "")}`,
        });
        return { error: error ? toMessage(error) : null };
      },

      async verifyOtp(phone, token) {
        if (!supabase) return NOT_CONFIGURED;
        const { error } = await supabase.auth.verifyOtp({
          phone: `+91${phone.replace(/\D/g, "")}`,
          token,
          type: "sms",
        });
        return { error: error ? toMessage(error) : null };
      },

      async signInWithGoogle() {
        if (!supabase) return NOT_CONFIGURED;
        const { error } = await supabase.auth.signInWithOAuth({
          provider: "google",
          options: { redirectTo: `${siteUrl()}/auth/callback` },
        });
        return { error: error ? toMessage(error) : null };
      },

      async resetPassword(email) {
        if (!supabase) return NOT_CONFIGURED;
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${siteUrl()}/auth/callback?next=/`,
        });
        return { error: error ? toMessage(error) : null };
      },

      async signOut() {
        if (!supabase) return;
        await supabase.auth.signOut();
      },
    };
  }, [user, session, loading, configured, supabase]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
