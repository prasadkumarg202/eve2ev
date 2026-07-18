/* ================================================================
   Ev2Ev — Constants
   ================================================================ */

export const SITE_NAME = "Ev2Ev";
export const SITE_TAGLINE = "Every Charger. One Platform.";
export const SITE_DESCRIPTION =
  "India's unified EV charging discovery platform. Find, compare, and book EV chargers across all operators — Tata Power, Statiq, Jio-bp, BPCL, and 50+ more.";
export const SITE_URL = "https://ev2ev.in";

export const DEFAULT_MAP_CENTER = { lat: 20.5937, lng: 78.9629 }; // Center of India
export const DEFAULT_MAP_ZOOM = 5;
export const INDIA_BOUNDS = {
  sw: { lat: 6.5, lng: 68.0 },
  ne: { lat: 37.0, lng: 97.5 },
};

export const CONNECTOR_TYPES = [
  { value: "CCS2", label: "CCS2", description: "Combined Charging System 2", color: "#3b82f6" },
  { value: "Type2", label: "Type 2", description: "IEC 62196 Type 2", color: "#8b5cf6" },
  { value: "BharatAC001", label: "Bharat AC-001", description: "Indian AC Standard", color: "#10b94e" },
  { value: "BharatDC001", label: "Bharat DC-001", description: "Indian DC Standard", color: "#f59e0b" },
  { value: "CHAdeMO", label: "CHAdeMO", description: "Japan DC Standard", color: "#ef4444" },
  { value: "GBT", label: "GB/T", description: "China Standard", color: "#ec4899" },
] as const;

export const VEHICLE_TYPES = [
  { value: "bike", label: "Bike", icon: "🏍️" },
  { value: "scooter", label: "Scooter", icon: "🛵" },
  { value: "auto", label: "Auto", icon: "🛺" },
  { value: "car", label: "Car", icon: "🚗" },
  { value: "bus", label: "Bus", icon: "🚌" },
  { value: "truck", label: "Truck", icon: "🚛" },
] as const;

export const POWER_LEVELS = [
  { value: 3, label: "3 kW", tier: "Slow" },
  { value: 7, label: "7 kW", tier: "Slow" },
  { value: 15, label: "15 kW", tier: "Moderate" },
  { value: 30, label: "30 kW", tier: "Fast" },
  { value: 60, label: "60 kW", tier: "Fast" },
  { value: 120, label: "120 kW", tier: "Rapid" },
  { value: 240, label: "240 kW+", tier: "Ultra-Rapid" },
] as const;

export const STATION_STATUSES = [
  { value: "available", label: "Available", color: "#10b94e" },
  { value: "busy", label: "Busy", color: "#f59e0b" },
  { value: "offline", label: "Offline", color: "#ef4444" },
  { value: "maintenance", label: "Under Maintenance", color: "#6b7280" },
] as const;

export const AMENITY_CATEGORIES = [
  { type: "restaurant", label: "Restaurants", icon: "🍽️" },
  { type: "hotel", label: "Hotels", icon: "🏨" },
  { type: "tea_stall", label: "Tea Stalls", icon: "☕" },
  { type: "coffee_shop", label: "Coffee Shops", icon: "☕" },
  { type: "restroom", label: "Restrooms", icon: "🚻" },
  { type: "hospital", label: "Hospitals", icon: "🏥" },
  { type: "medical_store", label: "Medical Stores", icon: "💊" },
  { type: "mechanic", label: "Mechanics", icon: "🔧" },
  { type: "tyre_repair", label: "Tyre Repair", icon: "🛞" },
  { type: "petrol_pump", label: "Petrol Pumps", icon: "⛽" },
  { type: "atm", label: "ATMs", icon: "🏧" },
  { type: "shopping_mall", label: "Shopping Malls", icon: "🛍️" },
  { type: "tourist_attraction", label: "Tourist Attractions", icon: "🏛️" },
  { type: "temple", label: "Temples", icon: "🛕" },
  { type: "parking", label: "Parking", icon: "🅿️" },
  { type: "ev_service", label: "EV Service Centers", icon: "🔋" },
] as const;

export const REWARD_TIERS = [
  { tier: "bronze", label: "Bronze Explorer", minPoints: 0, icon: "🥉" },
  { tier: "silver", label: "Silver Explorer", minPoints: 500, icon: "🥈" },
  { tier: "gold", label: "Gold Explorer", minPoints: 2000, icon: "🥇" },
  { tier: "platinum", label: "Platinum Explorer", minPoints: 5000, icon: "💎" },
] as const;

export const REWARD_ACTIONS = {
  review: { points: 20, label: "Write a Review" },
  photo: { points: 10, label: "Upload a Photo" },
  edit: { points: 15, label: "Suggest an Edit" },
  verified_update: { points: 30, label: "Verified Update" },
  blog: { points: 50, label: "Publish a Blog" },
  bug_report: { points: 25, label: "Bug Report" },
} as const;

export const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
] as const;

export const MAJOR_HIGHWAYS = [
  { id: "nh44", name: "NH-44", description: "Delhi to Chennai", length: "2369 km" },
  { id: "nh48", name: "NH-48", description: "Delhi to Mumbai", length: "1428 km" },
  { id: "nh65", name: "NH-65", description: "Pune to Machilipatnam", length: "841 km" },
  { id: "nh16", name: "NH-16", description: "Chennai to Kolkata", length: "2271 km" },
  { id: "nh19", name: "NH-19", description: "Delhi to Kolkata", length: "1435 km" },
  { id: "nh30", name: "NH-30", description: "Lucknow to Buxar", length: "467 km" },
] as const;

export const LANGUAGES = [
  { code: "en", name: "English", nativeName: "English" },
  { code: "hi", name: "Hindi", nativeName: "हिन्दी" },
  { code: "te", name: "Telugu", nativeName: "తెలుగు" },
  { code: "ta", name: "Tamil", nativeName: "தமிழ்" },
  { code: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ" },
  { code: "ml", name: "Malayalam", nativeName: "മലയാളം" },
  { code: "mr", name: "Marathi", nativeName: "मराठी" },
  { code: "gu", name: "Gujarati", nativeName: "ગુજરાતી" },
  { code: "bn", name: "Bengali", nativeName: "বাংলা" },
  { code: "pa", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ" },
  { code: "or", name: "Odia", nativeName: "ଓଡ଼ିଆ" },
] as const;

export const OPERATORS_LIST = [
  "Tata Power EZ Charge",
  "Statiq",
  "Jio-bp Pulse",
  "BPCL",
  "IndianOil",
  "ChargeZone",
  "Kazam",
  "EVI Technologies",
  "GLIDA",
  "Relux",
  "Zeon",
  "EVRE",
  "Ather Grid",
  "HPCL",
  "Fortum Charge & Drive",
  "Exicom",
  "Delta Electronics",
  "Okaya EV",
  "Magenta ChargeGrid",
  "Charge+Zone",
  "goEgoNetwork",
  "ElectricPe",
  "Turno",
] as const;
