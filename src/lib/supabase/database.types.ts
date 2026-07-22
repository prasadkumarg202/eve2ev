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
      operators: {
        Row: {
          id: string;
          name: string;
          slug: string;
          logo_url: string | null;
          website: string | null;
          support_phone: string | null;
          support_email: string | null;
          is_partner: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          name: string;
          slug: string;
          logo_url?: string | null;
          website?: string | null;
          support_phone?: string | null;
          support_email?: string | null;
          is_partner?: boolean;
        };
        Update: {
          name?: string;
          slug?: string;
          logo_url?: string | null;
          website?: string | null;
          is_partner?: boolean;
        };
        Relationships: [];
      };
      stations: {
        Row: {
          id: string;
          slug: string;
          name: string;
          address_line1: string;
          address_line2: string | null;
          city: string;
          district: string | null;
          state: string;
          pin_code: string | null;
          /** PostGIS geography — opaque to the client; read lat/lng instead. */
          geom: unknown;
          latitude: number | null;
          longitude: number | null;
          operator_id: string | null;
          phone: string | null;
          email: string | null;
          opening_hours: Json | null;
          is_24x7: boolean;
          free_parking: boolean;
          is_verified: boolean;
          status: StationStatusEnum;
          avg_rating: number;
          review_count: number;
          data_source: string;
          source_id: string | null;
          external_ids: Json;
          field_provenance: Json;
          merge_confidence: number | null;
          osm_location_id: string | null;
          metadata: Json;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          slug: string;
          name: string;
          geom: unknown;
          city?: string;
          state?: string;
          district?: string | null;
          pin_code?: string | null;
          operator_id?: string | null;
          status?: StationStatusEnum;
          data_source?: string;
          source_id?: string | null;
          external_ids?: Json;
        };
        Update: {
          name?: string;
          city?: string;
          state?: string;
          status?: StationStatusEnum;
          is_verified?: boolean;
          avg_rating?: number;
          review_count?: number;
        };
        Relationships: [
          {
            foreignKeyName: "stations_operator_id_fkey";
            columns: ["operator_id"];
            referencedRelation: "operators";
            referencedColumns: ["id"];
          }
        ];
      };
      chargers: {
        Row: {
          id: string;
          station_id: string;
          connector_type: ConnectorTypeEnum;
          power_kw: number;
          pricing_model: string | null;
          price_per_kwh: number | null;
          price_per_minute: number | null;
          price_per_session: number | null;
          status: ChargerStatusEnum;
          last_status_update: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          station_id: string;
          connector_type: ConnectorTypeEnum;
          power_kw: number;
          status?: ChargerStatusEnum;
        };
        Update: {
          power_kw?: number;
          status?: ChargerStatusEnum;
          last_status_update?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "chargers_station_id_fkey";
            columns: ["station_id"];
            referencedRelation: "stations";
            referencedColumns: ["id"];
          }
        ];
      };
    };
    Views: Record<string, never>;
    Functions: {
      /** Free-text + area search with trigram fuzzy fallback. */
      stations_search: {
        Args: {
          q?: string | null;
          p_state?: string | null;
          p_city?: string | null;
          max_results?: number;
        };
        Returns: {
          id: string;
          slug: string;
          name: string;
          city: string;
          district: string | null;
          state: string;
          pin_code: string | null;
          latitude: number;
          longitude: number;
          status: StationStatusEnum;
          operator_name: string | null;
          score: number;
        }[];
      };
      /** PostGIS radius search, nearest first. */
      stations_nearby: {
        Args: {
          lat: number;
          lng: number;
          radius_km?: number;
          max_results?: number;
        };
        Returns: {
          id: string;
          slug: string;
          name: string;
          city: string;
          state: string;
          latitude: number;
          longitude: number;
          status: StationStatusEnum;
          avg_rating: number;
          review_count: number;
          distance_km: number;
        }[];
      };
      /** Distinct state/city pairs that actually have stations. */
      station_areas: {
        Args: Record<string, never>;
        Returns: {
          state: string;
          city: string | null;
          station_count: number;
        }[];
      };
    };
    Enums: {
      station_status: StationStatusEnum;
      charger_status: ChargerStatusEnum;
      connector_type: ConnectorTypeEnum;
    };
    CompositeTypes: Record<string, never>;
  };
}

export type StationStatusEnum =
  | "available"
  | "busy"
  | "offline"
  | "maintenance";

export type ChargerStatusEnum =
  | "available"
  | "in_use"
  | "offline"
  | "maintenance";

export type ConnectorTypeEnum =
  | "CCS2"
  | "Type2"
  | "BharatAC001"
  | "BharatDC001"
  | "CHAdeMO"
  | "GBT";
