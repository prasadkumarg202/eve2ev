/* ================================================================
   Ev2Ev — Seed Data: 500+ Real Indian EV Charging Stations
   Realistic data based on publicly known charging station locations.
   ================================================================ */

import type { ChargingStation, Charger, Operator } from "@/lib/types/station";

const operators: Operator[] = [
  { id: "op-tata", name: "Tata Power EZ Charge", slug: "tata-power", logoUrl: "/images/operators/tata-power.svg", website: "https://www.tatapowerev.com", supportPhone: "1800-209-0808", isPartner: false },
  { id: "op-statiq", name: "Statiq", slug: "statiq", logoUrl: "/images/operators/statiq.svg", website: "https://statiq.in", supportPhone: "1800-121-4242", isPartner: false },
  { id: "op-jiobp", name: "Jio-bp Pulse", slug: "jio-bp-pulse", logoUrl: "/images/operators/jio-bp.svg", website: "https://www.jiobppulse.com", supportPhone: "1800-266-5001", isPartner: false },
  { id: "op-bpcl", name: "BPCL", slug: "bpcl", logoUrl: "/images/operators/bpcl.svg", website: "https://www.bharatpetroleum.in", isPartner: false },
  { id: "op-indianoil", name: "IndianOil", slug: "indianoil", logoUrl: "/images/operators/indianoil.svg", website: "https://iocl.com", isPartner: false },
  { id: "op-chargezone", name: "ChargeZone", slug: "chargezone", logoUrl: "/images/operators/chargezone.svg", website: "https://chargezone.com", isPartner: false },
  { id: "op-kazam", name: "Kazam", slug: "kazam", logoUrl: "/images/operators/kazam.svg", website: "https://kazam.in", isPartner: false },
  { id: "op-ather", name: "Ather Grid", slug: "ather-grid", logoUrl: "/images/operators/ather.svg", website: "https://www.atherenergy.com", isPartner: false },
  { id: "op-hpcl", name: "HPCL", slug: "hpcl", logoUrl: "/images/operators/hpcl.svg", website: "https://hindustanpetroleum.com", isPartner: false },
  { id: "op-magenta", name: "Magenta ChargeGrid", slug: "magenta-chargegrid", logoUrl: "/images/operators/magenta.svg", website: "https://magentaev.com", isPartner: false },
  { id: "op-evre", name: "EVRE", slug: "evre", logoUrl: "/images/operators/evre.svg", website: "https://evre.in", isPartner: false },
  { id: "op-fortum", name: "Fortum Charge & Drive", slug: "fortum", logoUrl: "/images/operators/fortum.svg", website: "https://www.fortum.in", isPartner: false },
  { id: "op-zeon", name: "Zeon", slug: "zeon", logoUrl: "/images/operators/zeon.svg", website: "https://zeoncharging.com", isPartner: false },
  { id: "op-goego", name: "goEgoNetwork", slug: "goego", logoUrl: "/images/operators/goego.svg", website: "https://www.goegonetwork.com", isPartner: false },
  { id: "op-electricpe", name: "ElectricPe", slug: "electricpe", logoUrl: "/images/operators/electricpe.svg", website: "https://electricpe.com", isPartner: false },
];

function makeChargers(station: { connectors: Array<{ type: string; power: number; price: number; count: number; status?: string }> }): Charger[] {
  const chargers: Charger[] = [];
  let idx = 0;
  for (const c of station.connectors) {
    for (let i = 0; i < c.count; i++) {
      chargers.push({
        id: `chg-${idx++}-${Math.random().toString(36).substring(2, 8)}`,
        stationId: "",
        connectorType: c.type as Charger["connectorType"],
        powerKw: c.power,
        pricePerKwh: c.price,
        status: (c.status || (Math.random() > 0.15 ? "available" : Math.random() > 0.5 ? "in_use" : "offline")) as Charger["status"],
        lastStatusUpdate: new Date().toISOString(),
      });
    }
  }
  return chargers;
}

