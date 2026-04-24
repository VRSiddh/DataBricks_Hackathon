/**
 * Empty string = same origin (FastAPI + static served from one Databricks App).
 * Override in dev: NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
 */
export function getApiBase(): string {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE.replace(/\/$/, "");
  }
  return "";
}

export async function fetchHealth() {
  const b = getApiBase();
  const r = await fetch(`${b}/api/health`, { cache: "no-store" });
  if (!r.ok) throw new Error(`Health check failed: ${r.status}`);
  return r.json() as Promise<{ status: string; service: string }>;
}
