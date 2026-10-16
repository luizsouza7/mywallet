import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowDownLeft, ArrowRight, ArrowUpRight, BarChart3, Check, CheckCircle2,
  ChevronRight, CircleAlert, FileUp, Landmark, LogOut,
  Menu, Pencil, Plus, ReceiptText, RefreshCw, ShieldCheck, Trash2,
  Wallet, X
} from 'lucide-react';
import {
  Account, api, centsFromInput, ImportRecord, money, Preview, sessionToken,
  setToken, shortDate, Summary, Transaction, TransactionInput, User
} from './api';

type View = 'overview' | 'transactions' | 'imports' | 'accounts';
type Mode = 'login' | 'register';
const menu: { id: View; title: string; Icon: typeof Wallet }[] = [
  { id: 'overview', title: 'Visão geral', Icon: BarChart3 },
  { id: 'transactions', title: 'Movimentações', Icon: ReceiptText },
  { id: 'imports', title: 'Importar extrato', Icon: FileUp },
  { id: 'accounts', title: 'Minhas contas', Icon: Landmark },
];
const initialSummary: Summary = { balance_cents: 0, income_cents: 0, expense_cents: 0, entries: 0, categories: [] };
const today = () => new Date().toLocaleDateString('en-CA');
const thisMonth = () => today().slice(0, 7);

function Auth({ onLogin }: { onLogin: (token: string, user: User) => void }) {
  const [mode, setMode] = useState<Mode>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (mode === 'register') {
        await api<{ message: string }>('/auth/register', {
          method: 'POST', body: JSON.stringify({ name, email, password })
        });
      }
      const response = await api<{ token: string; user: User }>('/auth/login', {
        method: 'POST', body: JSON.stringify({ email, password })
      });
      onLogin(response.token, response.user);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  return <div className="auth-shell">
    <div className="auth-intro">
      <div className="brand-icon"><Wallet size={28} strokeWidth={2.2} /></div>
      <div className="overline light">SEU DINHEIRO, MAIS CLARO</div>
      <h1>Tenha controle.<br /><span>Faça acontecer.</span></h1>
      <p>Organize suas contas, acompanhe seus gastos e importe seu extrato em poucos passos.</p>
      <div className="auth-accent"><ShieldCheck size={19} /> Dados locais na sua própria instalação</div>
    </div>
    <div className="auth-panel">
      <div className="auth-card">
        <span className="eyebrow">MYWALLET 2.0</span>
        <h2>{mode === 'login' ? 'Bem-vindo de volta!' : 'Comece sua jornada'}</h2>
        <p className="muted">{mode === 'login' ? 'Entre para acessar suas finanças.' : 'Crie sua conta pessoal e organize tudo.'}</p>
        <form onSubmit={submit} className="form-stack">
          {mode === 'register' && <label>Seu nome<input required minLength={2} maxLength={100} value={name} onChange={e => setName(e.target.value)} placeholder="Como podemos chamar você?" /></label>}
          <label>E-mail<input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="voce@email.com" autoComplete="email" /></label>
          <label>Senha<input required type="password" minLength={mode === 'register' ? 10 : undefined} value={password} onChange={e => setPassword(e.target.value)} placeholder={mode === 'register' ? 'Mínimo de 10 caracteres' : 'Sua senha'} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} /></label>
          {error && <div className="notice error"><CircleAlert size={17} />{error}</div>}
          <button className="btn primary wide" disabled={busy} type="submit">{busy ? 'Processando...' : mode === 'login' ? 'Entrar na minha conta' : 'Criar conta e entrar'}<ArrowRight size={17} /></button>
        </form>
        <div className="auth-switch">{mode === 'login' ? 'Ainda não tem conta?' : 'Já tem uma conta?'}{' '}
          <button type="button" className="text-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>
            {mode === 'login' ? 'Cadastre-se' : 'Fazer login'}
          </button>
        </div>
      </div>
    </div>
  </div>;
}

