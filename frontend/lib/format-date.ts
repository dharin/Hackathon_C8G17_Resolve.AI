// Deterministic date formatting without Intl. toLocaleString output differs
// byte-for-byte across ICU versions (e.g. narrow no-break space U+202F vs a
// plain space before AM/PM in Node vs the browser), which breaks React
// hydration on SSR'd text. Manual UTC formatting guarantees identical output
// on server and client.

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
] as const;

function timeParts(date: Date) {
  const hours24 = date.getUTCHours();
  const period = hours24 >= 12 ? "PM" : "AM";
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return { hours12, minutes, period };
}

/** e.g. "Jul 19, 08:12 AM" (UTC) */
export function formatShortTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const { hours12, minutes, period } = timeParts(date);
  const paddedHours = String(hours12).padStart(2, "0");
  return `${MONTHS[date.getUTCMonth()]} ${date.getUTCDate()}, ${paddedHours}:${minutes} ${period}`;
}

/** e.g. "Jul 19, 2026, 8:12 AM" (UTC) */
export function formatFullTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const { hours12, minutes, period } = timeParts(date);
  return `${MONTHS[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}, ${hours12}:${minutes} ${period}`;
}
