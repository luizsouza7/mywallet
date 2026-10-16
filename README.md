# MyWallet 2.0

Nova versão web responsiva do MyWallet com React, TypeScript e API Python/FastAPI. A edição desktop original continua em **mywallet/**; branches master e backup permanecem intactas.

## Funcionalidades desta versão

- Cadastro, login e sessões revogáveis (PBKDF2 com salt para senhas).
- Contas financeiras, saldo inicial e movimentações de receitas/despesas.
- Dashboard mensal, indicadores e gastos por categoria.
- Importação de extratos **CSV ou OFX**, prévia, seleção de linhas, validação, histórico e detecção de duplicatas.
- Design responsivo e manifesto PWA para adicionar o site à tela inicial do celular.
- Testes Python e build TypeScript via GitHub Actions.

## Execução local

Requer Python 3.12+ e Node.js 22+.

**Terminal 1:**

    cd backend
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    python -m pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

**Terminal 2:**

    cd frontend
    npm install
    npm run dev

Acesse http://localhost:5173 e crie sua conta. O frontend redireciona /api para localhost:8000 durante o desenvolvimento.

Verificações:

    cd backend
    python -m pytest -q

    cd ../frontend
    npm run build

Os dados ficam em backend/data/mywallet.sqlite3 por padrão. Este arquivo está no .gitignore.

## Importação

Selecione a conta, envie CSV/OFX (máximo 3 MB), confira a prévia e confirme as linhas escolhidas. CSV reconhece data/date, descricao/description/historico, valor/amount, ou colunas credito e debito. Arquivos podem variar conforme o banco; reveja tudo antes de importar. Para CSV com vírgulas decimais, prefira separação por ponto e vírgula. Arquivos importados de novo na mesma conta são detectados por impressão digital por lançamento. Uma transação criada manualmente ainda pode coincidir com a importação: confira a prévia.

**Importante:** não importe faturas de cartão de crédito como extrato da conta corrente. Cartões, pagamentos de fatura e transferências ainda terão tratamento específico para evitar dupla contagem.

## Segurança e limitações

**MVP para desenvolvimento e testes, não auditado para produção.** O SQLite não é criptografado em repouso. Proteja o servidor, faça backups e use HTTPS quando hospedar. O token permanece no sessionStorage do navegador até a aba/sessão ser encerrada. Antes de permitir uso público ou dados financeiros reais, implemente proteção anti-brute-force, revisão de autenticação, proteção de infraestrutura e monitoramento. Nenhum acesso direto a bancos é realizado. A importação envia o arquivo escolhido à sua API.

O manifesto da web permite uma experiência de instalação em navegadores compatíveis, mas **não existe modo offline completo nem sincronização entre servidores**. A sincronização PC/celular exige usar uma única instalação de API com banco persistente e acesso seguro. A lista de transações mostra 500 itens recentes por enquanto. Não há cartão de crédito, parcelamentos ou Open Finance nesta primeira entrega.

Os dados do SQLite da edição antiga **não são migrados automaticamente**; faça um backup antes de qualquer migração.

Veja docs/ROADMAP.md para próximos ciclos.

- Desenvolvimento: https://github.com/luizsouza7/mywallet/tree/develop/mywallet-v2
- Backup: https://github.com/luizsouza7/mywallet/tree/backup/pre-v2-2026-10-15
