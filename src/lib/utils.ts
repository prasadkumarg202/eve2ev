/* ================================================================
   Ev2Ev — Utility Functions: cn (class name merger)
   ================================================================ */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
