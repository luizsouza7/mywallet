# Extratos bancários — primeiros formatos aceitos

Os arquivos escolhidos são enviados para a API MyWallet instalada pelo usuário. **Não envie senhas de banco ou informações financeiras reais para servidores de terceiros.**

## CSV

Cabeçalhos possíveis: data/date; descricao/description/historico/lancamento/estabelecimento; valor/amount/quantia; tipo (opcional); categoria (opcional). Alternativa: credito e debito como duas colunas.

Exemplo, usando ponto e vírgula entre colunas:

    data;descricao;valor;categoria
    15/10/2026;Supermercado;-185,90;Alimentação
    15/10/2026;Salário;1.200,00;Salário

Datas ISO 2026-10-15 e brasileiras 15/10/2026 são aceitas. Valores podem ter vírgula decimal. Quando tipo está ausente, valores positivos são receita e negativos despesa.

## OFX

Suporte básico aos blocos STMTTRN, com tags DTPOSTED, TRNAMT, NAME/MEMO e FITID. O identificador FITID, quando existir, é usado para detectar duplicatas na mesma conta. Alguns bancos usam variações que exigirão adaptadores específicos.

## Regras e limites
- Tamanho máximo: 3 MB por arquivo; até 3.000 lançamentos.
- Prévia obrigatória, seleção de linhas e mensagens de erro.
- Reimportação das mesmas linhas em uma conta não duplica lançamentos reconhecidos.
- Transações semelhantes registradas manualmente ainda precisam de revisão; o sistema não faz conciliação automática.
- Pagamento de fatura e transferências entre suas próprias contas precisam de fluxo próprio. Não importe cegamente a fatura como gastos correntes de outra conta.
- Conserve o arquivo original e faça backup do banco SQLite.
