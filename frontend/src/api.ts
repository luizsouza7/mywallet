export type User = { id: number; name: string; email: string };
export type Account = { id: number; name: string; kind: string; opening_balance_cents: number; balance_cents: number };
export type Transaction = { id: number; account_id: number; account_name: string; description: string; amount_cents: number; direction: 'income' | 'expense'; category: string; booked_on: string; import_batch_id: number | null };
export type TransactionInput = Pick<Transaction, 'account_id' | 'description' | 'amount_cents' | 'direction' | 'category' | 'booked_on'>;
export type Summary = { balance_cents: number; income_cents: number; expense_cents: number; entries: number; categories: { category: string; amount_cents: number }[] };
export type PreviewRow = { date: string; description: string; amount_cents: number; direction: 'income' | 'expense'; category: string; fingerprint: string; duplicate: boolean; source_id?: string };
export type Preview = { rows: PreviewRow[]; errors: string[] };
export type ImportRecord = { id: number; filename: string; created_at: string; inserted_count: number; account_name: string };

const storageKey = 'mywallet_web_session';
export const sessionToken = () => sessionStorage.getItem(storageKey);
export const setToken = (token: string | null) => {
  if (token) sessionStorage.setItem(storageKey, token);
  else sessionStorage.removeItem(storageKey);
};

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = sessionToken();
  if (token) headers.set('Authorization', 'Bearer ' + token);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  let response: Response;
  try {
    response = await fetch('/api' + path, { ...init, headers });
  } catch {
    throw new Error('Não foi possível conectar ao servidor. Verifique se a API está em execução.');
  }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/login')) {
      setToken(null);
      window.dispatchEvent(new Event('mywallet-unauthorized'));
    }
    const data: { detail?: string | { msg?: string }[] } = await response.json().catch(() => ({}));
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(v => v.msg).join('; ') : 'Erro HTTP ' + response.status);
  }
  return response.json() as Promise<T>;
}

export const money = (cents: number) => new Intl.NumberFormat('pt-BR', {
  style: 'currency', currency: 'BRL'
}).format(cents / 100);

export function centsFromInput(raw: string): number {
  const normalized = raw.trim().replace(/r\$/gi, '').replace(/\s/g, '');
  const number = normalized.includes(',')
    ? normalized.replace(/\./g, '').replace(',', '.')
    : normalized;
  if (!/^\d+(\.\d{1,2})?$/.test(number)) throw new Error('Informe um valor válido, como 49,90.');
  const [whole, fraction = ''] = number.split('.');
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  if (!Number.isSafeInteger(cents) || cents <= 0) throw new Error('Valor fora do limite.');
  return cents;
}

export function shortDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return d + '/' + m + '/' + y;
}
