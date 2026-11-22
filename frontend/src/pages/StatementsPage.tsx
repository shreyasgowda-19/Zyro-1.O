import React, { useEffect, useState } from 'react';
import { AlertCircle, Download, FileText, Upload } from 'lucide-react';
import { api } from '../services/api';
import type { ImportedStatementRow, StatementRequest } from '../types';

interface PreviewRow extends ImportedStatementRow {
  displayDate: string;
  description: string;
  hasSourceCategory: boolean;
}

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = '';
  let quoted = false;
  const input = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < input.length; i += 1) {
    const char = input[i];
    if (char === '"' && quoted && input[i + 1] === '"') { cell += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { row.push(cell.trim()); cell = ''; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && input[i + 1] === '\n') i += 1;
      row.push(cell.trim());
      if (row.some((value) => value.length > 0)) rows.push(row);
      row = []; cell = '';
    } else cell += char;
  }
  row.push(cell.trim());
  if (row.some((value) => value.length > 0)) rows.push(row);
  return rows;
}

function parseDate(value: string): Date | null {
  const dmy = value.trim().match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$/);
  let date: Date;
  if (dmy) {
    const year = Number(dmy[3].length === 2 ? `20${dmy[3]}` : dmy[3]);
    date = new Date(Date.UTC(year, Number(dmy[2]) - 1, Number(dmy[1]), 12));
  } else date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function parseMoney(value: string): number | null {
  const text = value.trim();
  if (!text) return null;
  const negativeByParentheses = /^\(.*\)$/.test(text);
  const normalized = text.replace(/[₹,$\s,]/g, '').replace(/[()]/g, '');
  if (!/^[+-]?\d+(\.\d{1,2})?$/.test(normalized)) return null;
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed) || Math.abs(parsed) > 10000000000) return null;
  const paise = Math.round(parsed * 100);
  return negativeByParentheses ? -Math.abs(paise) : paise;
}

function columnIndex(headers: string[], names: string[]): number {
  return headers.findIndex((header) => names.includes(header.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()));
}

async function readStatementCsv(file: File): Promise<{ hash: string; rows: PreviewRow[] }> {
  if (file.size > 5 * 1024 * 1024) throw new Error('Choose a CSV file smaller than 5 MB.');
  const [text, digest] = await Promise.all([
    file.text(),
    crypto.subtle.digest('SHA-256', await file.arrayBuffer()),
  ]);
  const hash = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
  const matrix = parseCsv(text);
  if (matrix.length < 2) throw new Error('The CSV needs a header row and at least one transaction.');
  const headers = matrix[0].map((header) => header.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim());
  const dateCol = columnIndex(headers, ['date', 'transaction date', 'posting date', 'value date']);
  const descCol = columnIndex(headers, ['description', 'narration', 'details', 'particulars', 'transaction details', 'remarks']);
  const amountCol = columnIndex(headers, ['amount', 'transaction amount']);
  const debitCol = columnIndex(headers, ['debit', 'debit amount', 'withdrawal', 'withdrawal amount']);
  const creditCol = columnIndex(headers, ['credit', 'credit amount', 'deposit', 'deposit amount']);
  const typeCol = columnIndex(headers, ['type', 'transaction type', 'dr cr', 'debit credit']);
  const categoryCol = columnIndex(headers, ['category']);
  if (dateCol < 0 || (amountCol < 0 && debitCol < 0 && creditCol < 0)) {
    throw new Error('CSV must include a date column and an amount, debit, or credit column.');
  }

  const output: PreviewRow[] = [];
  for (let i = 1; i < matrix.length; i += 1) {
    const cells = matrix[i];
    const rawDate = cells[dateCol] || '';
    const date = parseDate(rawDate);
    let signedPaise: number | null = null;
    let inferredType: 'income' | 'expense' = 'expense';
    if (debitCol >= 0 || creditCol >= 0) {
      const debit = debitCol >= 0 ? parseMoney(cells[debitCol] || '') : null;
      const credit = creditCol >= 0 ? parseMoney(cells[creditCol] || '') : null;
      if ((debit ?? 0) > 0) { signedPaise = debit; inferredType = 'expense'; }
      else if ((credit ?? 0) > 0) { signedPaise = credit; inferredType = 'income'; }
    }
    if (signedPaise === null && amountCol >= 0) {
      const amount = parseMoney(cells[amountCol] || '');
      if (amount !== null && amount !== 0) {
        inferredType = amount < 0 ? 'expense' : 'income';
        signedPaise = Math.abs(amount);
      }
    }
    const typeText = typeCol >= 0 ? (cells[typeCol] || '').toLowerCase() : '';
    if (typeText.match(/\b(dr|debit|withdrawal|expense|spent)\b/)) inferredType = 'expense';
    else if (typeText.match(/\b(cr|credit|deposit|income)\b/)) inferredType = 'income';
    if (!date || !signedPaise || signedPaise > 1000000000000) {
      throw new Error(`Could not read the date or amount on CSV row ${i + 1}.`);
    }
    const description = descCol >= 0 ? (cells[descCol] || '').trim().slice(0, 140) : '';
    const category = categoryCol >= 0 ? (cells[categoryCol] || '').trim().slice(0, 50) : '';
    output.push({
      type: inferredType,
      amount_paise: signedPaise,
      category: category || 'General',
      note: description || undefined,
      created_at: date.toISOString(),
      row_number: i + 1,
      displayDate: rawDate,
      description: description || 'Transaction',
      hasSourceCategory: Boolean(category),
    });
  }
  if (output.length > 500) throw new Error('This importer accepts up to 500 transactions at a time.');
  return { hash, rows: output };
}

