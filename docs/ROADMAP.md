# MyWallet 2.0 — Roadmap

## Primeira entrega no código
- [x] API FastAPI + SQLite com valores em centavos
- [x] Autenticação com senhas PBKDF2 e sessões opacas
- [x] Contas e movimentações, validação de proprietário
- [x] Resumo mensal e distribuição por categoria
- [x] Interface React responsiva desktop/mobile
- [x] Importador CSV/OFX, prévia, duplicatas e histórico
- [x] Testes automatizados no GitHub Actions
- [x] Manifest para tela inicial (sem cache offline)

## Uso pessoal confiável
- [ ] Testar em iPhone real, acessibilidade e interações
- [x] Migrador opt-in de lançamentos desktop, com simulação e prevenção de duplicatas
- [ ] Teste de migração com banco real após backups e conferência manual
- [ ] Transferências vinculadas entre contas sem dupla contagem
- [ ] Busca/filtros/paginação na interface e desfazer importação
- [ ] Adaptadores CSV/OFX por banco, conciliação com entradas manuais
- [ ] Backup/restauração e exportação
- [ ] Rate limiting, revisão de autenticação e testes de segurança

## Cartões e automação
- [ ] Cartões, limites, faturas, fechamento e vencimento
- [ ] Parcelamentos e recorrências
- [ ] Pagamento de fatura contabilizado sem dupla despesa
- [ ] Regras configuráveis de categoria e orçamento mensal

## Hospedagem e mobile
- [ ] PostgreSQL e deploy privado com banco persistente
- [ ] HTTPS, backups protegidos e monitoramento
- [ ] Offline real, service worker e sincronização/conflictos
- [ ] PWA instalada e testada no celular
- [ ] Open Finance apenas se fizer sentido e com provedor autorizado

Não publicar com dados financeiros reais sem revisão de segurança.