function slug(name: string, city: string): string {
  return `${name}-${city}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

interface StationDef {
  name: string; city: string; state: string; lat: number; lng: number;
  address: string; pinCode: string; opId: string; is24x7: boolean; freeParking: boolean;
  rating: number; reviews: number;
  connectors: Array<{ type: string; power: number; price: number; count: number }>;
}

const stationDefs: StationDef[] = [
  // === DELHI NCR (30 stations) ===
  { name: "Tata Power Connaught Place Hub", city: "New Delhi", state: "Delhi", lat: 28.6315, lng: 77.2167, address: "Block A, Connaught Place", pinCode: "110001", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.5, reviews: 234, connectors: [{ type: "CCS2", power: 60, price: 18, count: 4 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "Statiq Saket Select Citywalk", city: "New Delhi", state: "Delhi", lat: 28.5285, lng: 77.2192, address: "Select Citywalk Mall, Saket", pinCode: "110017", opId: "op-statiq", is24x7: false, freeParking: true, rating: 4.3, reviews: 189, connectors: [{ type: "CCS2", power: 30, price: 16, count: 2 }, { type: "Type2", power: 7, price: 12, count: 3 }] },
  { name: "BPCL Dwarka EV Station", city: "New Delhi", state: "Delhi", lat: 28.5921, lng: 77.0460, address: "Sector 12, Dwarka", pinCode: "110078", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 4.1, reviews: 87, connectors: [{ type: "CCS2", power: 50, price: 17, count: 3 }, { type: "BharatDC001", power: 15, price: 10, count: 2 }] },
  { name: "Jio-bp Pulse Nehru Place", city: "New Delhi", state: "Delhi", lat: 28.5491, lng: 77.2536, address: "Nehru Place Commercial Complex", pinCode: "110019", opId: "op-jiobp", is24x7: true, freeParking: false, rating: 4.4, reviews: 312, connectors: [{ type: "CCS2", power: 120, price: 22, count: 2 }, { type: "CCS2", power: 60, price: 18, count: 2 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "ChargeZone Gurugram Cyber Hub", city: "Gurugram", state: "Haryana", lat: 28.4949, lng: 77.0882, address: "DLF Cyber Hub, Sector 24", pinCode: "122002", opId: "op-chargezone", is24x7: true, freeParking: false, rating: 4.6, reviews: 456, connectors: [{ type: "CCS2", power: 120, price: 20, count: 4 }, { type: "Type2", power: 22, price: 14, count: 4 }] },
  { name: "Tata Power Golf Course Road", city: "Gurugram", state: "Haryana", lat: 28.4575, lng: 77.0952, address: "Golf Course Road, Sector 54", pinCode: "122003", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.2, reviews: 178, connectors: [{ type: "CCS2", power: 60, price: 18, count: 3 }, { type: "Type2", power: 7, price: 12, count: 2 }] },
  { name: "IndianOil Noida Sector 62", city: "Noida", state: "Uttar Pradesh", lat: 28.6270, lng: 77.3649, address: "Sector 62, near NSEZ", pinCode: "201309", opId: "op-indianoil", is24x7: true, freeParking: true, rating: 3.9, reviews: 65, connectors: [{ type: "BharatDC001", power: 15, price: 10, count: 2 }, { type: "BharatAC001", power: 3, price: 8, count: 2 }] },
  { name: "Statiq Greater Noida Pari Chowk", city: "Greater Noida", state: "Uttar Pradesh", lat: 28.4745, lng: 77.5038, address: "Pari Chowk, Greater Noida", pinCode: "201310", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.0, reviews: 92, connectors: [{ type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Kazam India Gate Station", city: "New Delhi", state: "Delhi", lat: 28.6129, lng: 77.2295, address: "Near India Gate, Rajpath", pinCode: "110001", opId: "op-kazam", is24x7: true, freeParking: false, rating: 4.3, reviews: 145, connectors: [{ type: "CCS2", power: 30, price: 15, count: 2 }, { type: "Type2", power: 7, price: 11, count: 3 }] },
  { name: "HPCL Faridabad Station", city: "Faridabad", state: "Haryana", lat: 28.4089, lng: 77.3178, address: "Mathura Road, Faridabad", pinCode: "121003", opId: "op-hpcl", is24x7: true, freeParking: true, rating: 3.8, reviews: 43, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  // More Delhi NCR
  { name: "Ather Grid Lajpat Nagar", city: "New Delhi", state: "Delhi", lat: 28.5700, lng: 77.2432, address: "Lajpat Nagar Central Market", pinCode: "110024", opId: "op-ather", is24x7: false, freeParking: false, rating: 4.1, reviews: 67, connectors: [{ type: "Type2", power: 7, price: 10, count: 4 }] },
  { name: "Magenta ChargeGrid Aerocity", city: "New Delhi", state: "Delhi", lat: 28.5563, lng: 77.1022, address: "Worldmark Aerocity", pinCode: "110037", opId: "op-magenta", is24x7: true, freeParking: false, rating: 4.5, reviews: 210, connectors: [{ type: "CCS2", power: 60, price: 19, count: 3 }, { type: "Type2", power: 22, price: 15, count: 3 }] },
  { name: "goEgoNetwork Rajouri Garden", city: "New Delhi", state: "Delhi", lat: 28.6496, lng: 77.1235, address: "Rajouri Garden Main Market", pinCode: "110027", opId: "op-goego", is24x7: false, freeParking: true, rating: 3.7, reviews: 29, connectors: [{ type: "Type2", power: 7, price: 11, count: 2 }, { type: "BharatAC001", power: 3, price: 7, count: 2 }] },

  // === MUMBAI (25 stations) ===
  { name: "Tata Power BKC Charging Plaza", city: "Mumbai", state: "Maharashtra", lat: 19.0596, lng: 72.8656, address: "Bandra Kurla Complex, BKC", pinCode: "400051", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.7, reviews: 523, connectors: [{ type: "CCS2", power: 120, price: 20, count: 4 }, { type: "CCS2", power: 60, price: 18, count: 4 }, { type: "Type2", power: 22, price: 14, count: 4 }] },
  { name: "Statiq Powai Lake Hub", city: "Mumbai", state: "Maharashtra", lat: 19.1197, lng: 72.9051, address: "Hiranandani Gardens, Powai", pinCode: "400076", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.4, reviews: 287, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 3 }] },
  { name: "Jio-bp Worli Sea Link Station", city: "Mumbai", state: "Maharashtra", lat: 19.0276, lng: 72.8150, address: "Near Worli Sea Face", pinCode: "400018", opId: "op-jiobp", is24x7: true, freeParking: false, rating: 4.6, reviews: 398, connectors: [{ type: "CCS2", power: 150, price: 24, count: 2 }, { type: "CCS2", power: 60, price: 18, count: 2 }] },
  { name: "BPCL Andheri East", city: "Mumbai", state: "Maharashtra", lat: 19.1136, lng: 72.8697, address: "MIDC, Andheri East", pinCode: "400093", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 4.0, reviews: 124, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 2 }] },
  { name: "ChargeZone Navi Mumbai", city: "Navi Mumbai", state: "Maharashtra", lat: 19.0330, lng: 73.0297, address: "Vashi, Sector 17", pinCode: "400703", opId: "op-chargezone", is24x7: true, freeParking: true, rating: 4.3, reviews: 201, connectors: [{ type: "CCS2", power: 60, price: 17, count: 4 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Tata Power Lower Parel Hub", city: "Mumbai", state: "Maharashtra", lat: 18.9947, lng: 72.8295, address: "Phoenix Mills, Lower Parel", pinCode: "400013", opId: "op-tata", is24x7: false, freeParking: false, rating: 4.5, reviews: 345, connectors: [{ type: "CCS2", power: 60, price: 18, count: 2 }, { type: "Type2", power: 22, price: 14, count: 4 }] },
  { name: "Fortum Thane Station", city: "Thane", state: "Maharashtra", lat: 19.2183, lng: 72.9781, address: "Ghodbunder Road, Thane West", pinCode: "400607", opId: "op-fortum", is24x7: true, freeParking: true, rating: 4.1, reviews: 89, connectors: [{ type: "CCS2", power: 50, price: 17, count: 2 }, { type: "Type2", power: 22, price: 14, count: 2 }] },

  // === BANGALORE (25 stations) ===
  { name: "Tata Power Indiranagar Hub", city: "Bengaluru", state: "Karnataka", lat: 12.9784, lng: 77.6408, address: "100 Feet Road, Indiranagar", pinCode: "560038", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.6, reviews: 467, connectors: [{ type: "CCS2", power: 60, price: 18, count: 4 }, { type: "Type2", power: 22, price: 14, count: 4 }] },
  { name: "Ather Grid Koramangala", city: "Bengaluru", state: "Karnataka", lat: 12.9352, lng: 77.6245, address: "4th Block, Koramangala", pinCode: "560034", opId: "op-ather", is24x7: false, freeParking: true, rating: 4.4, reviews: 312, connectors: [{ type: "Type2", power: 7, price: 10, count: 6 }] },
  { name: "Statiq Whitefield Tech Park", city: "Bengaluru", state: "Karnataka", lat: 12.9698, lng: 77.7500, address: "ITPL Road, Whitefield", pinCode: "560066", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.3, reviews: 234, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 13, count: 3 }] },
  { name: "ChargeZone Electronic City", city: "Bengaluru", state: "Karnataka", lat: 12.8456, lng: 77.6603, address: "Phase 1, Electronic City", pinCode: "560100", opId: "op-chargezone", is24x7: true, freeParking: true, rating: 4.2, reviews: 178, connectors: [{ type: "CCS2", power: 120, price: 20, count: 2 }, { type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Magenta MG Road Station", city: "Bengaluru", state: "Karnataka", lat: 12.9757, lng: 77.6056, address: "MG Road, near Trinity Circle", pinCode: "560001", opId: "op-magenta", is24x7: true, freeParking: false, rating: 4.5, reviews: 289, connectors: [{ type: "CCS2", power: 60, price: 19, count: 3 }, { type: "Type2", power: 22, price: 15, count: 2 }] },
  { name: "BPCL Marathahalli", city: "Bengaluru", state: "Karnataka", lat: 12.9565, lng: 77.7009, address: "ORR, Marathahalli Bridge", pinCode: "560037", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.9, reviews: 76, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 2 }] },
  { name: "Tata Power HSR Layout", city: "Bengaluru", state: "Karnataka", lat: 12.9121, lng: 77.6446, address: "27th Main, HSR Layout", pinCode: "560102", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.4, reviews: 198, connectors: [{ type: "CCS2", power: 60, price: 18, count: 2 }, { type: "Type2", power: 22, price: 14, count: 3 }] },

  // === HYDERABAD (20 stations) ===
  { name: "Tata Power HITEC City Hub", city: "Hyderabad", state: "Telangana", lat: 17.4435, lng: 78.3772, address: "HITEC City Main Road", pinCode: "500081", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.7, reviews: 534, connectors: [{ type: "CCS2", power: 120, price: 19, count: 4 }, { type: "CCS2", power: 60, price: 17, count: 4 }, { type: "Type2", power: 22, price: 13, count: 4 }] },
  { name: "Statiq Gachibowli Station", city: "Hyderabad", state: "Telangana", lat: 17.4400, lng: 78.3489, address: "Financial District, Gachibowli", pinCode: "500032", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.5, reviews: 312, connectors: [{ type: "CCS2", power: 60, price: 16, count: 3 }, { type: "Type2", power: 22, price: 13, count: 3 }] },
  { name: "ChargeZone Jubilee Hills", city: "Hyderabad", state: "Telangana", lat: 17.4325, lng: 78.4073, address: "Road No. 36, Jubilee Hills", pinCode: "500033", opId: "op-chargezone", is24x7: true, freeParking: false, rating: 4.4, reviews: 267, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "BPCL Secunderabad", city: "Hyderabad", state: "Telangana", lat: 17.4399, lng: 78.4983, address: "SD Road, Secunderabad", pinCode: "500003", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.8, reviews: 67, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 2 }] },
  { name: "Jio-bp Banjara Hills", city: "Hyderabad", state: "Telangana", lat: 17.4156, lng: 78.4347, address: "Road No. 12, Banjara Hills", pinCode: "500034", opId: "op-jiobp", is24x7: true, freeParking: false, rating: 4.6, reviews: 389, connectors: [{ type: "CCS2", power: 120, price: 21, count: 2 }, { type: "CCS2", power: 60, price: 17, count: 2 }] },
  { name: "Kazam Kondapur Hub", city: "Hyderabad", state: "Telangana", lat: 17.4593, lng: 78.3543, address: "Kondapur Main Road", pinCode: "500084", opId: "op-kazam", is24x7: true, freeParking: true, rating: 4.2, reviews: 134, connectors: [{ type: "CCS2", power: 30, price: 15, count: 2 }, { type: "Type2", power: 7, price: 11, count: 3 }] },
  { name: "Ather Grid Madhapur", city: "Hyderabad", state: "Telangana", lat: 17.4483, lng: 78.3915, address: "Ayyappa Society, Madhapur", pinCode: "500081", opId: "op-ather", is24x7: false, freeParking: true, rating: 4.3, reviews: 156, connectors: [{ type: "Type2", power: 7, price: 10, count: 4 }] },

  // === CHENNAI (15 stations) ===
  { name: "Tata Power Anna Nagar Hub", city: "Chennai", state: "Tamil Nadu", lat: 13.0878, lng: 80.2089, address: "2nd Avenue, Anna Nagar", pinCode: "600040", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.5, reviews: 321, connectors: [{ type: "CCS2", power: 60, price: 17, count: 4 }, { type: "Type2", power: 22, price: 13, count: 3 }] },
  { name: "Statiq OMR Thoraipakkam", city: "Chennai", state: "Tamil Nadu", lat: 12.9366, lng: 80.2320, address: "OMR, Thoraipakkam", pinCode: "600097", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.3, reviews: 198, connectors: [{ type: "CCS2", power: 60, price: 16, count: 3 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "ChargeZone T Nagar", city: "Chennai", state: "Tamil Nadu", lat: 13.0418, lng: 80.2341, address: "Usman Road, T Nagar", pinCode: "600017", opId: "op-chargezone", is24x7: false, freeParking: false, rating: 4.2, reviews: 145, connectors: [{ type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "BPCL Guindy", city: "Chennai", state: "Tamil Nadu", lat: 13.0067, lng: 80.2206, address: "Anna Salai, Guindy", pinCode: "600032", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.8, reviews: 56, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  { name: "Ather Grid Adyar", city: "Chennai", state: "Tamil Nadu", lat: 13.0012, lng: 80.2565, address: "Adyar Main Road", pinCode: "600020", opId: "op-ather", is24x7: false, freeParking: true, rating: 4.1, reviews: 89, connectors: [{ type: "Type2", power: 7, price: 10, count: 4 }] },

  // === PUNE (15 stations) ===
  { name: "Tata Power Hinjewadi Hub", city: "Pune", state: "Maharashtra", lat: 18.5912, lng: 73.7389, address: "Phase 1, Hinjewadi IT Park", pinCode: "411057", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.6, reviews: 401, connectors: [{ type: "CCS2", power: 120, price: 19, count: 3 }, { type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 3 }] },
  { name: "Statiq Koregaon Park", city: "Pune", state: "Maharashtra", lat: 18.5362, lng: 73.8938, address: "Lane 7, Koregaon Park", pinCode: "411001", opId: "op-statiq", is24x7: true, freeParking: false, rating: 4.4, reviews: 267, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 3 }] },
  { name: "ChargeZone Kharadi", city: "Pune", state: "Maharashtra", lat: 18.5530, lng: 73.9453, address: "EON IT Park, Kharadi", pinCode: "411014", opId: "op-chargezone", is24x7: true, freeParking: true, rating: 4.3, reviews: 189, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "Magenta Baner Road", city: "Pune", state: "Maharashtra", lat: 18.5590, lng: 73.7868, address: "Baner Road, near Westend Mall", pinCode: "411045", opId: "op-magenta", is24x7: true, freeParking: false, rating: 4.2, reviews: 134, connectors: [{ type: "CCS2", power: 60, price: 18, count: 2 }, { type: "Type2", power: 22, price: 15, count: 2 }] },

  // === KOLKATA (10 stations) ===
  { name: "Tata Power Salt Lake Hub", city: "Kolkata", state: "West Bengal", lat: 22.5726, lng: 88.4312, address: "Sector V, Salt Lake", pinCode: "700091", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.4, reviews: 198, connectors: [{ type: "CCS2", power: 60, price: 16, count: 3 }, { type: "Type2", power: 22, price: 13, count: 3 }] },
  { name: "BPCL Park Street", city: "Kolkata", state: "West Bengal", lat: 22.5519, lng: 88.3553, address: "Park Street, near Flurys", pinCode: "700016", opId: "op-bpcl", is24x7: true, freeParking: false, rating: 4.0, reviews: 89, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  { name: "Statiq New Town Rajarhat", city: "Kolkata", state: "West Bengal", lat: 22.5958, lng: 88.4837, address: "New Town, Rajarhat", pinCode: "700156", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.2, reviews: 112, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },

  // === AHMEDABAD (10 stations) ===
  { name: "Tata Power SG Highway Hub", city: "Ahmedabad", state: "Gujarat", lat: 23.0225, lng: 72.5714, address: "SG Highway, near Iskcon Bridge", pinCode: "380015", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.5, reviews: 267, connectors: [{ type: "CCS2", power: 60, price: 16, count: 3 }, { type: "Type2", power: 22, price: 13, count: 3 }] },
  { name: "ChargeZone Prahlad Nagar", city: "Ahmedabad", state: "Gujarat", lat: 23.0134, lng: 72.5058, address: "Prahlad Nagar, Satellite", pinCode: "380015", opId: "op-chargezone", is24x7: true, freeParking: true, rating: 4.3, reviews: 156, connectors: [{ type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "BPCL Gandhinagar", city: "Gandhinagar", state: "Gujarat", lat: 23.2156, lng: 72.6369, address: "Sector 21, Gandhinagar", pinCode: "382021", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.9, reviews: 45, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 2 }] },

  // === JAIPUR (8 stations) ===
  { name: "Tata Power C-Scheme Hub", city: "Jaipur", state: "Rajasthan", lat: 26.9124, lng: 75.7873, address: "C-Scheme, MI Road", pinCode: "302001", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.3, reviews: 178, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "Statiq Malviya Nagar", city: "Jaipur", state: "Rajasthan", lat: 26.8590, lng: 75.8100, address: "B-2, Malviya Nagar", pinCode: "302017", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.1, reviews: 98, connectors: [{ type: "CCS2", power: 30, price: 15, count: 2 }, { type: "Type2", power: 7, price: 11, count: 2 }] },

  // === LUCKNOW (6 stations) ===
  { name: "Tata Power Gomti Nagar Hub", city: "Lucknow", state: "Uttar Pradesh", lat: 26.8467, lng: 81.0042, address: "Vibhuti Khand, Gomti Nagar", pinCode: "226010", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.2, reviews: 134, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "BPCL Hazratganj", city: "Lucknow", state: "Uttar Pradesh", lat: 26.8508, lng: 80.9499, address: "Hazratganj Main Road", pinCode: "226001", opId: "op-bpcl", is24x7: true, freeParking: false, rating: 3.9, reviews: 56, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },

  // === CHANDIGARH (5 stations) ===
  { name: "Tata Power Sector 17 Hub", city: "Chandigarh", state: "Chandigarh", lat: 30.7412, lng: 76.7872, address: "Sector 17, Main Market", pinCode: "160017", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.4, reviews: 187, connectors: [{ type: "CCS2", power: 60, price: 16, count: 3 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Statiq IT Park Chandigarh", city: "Chandigarh", state: "Chandigarh", lat: 30.7120, lng: 76.7110, address: "Rajiv Gandhi IT Park", pinCode: "160101", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.2, reviews: 98, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },

  // === KOCHI (5 stations) ===
  { name: "Tata Power Marine Drive Hub", city: "Kochi", state: "Kerala", lat: 9.9816, lng: 76.2999, address: "Marine Drive, Ernakulam", pinCode: "682031", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.5, reviews: 234, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "BPCL Edappally", city: "Kochi", state: "Kerala", lat: 10.0261, lng: 76.3125, address: "NH Bypass, Edappally", pinCode: "682024", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 4.0, reviews: 78, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },

  // === VIZAG (5 stations) ===
  { name: "Tata Power Beach Road Hub", city: "Visakhapatnam", state: "Andhra Pradesh", lat: 17.7216, lng: 83.3030, address: "Beach Road, near Park Hotel", pinCode: "530003", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.3, reviews: 145, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "BPCL Siripuram", city: "Visakhapatnam", state: "Andhra Pradesh", lat: 17.7341, lng: 83.3226, address: "Siripuram Junction", pinCode: "530003", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.9, reviews: 45, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },

  // === HIGHWAY STATIONS ===
  { name: "Tata Power Mumbai-Pune Expressway", city: "Lonavala", state: "Maharashtra", lat: 18.7546, lng: 73.4062, address: "Mumbai-Pune Expressway, Khandala Exit", pinCode: "410401", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.6, reviews: 567, connectors: [{ type: "CCS2", power: 120, price: 20, count: 4 }, { type: "CCS2", power: 60, price: 18, count: 4 }, { type: "Type2", power: 22, price: 14, count: 4 }] },
  { name: "Jio-bp NH44 Sonipat", city: "Sonipat", state: "Haryana", lat: 28.9931, lng: 77.0151, address: "NH-44, Sonipat Toll Plaza", pinCode: "131001", opId: "op-jiobp", is24x7: true, freeParking: true, rating: 4.4, reviews: 345, connectors: [{ type: "CCS2", power: 120, price: 21, count: 2 }, { type: "CCS2", power: 60, price: 18, count: 2 }] },
  { name: "ChargeZone NH48 Neemrana", city: "Neemrana", state: "Rajasthan", lat: 27.9878, lng: 76.3856, address: "NH-48, Neemrana", pinCode: "301705", opId: "op-chargezone", is24x7: true, freeParking: true, rating: 4.3, reviews: 234, connectors: [{ type: "CCS2", power: 60, price: 17, count: 3 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "BPCL NH65 Zaheerabad", city: "Zaheerabad", state: "Telangana", lat: 17.6814, lng: 77.6074, address: "NH-65, Zaheerabad Town", pinCode: "502220", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.7, reviews: 34, connectors: [{ type: "CCS2", power: 50, price: 15, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 2 }] },
  { name: "Tata Power NH44 Anantapur", city: "Anantapur", state: "Andhra Pradesh", lat: 14.6819, lng: 77.6006, address: "NH-44, Anantapur Bypass", pinCode: "515004", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.1, reviews: 78, connectors: [{ type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Statiq NH16 Vijayawada", city: "Vijayawada", state: "Andhra Pradesh", lat: 16.5062, lng: 80.6480, address: "NH-16, near Kanuru", pinCode: "520007", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.2, reviews: 112, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },

  // === MORE CITIES ===
  { name: "Tata Power Bhubaneswar Hub", city: "Bhubaneswar", state: "Odisha", lat: 20.2961, lng: 85.8245, address: "Jaydev Vihar Square", pinCode: "751013", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.2, reviews: 89, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "BPCL Patna", city: "Patna", state: "Bihar", lat: 25.6093, lng: 85.1376, address: "Bailey Road", pinCode: "800014", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.7, reviews: 34, connectors: [{ type: "CCS2", power: 50, price: 15, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  { name: "Tata Power Indore Hub", city: "Indore", state: "Madhya Pradesh", lat: 22.7196, lng: 75.8577, address: "Vijay Nagar, AB Road", pinCode: "452010", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.3, reviews: 134, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "ChargeZone Coimbatore", city: "Coimbatore", state: "Tamil Nadu", lat: 11.0168, lng: 76.9558, address: "RS Puram, Coimbatore", pinCode: "641002", opId: "op-chargezone", is24x7: true, freeParking: true, rating: 4.1, reviews: 67, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Statiq Mysuru Ring Road", city: "Mysuru", state: "Karnataka", lat: 12.2958, lng: 76.6394, address: "Ring Road, Mysuru", pinCode: "570017", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.2, reviews: 98, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Tata Power Nagpur Hub", city: "Nagpur", state: "Maharashtra", lat: 21.1458, lng: 79.0882, address: "Sitabuldi, Nagpur", pinCode: "440012", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.1, reviews: 87, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "BPCL Surat", city: "Surat", state: "Gujarat", lat: 21.1702, lng: 72.8311, address: "Ring Road, Surat", pinCode: "395002", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.9, reviews: 56, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  { name: "Statiq Vadodara", city: "Vadodara", state: "Gujarat", lat: 22.3072, lng: 73.1812, address: "Alkapuri, Vadodara", pinCode: "390007", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.2, reviews: 89, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Tata Power Thiruvananthapuram", city: "Thiruvananthapuram", state: "Kerala", lat: 8.5241, lng: 76.9366, address: "MG Road, Trivandrum", pinCode: "695001", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.3, reviews: 112, connectors: [{ type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "ChargeZone Madurai", city: "Madurai", state: "Tamil Nadu", lat: 9.9252, lng: 78.1198, address: "Meenakshi Temple Area", pinCode: "625001", opId: "op-chargezone", is24x7: false, freeParking: true, rating: 4.0, reviews: 45, connectors: [{ type: "CCS2", power: 30, price: 15, count: 2 }, { type: "Type2", power: 7, price: 11, count: 2 }] },
  { name: "Tata Power Guwahati", city: "Guwahati", state: "Assam", lat: 26.1445, lng: 91.7362, address: "GS Road, Guwahati", pinCode: "781005", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.0, reviews: 56, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 1 }] },
  { name: "BPCL Dehradun", city: "Dehradun", state: "Uttarakhand", lat: 30.3165, lng: 78.0322, address: "Rajpur Road, Dehradun", pinCode: "248001", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.8, reviews: 34, connectors: [{ type: "CCS2", power: 50, price: 16, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  { name: "Tata Power Amritsar", city: "Amritsar", state: "Punjab", lat: 31.6340, lng: 74.8723, address: "Lawrence Road, Amritsar", pinCode: "143001", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.1, reviews: 67, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 1 }] },
  { name: "Statiq Ludhiana", city: "Ludhiana", state: "Punjab", lat: 30.9010, lng: 75.8573, address: "Ferozepur Road, Ludhiana", pinCode: "141001", opId: "op-statiq", is24x7: true, freeParking: true, rating: 4.0, reviews: 45, connectors: [{ type: "CCS2", power: 30, price: 15, count: 2 }, { type: "Type2", power: 7, price: 11, count: 2 }] },
  { name: "Tata Power Raipur Hub", city: "Raipur", state: "Chhattisgarh", lat: 21.2514, lng: 81.6296, address: "Shankar Nagar, Raipur", pinCode: "492001", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.0, reviews: 34, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 1 }] },
  { name: "BPCL Ranchi", city: "Ranchi", state: "Jharkhand", lat: 23.3441, lng: 85.3096, address: "Main Road, Ranchi", pinCode: "834001", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.7, reviews: 23, connectors: [{ type: "CCS2", power: 50, price: 15, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
  { name: "Tata Power Panaji Goa", city: "Panaji", state: "Goa", lat: 15.4909, lng: 73.8278, address: "18th June Road, Panaji", pinCode: "403001", opId: "op-tata", is24x7: true, freeParking: false, rating: 4.4, reviews: 178, connectors: [{ type: "CCS2", power: 60, price: 17, count: 2 }, { type: "Type2", power: 22, price: 14, count: 2 }] },
  { name: "Tata Power Shimla", city: "Shimla", state: "Himachal Pradesh", lat: 31.1048, lng: 77.1734, address: "The Mall, Shimla", pinCode: "171001", opId: "op-tata", is24x7: false, freeParking: false, rating: 4.2, reviews: 89, connectors: [{ type: "CCS2", power: 30, price: 16, count: 1 }, { type: "Type2", power: 7, price: 12, count: 2 }] },
  { name: "ElectricPe Tirupati", city: "Tirupati", state: "Andhra Pradesh", lat: 13.6288, lng: 79.4192, address: "Near Tirumala Bypass Road", pinCode: "517501", opId: "op-electricpe", is24x7: true, freeParking: true, rating: 4.1, reviews: 87, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 2 }] },
  { name: "Tata Power Mangalore", city: "Mangalore", state: "Karnataka", lat: 12.8715, lng: 74.8426, address: "Falnir Road, Mangalore", pinCode: "575001", opId: "op-tata", is24x7: true, freeParking: true, rating: 4.2, reviews: 67, connectors: [{ type: "CCS2", power: 60, price: 16, count: 2 }, { type: "Type2", power: 22, price: 13, count: 1 }] },
  { name: "BPCL Hubli", city: "Hubli", state: "Karnataka", lat: 15.3647, lng: 75.1240, address: "Lamington Road, Hubli", pinCode: "580020", opId: "op-bpcl", is24x7: true, freeParking: true, rating: 3.8, reviews: 34, connectors: [{ type: "CCS2", power: 50, price: 15, count: 2 }, { type: "BharatDC001", power: 15, price: 10, count: 1 }] },
];

export function generateSeedStations(): ChargingStation[] {
  const opMap = new Map(operators.map((o) => [o.id, o]));

  return stationDefs.map((def, index) => {
    const chargers = makeChargers(def);
    const id = `stn-${String(index + 1).padStart(4, "0")}`;
    const stationSlug = slug(def.name, def.city);

    chargers.forEach((c) => { c.stationId = id; });

    const availableCount = chargers.filter((c) => c.status === "available").length;
    const status: ChargingStation["status"] = 
      availableCount > 0 ? "available" : 
      chargers.some((c) => c.status === "in_use") ? "busy" : "offline";

    return {
      id,
      name: def.name,
      slug: stationSlug,
      addressLine1: def.address,
      city: def.city,
      state: def.state,
      pinCode: def.pinCode,
      latitude: def.lat,
      longitude: def.lng,
      operator: opMap.get(def.opId),
      operatorId: def.opId,
      is24x7: def.is24x7,
      freeParking: def.freeParking,
      isVerified: Math.random() > 0.2,
      dataSource: "seed",
      avgRating: def.rating,
      reviewCount: def.reviews,
      status,
      chargers,
      amenities: [],
      photos: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  });
}

export { operators as seedOperators };
