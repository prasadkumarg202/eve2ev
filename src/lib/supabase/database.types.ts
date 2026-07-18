/* ================================================================
   Ev2Ev — Supabase Database Types
   Hand-authored to match supabase/schema.sql. Regenerate with the
   Supabase CLI (`supabase gen types typescript`) once the project is
   linked, if you prefer generated types.
   ================================================================ */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          display_name: string;
          avatar_url: string | null;
          role: string;
          preferred_language: string;
          reward_points: number;
          reward_tier: string;
          created_at: string;
        };
        Insert: {
          id: string;
          display_name?: string;
          avatar_url?: string | null;
          role?: string;
          preferred_language?: string;
          reward_points?: number;
          reward_tier?: string;
          created_at?: string;
        };
        Update: {
          display_name?: string;
          avatar_url?: string | null;
          role?: string;
          preferred_language?: string;
          reward_points?: number;
          reward_tier?: string;
        };
        Relationships: [];
      };
      reviews: {
        Row: {
          id: string;
          user_id: string;
          station_slug: string;
          rating: number;
          body: string;
          waiting_minutes: number | null;
          status: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          station_slug: string;
          rating: number;
          body: string;
          waiting_minutes?: number | null;
          status?: string;
          created_at?: string;
        };
        Update: {
          rating?: number;
          body?: string;
          waiting_minutes?: number | null;
          status?: string;
        };
        Relationships: [
          {
            foreignKeyName: "reviews_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
      favorites: {
        Row: {
          user_id: string;
          station_slug: string;
          created_at: string;
        };
        Insert: {
          user_id: string;
          station_slug: string;
          created_at?: string;
        };
        Update: {
          station_slug?: string;
        };
        Relationships: [
          {
            foreignKeyName: "favorites_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
      bookings: {
        Row: {
          id: string;
          user_id: string;
          station_slug: string;
          charger_id: string | null;
          slot_start: string;
          slot_end: string;
          status: string;
          qr_code: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          station_slug: string;
          charger_id?: string | null;
          slot_start: string;
          slot_end: string;
          status?: string;
          qr_code?: string | null;
          created_at?: string;
        };
        Update: {
          slot_start?: string;
          slot_end?: string;
          status?: string;
          qr_code?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "bookings_user_id_fkey";
            columns: ["user_id"];
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
}
