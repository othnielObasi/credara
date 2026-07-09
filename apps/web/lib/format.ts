export function fmt(value: number | string | undefined, currency = '£') {
  return `${currency}${Number(value || 0).toLocaleString('en-GB')}`;
}

export function titleCase(value: string | undefined) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function statusTone(status: string) {
  if (/confirmed|active|ready|verified|anchored|tokenized|released|approved|low|valid|funded/i.test(status)) return 'green';
  if (/pending|submitted|review|sent|offer|medium|partial/i.test(status)) return 'amber';
  if (/disputed|rejected|high|failed|blocked/i.test(status)) return 'red';
  return 'grey';
}
