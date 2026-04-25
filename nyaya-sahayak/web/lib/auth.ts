/**
 * Tiny client-side "auth" using localStorage.
 * Google Identity Services (One Tap) sets the user object here.
 * For the hackathon the JWT is not server-validated; we just store profile data.
 */

export interface UserProfile {
  name: string;
  email: string;
  picture?: string;
  /** Filled during onboarding */
  age?: number;
  gender?: string;
  state?: string;
  locality?: string;
  caste?: string;
  occupation?: string;
  annual_income?: string;
  education?: string;
  onboarded?: boolean;
}

const KEY = "nyaya_user";

export function getUser(): UserProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as UserProfile) : null;
  } catch {
    return null;
  }
}

export function saveUser(u: UserProfile): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(u));
}

export function clearUser(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}