export const StatementsPage: React.FC = () => {
  const today = new Date().toISOString().slice(0, 10);
  const [startDate, setStartDate] = useState(`${today.slice(0, 7)}-01`);
  const [endDate, setEndDate] = useState(today);
  const [requests, setRequests] = useState<StatementRequest[]>([]);
  const [preview, setPreview] = useState<PreviewRow[]>([]);
  const [fileHash, setFileHash] = useState('');
  const [defaultCategory, setDefaultCategory] = useState('General');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadRequests() {
    try { setRequests(await api.getStatementRequests()); }
    catch (err: any) { setError(err?.message || 'Could not load statement requests.'); }
  }
  useEffect(() => { void loadRequests(); }, []);

  async function handleFile(file?: File) {
    setError(null); setNotice(null); setPreview([]); setFileHash('');
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) { setError('Please choose a CSV statement file.'); return; }
    try {
      const parsed = await readStatementCsv(file);
      setFileHash(parsed.hash);
      setPreview(parsed.rows.map((row) => row.hasSourceCategory ? row : { ...row, category: defaultCategory }));
    } catch (err: any) { setError(err?.message || 'Could not read this CSV file.'); }
  }

  async function importRows() {
    if (preview.some((row) => !row.category.trim())) {
      setError('Every transaction needs a category before import.');
      return;
    }
    setBusy(true); setError(null); setNotice(null);
    try {
      const result = await api.importStatementRows(fileHash, preview.map(({ displayDate, description, ...row }) => row));
      setNotice(`${result.imported_count} transaction(s) imported; ${result.duplicates_skipped} duplicate row(s) skipped.`);
      setPreview([]); setFileHash('');
    } catch (err: any) { setError(err?.message || 'Could not import these transactions.'); }
    finally { setBusy(false); }
  }

  async function requestStatement(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(null); setNotice(null);
    try {
      await api.createStatementRequest(startDate, endDate);
      setNotice('Statement request sent to the bank manager for review.');
      await loadRequests();
    } catch (err: any) { setError(err?.message || 'Could not submit the statement request.'); }
    finally { setBusy(false); }
  }

  async function downloadStatement(requestId: number) {
    setError(null);
    try {
      const blob = await api.downloadStatement(requestId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `finshield_activity_${requestId}.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: any) { setError(err?.message || 'Could not download this statement.'); }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-indigo-50 text-indigo-700 p-3"><FileText className="w-6 h-6" /></div>
          <div><h1 className="text-2xl font-bold text-slate-900">Statements</h1><p className="mt-1 text-sm text-slate-600">Import your own transaction CSV, or request an activity statement for manager approval.</p></div>
        </div>
        <p className="mt-4 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-900">CSV rows are parsed in your browser; the original file is not saved. Imported rows are marked as customer-entered. FinShield reports are not official bank statements and do not connect to your bank.</p>
      </header>

      {(error || notice) && <div role={error ? 'alert' : 'status'} className={`rounded-xl border p-3 text-sm flex items-center gap-2 ${error ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}`}>{error ? <AlertCircle className="w-4 h-4 shrink-0" /> : null}<span>{error || notice}</span></div>}

      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2"><Upload className="w-4 h-4 text-teal-700" /> Import a bank CSV</h2>
        <p className="mt-1 text-xs text-slate-500">Supported columns: date, amount or debit/credit, and optional description, category, and type. Up to 500 rows, 5 MB.</p>
        <label className="mt-3 block max-w-sm text-sm font-medium text-slate-700">Default category for uncategorized rows
          <input maxLength={50} value={defaultCategory} onChange={(event) => {
            const value = event.target.value;
            setDefaultCategory(value);
            setPreview((current) => current.map((row) => row.hasSourceCategory ? row : { ...row, category: value }));
          }} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
        </label>
        <label className="mt-4 block text-sm font-medium text-slate-700">Choose CSV file
          <input type="file" accept=".csv,text/csv" onChange={(event) => void handleFile(event.target.files?.[0])} className="mt-1 block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-teal-50 file:px-4 file:py-2 file:font-semibold file:text-teal-800 hover:file:bg-teal-100" />
        </label>
        {preview.length > 0 && <>
          <div className="mt-4 max-h-96 overflow-auto rounded-xl border border-slate-200">
            <table className="min-w-full text-left text-xs"><thead className="sticky top-0 bg-slate-50 text-slate-500"><tr><th className="px-3 py-2">Date</th><th className="px-3 py-2">Description</th><th className="px-3 py-2">Type</th><th className="px-3 py-2">Category</th><th className="px-3 py-2 text-right">Amount (₹)</th></tr></thead>
              <tbody className="divide-y divide-slate-100">{preview.map((row) => <tr key={row.row_number}><td className="px-3 py-2 whitespace-nowrap">{row.displayDate}</td><td className="px-3 py-2">{row.description}</td><td className="px-3 py-2 capitalize">{row.type}</td><td className="px-3 py-2"><input aria-label={`Category for CSV row ${row.row_number}`} maxLength={50} value={row.category} onChange={(event) => setPreview((current) => current.map((item) => item.row_number === row.row_number ? { ...item, category: event.target.value } : item))} className="w-36 rounded border border-slate-300 px-2 py-1 focus:outline-none focus:ring-1 focus:ring-teal-500" /></td><td className="px-3 py-2 text-right">{(row.amount_paise / 100).toFixed(2)}</td></tr>)}</tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-slate-500">Review all {preview.length} rows and adjust categories as needed. Re-importing the same file skips previously imported rows.</p>
          <button onClick={() => void importRows()} disabled={busy} className="mt-3 inline-flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50">{busy ? 'Importing…' : 'Import transactions'}</button>
        </>}
      </section>

      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <h2 className="text-base font-bold text-slate-900">Request an activity statement</h2>
        <p className="mt-1 text-xs text-slate-500">A supervisor acting as the demo bank manager must approve the request before the CSV download is available.</p>
        <form onSubmit={requestStatement} className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
          <label className="text-sm font-medium text-slate-700">From<input required type="date" max={endDate} value={startDate} onChange={(e) => setStartDate(e.target.value)} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
          <label className="text-sm font-medium text-slate-700">To<input required type="date" min={startDate} max={today} value={endDate} onChange={(e) => setEndDate(e.target.value)} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
          <button disabled={busy} className="rounded-lg bg-indigo-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-800 disabled:opacity-50">Send for approval</button>
        </form>
        <div className="mt-5 space-y-2">
          {requests.length === 0 ? <p className="text-sm text-slate-500">No statement requests yet.</p> : requests.map((request) => (
            <div key={request.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-xl border border-slate-200 p-4">
              <div><p className="text-sm font-semibold text-slate-800">{request.start_date} to {request.end_date}</p><p className="text-xs text-slate-500">{request.transaction_count} completed row(s) · {new Date(request.requested_at).toLocaleString()}</p>{request.review_note && <p className="mt-1 text-xs text-slate-600">Manager note: {request.review_note}</p>}</div>
              <div className="flex items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-[11px] font-bold capitalize ${request.status === 'approved' ? 'bg-emerald-100 text-emerald-800' : request.status === 'rejected' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}`}>{request.status}</span>{request.status === 'approved' && <button onClick={() => void downloadStatement(request.id)} className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold text-white"><Download className="w-3.5 h-3.5" /> Download CSV</button>}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