function Metric({ title, value, hint, Icon, tone }: {
  title: string; value: string; hint: string; Icon: typeof Wallet; tone: 'blue' | 'green' | 'red';
}) {
  return <article className={'metric metric-' + tone}>
    <div className="metric-header"><span>{title}</span><span className="metric-icon"><Icon size={20} /></span></div>
    <div className="metric-value">{value}</div>
    <div className="metric-hint">{hint}</div>
  </article>;
}

export default function App() {
  const [token, setCurrentToken] = useState<string | null>(sessionToken);
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<View>('overview');
  const [drawer, setDrawer] = useState(false);
  const [month, setMonth] = useState(thisMonth);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<Summary>(initialSummary);
  const [imports, setImports] = useState<ImportRecord[]>([]);
  const [loading, setLoading] = useState(Boolean(token));
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [formAccount, setFormAccount] = useState(0);
  const [formDescription, setFormDescription] = useState('');
  const [formValue, setFormValue] = useState('');
  const [formDate, setFormDate] = useState(today);
  const [formDirection, setFormDirection] = useState<'income' | 'expense'>('expense');
  const [formCategory, setFormCategory] = useState('Outros');
  const [saving, setSaving] = useState(false);
  const [accountName, setAccountName] = useState('');
  const [accountKind, setAccountKind] = useState<'checking' | 'savings' | 'cash'>('checking');
  const [accountOpening, setAccountOpening] = useState('0');
  const [file, setFile] = useState<File | null>(null);
  const [importAccount, setImportAccount] = useState(0);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [importBusy, setImportBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!sessionToken()) return;
    try {
      const [a, t, s, i] = await Promise.all([
        api<Account[]>('/accounts'), api<Transaction[]>('/transactions?limit=500'),
        api<Summary>('/dashboard?month=' + month), api<ImportRecord[]>('/imports')
      ]);
      setAccounts(a); setTransactions(t); setSummary(s); setImports(i);
      setFormAccount(current => current || a[0]?.id || 0);
      setImportAccount(current => current || a[0]?.id || 0);
    } catch (e) { setError((e as Error).message); }
  }, [month]);

  useEffect(() => {
    function unauthorized() { setCurrentToken(null); setUser(null); }
    window.addEventListener('mywallet-unauthorized', unauthorized);
    return () => window.removeEventListener('mywallet-unauthorized', unauthorized);
  }, []);

  useEffect(() => {
    if (!token) { setLoading(false); return; }
    let alive = true;
    setLoading(true);
    api<User>('/auth/me').then(u => { if (alive) setUser(u); })
      .then(() => refresh())
      .catch(e => { if (alive) setError((e as Error).message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [token, refresh]);

  const monthTransactions = useMemo(
    () => transactions.filter(t => t.booked_on.startsWith(month)), [transactions, month]
  );
  const maxCategory = Math.max(1, ...summary.categories.map(c => c.amount_cents));

  function signed(t: Transaction) { return (t.direction === 'income' ? '+' : '-') + money(t.amount_cents); }
  function notify(text: string) { setError(''); setMessage(text); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  function fail(e: unknown) { setMessage(''); setError((e as Error).message || 'Algo deu errado.'); }

  function openTransaction(item?: Transaction) {
    setEditing(item || null);
    setFormAccount(item?.account_id || accounts[0]?.id || 0);
    setFormDescription(item?.description || '');
    setFormValue(item ? (item.amount_cents / 100).toFixed(2).replace('.', ',') : '');
    setFormDate(item?.booked_on || today());
    setFormDirection(item?.direction || 'expense');
    setFormCategory(item?.category || 'Outros');
    setFormOpen(true);
    setDrawer(false);
  }

  async function saveTransaction(e: FormEvent) {
    e.preventDefault(); setSaving(true); setError('');
    try {
      const body: TransactionInput = {
        account_id: Number(formAccount), description: formDescription.trim(),
        amount_cents: centsFromInput(formValue), direction: formDirection,
        booked_on: formDate, category: formCategory.trim() || 'Outros'
      };
      await api(editing ? '/transactions/' + editing.id : '/transactions', {
        method: editing ? 'PUT' : 'POST', body: JSON.stringify(body)
      });
      setFormOpen(false);
      await refresh();
      notify(editing ? 'Movimentação atualizada!' : 'Movimentação registrada!');
    } catch (err) { fail(err); }
    finally { setSaving(false); }
  }

  async function removeTransaction(t: Transaction) {
    if (!window.confirm('Excluir "' + t.description + '"? Essa ação não pode ser desfeita.')) return;
    try {
      await api('/transactions/' + t.id, { method: 'DELETE' });
      await refresh(); notify('Movimentação excluída.');
    } catch (e) { fail(e); }
  }

  async function addAccount(e: FormEvent) {
    e.preventDefault(); setSaving(true);
    try {
      const cents = accountOpening.trim() === '0' || accountOpening.trim() === '' ? 0
        : (accountOpening.trim().startsWith('-') ? -1 : 1) * centsFromInput(accountOpening.trim().replace(/^[+-]/, ''));
      await api('/accounts', {
        method: 'POST', body: JSON.stringify({
          name: accountName.trim(), kind: accountKind, opening_balance_cents: cents
        })
      });
      setAccountName(''); setAccountOpening('0');
      await refresh(); notify('Conta criada!');
    } catch (err) { fail(err); }
    finally { setSaving(false); }
  }

  function importFormData(): FormData {
    if (!file) throw new Error('Selecione um arquivo CSV ou OFX.');
    const data = new FormData();
    data.append('account_id', String(importAccount));
    data.append('file', file);
    return data;
  }

  async function previewImport() {
    setImportBusy(true); setPreview(null); setSelected([]); setError('');
    try {
      const p = await api<Preview>('/imports/preview', { method: 'POST', body: importFormData() });
      setPreview(p);
      setSelected(p.rows.flatMap((r, i) => r.duplicate ? [] : [i]));
    } catch (err) { fail(err); }
    finally { setImportBusy(false); }
  }

  async function commitImport() {
    if (!selected.length) return;
    setImportBusy(true);
    try {
      const body = importFormData();
      body.append('selected_indices', JSON.stringify(selected));
      const result = await api<{ imported: number; duplicates: number; invalid: number }>('/imports/commit', { method: 'POST', body });
      setPreview(null); setFile(null); setSelected([]);
      const picker = document.getElementById('statement-file') as HTMLInputElement | null;
      if (picker) picker.value = '';
      await refresh();
      notify(result.imported + ' movimentações importadas. ' + result.duplicates + ' duplicadas ignoradas.');
    } catch (e) { fail(e); }
    finally { setImportBusy(false); }
  }

  async function logout() {
    try { await api('/auth/logout', { method: 'POST' }); } catch { /* local session still expires */ }
    setToken(null); setCurrentToken(null); setUser(null);
    setAccounts([]); setTransactions([]); setPreview(null);
  }

  if (!token) return <Auth onLogin={(newToken, newUser) => {
    setToken(newToken); setCurrentToken(newToken); setUser(newUser); setError('');
  }} />;

  if (loading && !user) return <div className="splash"><div className="brand-icon"><Wallet /></div><p>Carregando MyWallet...</p></div>;

  return <div className="app">
    <aside className={'sidebar ' + (drawer ? 'sidebar-open' : '')}>
      <div className="sidebar-brand">
        <span className="small-logo"><Wallet size={22} /></span>
        <div><strong>MyWallet<span className="brand-dot">.</span></strong><small>Suas finanças</small></div>
        <button className="icon-button side-close" onClick={() => setDrawer(false)} aria-label="Fechar menu"><X size={18} /></button>
      </div>
      <div className="menu-label">MENU PRINCIPAL</div>
      <nav className="nav-list">
        {menu.map(({ id, title, Icon }) => <button key={id} className={'nav-item ' + (view === id ? 'active' : '')}
          onClick={() => { setView(id); setDrawer(false); setMessage(''); }}>
          <Icon size={19} />{title}{view === id && <span className="active-marker" />}
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="privacy"><ShieldCheck size={17} /> Seus dados sob controle</div>
        <div className="sidebar-profile">
          <div className="avatar">{(user?.name || '?').trim().slice(0, 1).toUpperCase()}</div>
          <div className="profile-name"><strong>{user?.name || 'Usuário'}</strong><span>{user?.email}</span></div>
          <button className="icon-button" aria-label="Sair" title="Sair" onClick={logout}><LogOut size={18} /></button>
        </div>
      </div>
    </aside>
    {drawer && <button className="sidebar-scrim" aria-label="Fechar menu" onClick={() => setDrawer(false)} />}
    <main className="main">
      <header className="topbar">
        <div className="topbar-left">
          <button className="icon-button menu-trigger" aria-label="Abrir menu" onClick={() => setDrawer(true)}><Menu size={23} /></button>
          <span className="topbar-breadcrumb">Minha carteira <ChevronRight size={14} /> <strong>{menu.find(m => m.id === view)?.title}</strong></span>
        </div>
        <div className="topbar-right">
          <span className="topbar-desktop muted">Olá, {user?.name?.split(' ')[0]} 👋</span>
          <button className="icon-button" title="Atualizar" aria-label="Atualizar" onClick={() => void refresh()}><RefreshCw size={18} /></button>
          <button className="btn primary top-new" onClick={() => openTransaction()}><Plus size={17} /> Nova movimentação</button>
        </div>
      </header>
      <div className="content">
        {message && <div className="notice success" role="status"><CheckCircle2 size={18} />{message}<button onClick={() => setMessage('')} aria-label="Fechar aviso"><X size={16} /></button></div>}
        {error && <div className="notice error" role="alert"><CircleAlert size={18} />{error}<button onClick={() => setError('')} aria-label="Fechar erro"><X size={16} /></button></div>}

        {view === 'overview' && <>
          <div className="page-heading"><div><div className="eyebrow">SEU RESUMO FINANCEIRO</div><h1>Visão geral</h1><p>Seu dinheiro, de um jeito mais simples.</p></div>
            <label className="month-picker"><span>Período</span><input aria-label="Mês de referência" type="month" value={month} onChange={e => setMonth(e.target.value)} /></label>
          </div>
          <div className="metrics">
            <Metric title="Saldo consolidado" value={money(summary.balance_cents)} hint="Saldo atual das suas contas" Icon={Wallet} tone="blue" />
            <Metric title="Receitas no período" value={money(summary.income_cents)} hint="Total de entradas" Icon={ArrowDownLeft} tone="green" />
            <Metric title="Despesas no período" value={money(summary.expense_cents)} hint="Total de saídas" Icon={ArrowUpRight} tone="red" />
          </div>
          <div className="main-grid">
            <section className="panel spending-panel">
              <div className="panel-head"><div><h2>Gastos por categoria</h2><p>Entenda para onde seu dinheiro está indo</p></div><span className="pill">{summary.entries} lançamentos</span></div>
              {summary.categories.length ? <div className="category-list">{summary.categories.map((cat, i) =>
                <div className="category-item" key={cat.category}>
                  <div className="category-row"><span><i className={'cat-dot color-' + (i % 5)} />{cat.category}</span><strong>{money(cat.amount_cents)}</strong></div>
                  <div className="bar-track"><div className={'bar-fill color-' + (i % 5)} style={{ width: (cat.amount_cents / maxCategory * 100) + '%' }} /></div>
                </div>
              )}</div> : <div className="empty"><BarChart3 size={34} /><strong>Seus gráficos começam aqui</strong><span>Registre uma despesa ou importe um extrato.</span></div>}
            </section>
            <section className="panel">
              <div className="panel-head"><div><h2>Suas contas</h2><p>Saldo atualizado de cada conta</p></div><button className="text-button" onClick={() => setView('accounts')}>Ver todas <ArrowRight size={15} /></button></div>
              <div className="account-list">{accounts.map(a => <div className="account-line" key={a.id}><div className="account-symbol"><Landmark size={19} /></div><div className="account-text"><strong>{a.name}</strong><span>{a.kind === 'checking' ? 'Conta corrente' : a.kind === 'savings' ? 'Poupança' : 'Dinheiro'}</span></div><strong>{money(a.balance_cents)}</strong></div>)}</div>
              <button className="link-row" onClick={() => setView('imports')}><FileUp size={18} /><span>Importar extrato bancário</span><ChevronRight size={18} /></button>
            </section>
          </div>
          <section className="panel transactions-panel">
            <div className="panel-head"><div><h2>Movimentações recentes</h2><p>Últimas entradas e saídas do período</p></div>
              <button className="text-button" onClick={() => setView('transactions')}>Ver todas <ArrowRight size={15} /></button></div>
            <TransactionList items={monthTransactions.slice(0, 6)} signed={signed} onEdit={openTransaction} onDelete={removeTransaction} compact />
          </section>
        </>}

        {view === 'transactions' && <>
          <div className="page-heading"><div><div className="eyebrow">CONTROLE DO DIA A DIA</div><h1>Movimentações</h1><p>Acompanhe e organize suas entradas e despesas.</p></div><button className="btn primary" onClick={() => openTransaction()}><Plus size={17} /> Adicionar</button></div>
          <section className="panel transactions-panel">
            <div className="panel-head"><div><h2>Histórico completo</h2><p>Exibindo até 500 movimentações mais recentes</p></div><span className="pill">{transactions.length} itens</span></div>
            <TransactionList items={transactions} signed={signed} onEdit={openTransaction} onDelete={removeTransaction} />
          </section>
        </>}

        {view === 'accounts' && <>
          <div className="page-heading"><div><div className="eyebrow">ORGANIZE SEU DINHEIRO</div><h1>Minhas contas</h1><p>Separe seu saldo por conta, poupança ou dinheiro.</p></div></div>
          <div className="accounts-grid">{accounts.map(a => <article key={a.id} className="account-card"><div className="account-card-top"><span className="account-symbol"><Landmark size={21} /></span><span className="pill">{a.kind === 'checking' ? 'Corrente' : a.kind === 'savings' ? 'Poupança' : 'Dinheiro'}</span></div><h3>{a.name}</h3><span className="muted">Saldo disponível</span><strong className="account-balance">{money(a.balance_cents)}</strong></article>)}</div>
          <section className="panel create-account"><div className="panel-head"><div><h2>Adicionar conta</h2><p>Cadastre outras contas e acompanhe seus saldos.</p></div></div>
            <form className="account-form" onSubmit={addAccount}>
              <label>Nome da conta<input required maxLength={70} value={accountName} onChange={e => setAccountName(e.target.value)} placeholder="Ex.: Nubank" /></label>
              <label>Tipo<select value={accountKind} onChange={e => setAccountKind(e.target.value as typeof accountKind)}><option value="checking">Conta corrente</option><option value="savings">Poupança</option><option value="cash">Dinheiro</option></select></label>
              <label>Saldo inicial (R$)<input value={accountOpening} onChange={e => setAccountOpening(e.target.value)} placeholder="0,00" inputMode="decimal" /></label>
              <button className="btn primary" disabled={saving} type="submit"><Plus size={17} /> Adicionar conta</button>
            </form>
            <div className="inline-note">O saldo inicial representa o dinheiro já existente antes de registrar lançamentos.</div>
          </section>
        </>}

        {view === 'imports' && <>
          <div className="page-heading"><div><div className="eyebrow">MENOS DIGITAÇÃO, MAIS CONTROLE</div><h1>Importar extrato</h1><p>Traga seus lançamentos do banco com segurança e revisão.</p></div></div>
          <div className="import-layout">
            <section className="panel import-panel">
              <div className="panel-head"><div><h2>Adicionar extrato bancário</h2><p>Formatos CSV e OFX, até 3 MB.</p></div><FileUp className="panel-decoration" size={24} /></div>
              <div className="import-form">
                <label>Importar para a conta<select value={importAccount} onChange={e => { setImportAccount(Number(e.target.value)); setPreview(null); }} disabled={importBusy}>{accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
                <label className="upload-area" htmlFor="statement-file"><FileUp size={30} /><strong>{file ? file.name : 'Escolher arquivo do banco'}</strong><span>Toque para selecionar CSV ou OFX</span></label>
                <input id="statement-file" type="file" accept=".csv,.ofx,text/csv" className="visually-hidden" onChange={e => { setFile(e.target.files?.[0] || null); setPreview(null); }} />
                <button className="btn primary wide" onClick={previewImport} disabled={!file || !importAccount || importBusy}>{importBusy ? 'Lendo extrato...' : 'Analisar arquivo'}<ArrowRight size={17} /></button>
              </div>
            </section>
            <aside className="panel import-guide">
              <h2><ShieldCheck size={20} /> Como funciona</h2>
              <div className="step"><span>01</span><div><strong>Exporte no seu banco</strong><p>Baixe seu extrato CSV ou OFX pelo aplicativo ou site do banco.</p></div></div>
              <div className="step"><span>02</span><div><strong>Confira a prévia</strong><p>Revise valores, datas e possíveis duplicidades.</p></div></div>
              <div className="step"><span>03</span><div><strong>Confirme a importação</strong><p>Somente as movimentações selecionadas serão adicionadas.</p></div></div>
              <div className="inline-note"><CircleAlert size={17} /> Não envie senhas bancárias. Os arquivos são processados pela sua API MyWallet.</div>
            </aside>
          </div>
          {preview && <section className="panel preview-panel">
            <div className="panel-head"><div><h2>Prévia do extrato</h2><p>{preview.rows.length} reconhecidas · {preview.rows.filter(r => r.duplicate).length} já importadas</p></div><span className="pill">{selected.length} selecionadas</span></div>
            {preview.errors.length > 0 && <div className="notice warning"><CircleAlert size={17} />{preview.errors.length} linhas inválidas: {preview.errors.slice(0, 3).join('; ')}</div>}
            <div className="preview-actions"><button className="btn ghost" onClick={() => setSelected(preview.rows.flatMap((r, i) => r.duplicate ? [] : [i]))}>Selecionar novas</button><button className="btn ghost" onClick={() => setSelected([])}>Limpar seleção</button></div>
            <div className="preview-table">{preview.rows.map((r, i) =>
              <label key={r.fingerprint + i} className={'preview-row ' + (r.duplicate ? 'duplicate' : '')}>
                <input type="checkbox" checked={selected.includes(i)} disabled={r.duplicate}
                  onChange={e => setSelected(old => e.target.checked ? [...old, i] : old.filter(x => x !== i))} />
                <span className="preview-desc"><strong>{r.description}</strong><small>{shortDate(r.date)} · {r.category}</small></span>
                <span className={'amount ' + r.direction}>{r.direction === 'income' ? '+' : '-'}{money(r.amount_cents)}</span>
                {r.duplicate && <span className="duplicate-pill">Duplicada</span>}
              </label>)}</div>
            <div className="preview-footer"><span>Confira as movimentações antes de confirmar.</span><button className="btn primary" onClick={commitImport} disabled={!selected.length || importBusy}><Check size={17} />{importBusy ? 'Importando...' : 'Importar ' + selected.length + ' itens'}</button></div>
          </section>}
          <section className="panel import-history"><div className="panel-head"><div><h2>Importações anteriores</h2><p>Histórico dos arquivos processados.</p></div></div>
            {imports.length ? imports.map(item => <div className="history-row" key={item.id}><span className="account-symbol"><FileUp size={19} /></span><div><strong>{item.filename}</strong><span>{item.account_name} · {item.created_at.slice(0, 10)} · {item.inserted_count} lançamentos</span></div><CheckCircle2 size={18} className="success-icon" /></div>) : <div className="empty compact-empty"><FileUp size={30} /><span>Nenhuma importação realizada.</span></div>}
          </section>
        </>}
        <footer className="footer"><span>MyWallet 2.0 · Primeira versão web</span><span>Construído para você ter clareza sobre o seu dinheiro.</span></footer>
      </div>
    </main>
    <nav className="bottom-nav" aria-label="Navegação principal">
      {menu.map(({ id, title, Icon }) => <button key={id} aria-label={title} className={view === id ? 'active' : ''} onClick={() => { setView(id); setMessage(''); window.scrollTo(0, 0); }}><Icon size={21} /><span>{id === 'overview' ? 'Início' : id === 'transactions' ? 'Extrato' : id === 'imports' ? 'Importar' : 'Contas'}</span></button>)}
    </nav>
    <button className="mobile-fab" title="Nova movimentação" aria-label="Nova movimentação" onClick={() => openTransaction()}><Plus size={26} /></button>

    {formOpen && <div className="modal-overlay" onMouseDown={e => { if (e.target === e.currentTarget) setFormOpen(false); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={editing ? 'Editar movimentação' : 'Nova movimentação'}>
        <div className="modal-header"><div><span className="eyebrow">CONTROLE FINANCEIRO</span><h2>{editing ? 'Editar movimentação' : 'Nova movimentação'}</h2></div><button className="icon-button" aria-label="Fechar" onClick={() => setFormOpen(false)}><X size={22} /></button></div>
        <form className="form-stack" onSubmit={saveTransaction}>
          <div className="direction-tabs"><button type="button" className={formDirection === 'expense' ? 'selected expense' : ''} onClick={() => setFormDirection('expense')}><ArrowUpRight size={17} /> Despesa</button><button type="button" className={formDirection === 'income' ? 'selected income' : ''} onClick={() => setFormDirection('income')}><ArrowDownLeft size={17} /> Receita</button></div>
          <label>Descrição<input required maxLength={200} value={formDescription} onChange={e => setFormDescription(e.target.value)} placeholder="Ex.: Supermercado" autoFocus /></label>
          <div className="form-row"><label>Valor (R$)<input required inputMode="decimal" value={formValue} onChange={e => setFormValue(e.target.value)} placeholder="0,00" /></label><label>Data<input required type="date" value={formDate} onChange={e => setFormDate(e.target.value)} /></label></div>
          <label>Conta<select value={formAccount} onChange={e => setFormAccount(Number(e.target.value))} required>{accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
          <label>Categoria<input required maxLength={60} value={formCategory} onChange={e => setFormCategory(e.target.value)} list="categories" placeholder="Ex.: Alimentação" />
            <datalist id="categories">{['Alimentação','Moradia','Transporte','Saúde','Lazer','Educação','Assinaturas','Compras','Salário','Transferência','Outros'].map(c => <option key={c} value={c} />)}</datalist></label>
          <button type="submit" disabled={saving} className="btn primary wide">{saving ? 'Salvando...' : editing ? 'Salvar alterações' : 'Registrar movimentação'}<Check size={18} /></button>
        </form>
      </div>
    </div>}
  </div>;
}

function TransactionList({ items, signed, onEdit, onDelete, compact = false }: {
  items: Transaction[];
  signed: (t: Transaction) => string;
  onEdit: (t: Transaction) => void;
  onDelete: (t: Transaction) => void;
  compact?: boolean;
}) {
  if (!items.length) return <div className="empty compact-empty"><ReceiptText size={32} /><strong>Nenhum lançamento por enquanto</strong><span>Comece adicionando uma movimentação.</span></div>;
  return <div className="transaction-list">{items.map(t => <div className="transaction-line" key={t.id}>
    <div className={'transaction-symbol ' + t.direction}>{t.direction === 'income' ? <ArrowDownLeft size={20} /> : <ArrowUpRight size={20} />}</div>
    <div className="transaction-details"><strong>{t.description}</strong><span>{t.category} · {t.account_name} · {shortDate(t.booked_on)}</span></div>
    <span className={'amount ' + t.direction}>{signed(t)}</span>
    {!compact && <div className="line-actions"><button className="icon-button" onClick={() => onEdit(t)} aria-label={'Editar ' + t.description} title="Editar"><Pencil size={17} /></button><button className="icon-button danger" onClick={() => onDelete(t)} aria-label={'Excluir ' + t.description} title="Excluir"><Trash2 size={17} /></button></div>}
  </div>)}</div>;
}
