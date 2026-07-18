/* ================================================================
   Ev2Ev — Type Definitions: Charging Station & Related Entities
   ================================================================ */

export type StationStatus = "available" | "busy" | "offline" | "maintenance";
export type ConnectorType = "CCS2" | "Type2" | "BharatAC001" | "BharatDC001" | "CHAdeMO" | "GBT";
export type VehicleType = "bike" | "scooter" | "auto" | "car" | "bus" | "truck";
export type ChargerStatus = "available" | "in_use" | "offline" | "maintenance";
export type ReviewStatus = "pending" | "approved" | "rejected";
export type BookingStatus = "confirmed" | "cancelled" | "completed" | "no_show";
export type BlogStatus = "draft" | "pending_review" | "published" | "rejected";
export type UserRole = "user" | "contributor" | "moderator" | "admin" | "operator";
export type RewardTier = "bronze" | "silver" | "gold" | "platinum";

export interface Operator {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
  website?: string;
  supportPhone?: string;
  supportEmail?: string;
  isPartner: boolean;
}

export interface Charger {
  id: string;
  stationId: string;
  connectorType: ConnectorType;
  powerKw: number;
  pricingModel?: string;
  pricePerKwh?: number;
  pricePerMinute?: number;
  pricePerSession?: number;
  status: ChargerStatus;
  lastStatusUpdate?: string;
}

export interface StationAmenity {
  type: string;
  name: string;
  distance?: string;
  icon: string;
}

export interface StationPhoto {
  id: string;
  url: string;
  caption?: string;
  uploadedBy: string;
  createdAt: string;
}

export interface ChargingStation {
  id: string;
  name: string;
  slug: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  district?: string;
  state: string;
  pinCode?: string;
  latitude: number;
  longitude: number;
  operator?: Operator;
  operatorId?: string;
  phone?: string;
  email?: string;
  openingHours?: Record<string, string>;
  is24x7: boolean;
  freeParking: boolean;
  isVerified: boolean;
  dataSource: string;
  sourceId?: string;
  avgRating: number;
  reviewCount: number;
  status: StationStatus;
  chargers: Charger[];
  amenities: StationAmenity[];
  photos: StationPhoto[];
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface Review {
  id: string;
  userId: string;
  stationId: string;
  rating: number;
  body: string;
  waitingMinutes?: number;
  status: ReviewStatus;
  createdAt: string;
  user?: {
    displayName: string;
    avatarUrl?: string;
  };
}

export interface Booking {
  id: string;
  userId: string;
  stationId: string;
  chargerId: string;
  slotStart: string;
  slotEnd: string;
  status: BookingStatus;
  qrCode?: string;
  station?: ChargingStation;
  createdAt: string;
}

export interface Blog {
  id: string;
  authorId: string;
  title: string;
  slug: string;
  bodyMarkdown: string;
  bodyHtml: string;
  coverImageUrl?: string;
  tags: string[];
  status: BlogStatus;
  viewCount: number;
  likeCount: number;
  routeData?: RouteData;
  publishedAt?: string;
  createdAt: string;
  author?: {
    displayName: string;
    avatarUrl?: string;
  };
}

export interface UserProfile {
  id: string;
  email?: string;
  phone?: string;
  displayName: string;
  avatarUrl?: string;
  role: UserRole;
  preferredLanguage: string;
  vehicleInfo?: VehicleInfo;
  rewardPoints: number;
  rewardTier: RewardTier;
  createdAt: string;
}

export interface VehicleInfo {
  type: VehicleType;
  make: string;
  model: string;
  year?: number;
  batteryCapacity?: number; // kWh
  range?: number; // km
  connectorType?: ConnectorType;
}

export interface RouteData {
  source: { lat: number; lng: number; name: string };
  destination: { lat: number; lng: number; name: string };
  chargingStops: {
    station: ChargingStation;
    arrivalBattery: number;
    departureBattery: number;
    chargingDuration: number; // minutes
    chargingCost: number;
  }[];
  totalDistance: number; // km
  totalTime: number; // minutes
  totalChargingCost: number;
}

export interface SearchFilters {
  query?: string;
  lat?: number;
  lng?: number;
  radius?: number; // km
  vehicleType?: VehicleType;
  connectorTypes?: ConnectorType[];
  availability?: StationStatus[];
  powerRange?: { min: number; max: number };
  maxPrice?: number;
  operators?: string[];
  minRating?: number;
  is24x7?: boolean;
  freeParking?: boolean;
  sortBy?: "distance" | "rating" | "price" | "power";
  page?: number;
  limit?: number;
}

export interface NearbyPlace {
  id: string;
  name: string;
  type: string;
  category: string;
  distance: number; // meters
  icon: string;
  lat: number;
  lng: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
