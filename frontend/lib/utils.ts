import type { TaxReturn } from "./types";

const STORAGE_KEY = "taxapp_return";
const STEP_KEY = "taxapp_step";

export function saveReturn(data: Partial<TaxReturn>): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function loadReturn(): Partial<TaxReturn> | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Partial<TaxReturn>) : null;
  } catch {
    return null;
  }
}

export function clearReturn(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(STORAGE_KEY);
  sessionStorage.removeItem(STEP_KEY);
}

export function saveStep(step: number): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STEP_KEY, String(step));
}

export function loadStep(): number {
  if (typeof window === "undefined") return 1;
  return parseInt(sessionStorage.getItem(STEP_KEY) ?? "1", 10);
}

/** Format a dollar string (e.g. "12345.67" → "$12,345.67") */
export function formatDollar(raw: string | number): string {
  const num = typeof raw === "string" ? parseFloat(raw) : raw;
  if (isNaN(num)) return "$0";
  const abs = Math.abs(num);
  const formatted = abs.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  return num < 0 ? `−${formatted}` : formatted;
}

/** Format a percentage string (e.g. "0.2143" → "21.4%") */
export function formatPct(raw: string | number): string {
  const num = typeof raw === "string" ? parseFloat(raw) : raw;
  if (isNaN(num)) return "0%";
  return (num * 100).toFixed(1) + "%";
}

export const FILING_STATUS_LABELS: Record<string, string> = {
  single: "Single",
  married_filing_jointly: "Married Filing Jointly",
  married_filing_separately: "Married Filing Separately",
  head_of_household: "Head of Household",
  qualifying_surviving_spouse: "Qualifying Surviving Spouse",
};

export const STATE_OPTIONS = [
  { value: "IL", label: "Illinois" },
  { value: "MN", label: "Minnesota" },
];

/** Short aliases for new result components (always numeric) */
export function fmtDollar(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

export function fmtPct(n: number): string {
  return (n * 100).toFixed(1) + "%";
}
