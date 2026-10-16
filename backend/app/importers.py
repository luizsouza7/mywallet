"""Conservative CSV/OFX parsing. Never run spreadsheet formulas or connect to banks."""
import csv
import hashlib
import io
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MAX_BYTES = 3 * 1024 * 1024
MAX_ROWS = 3000

def normalize(value):
    s = unicodedata.normalize("NFD", str(value or "").strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("_", " ")

def money_cents(raw):
    s = str(raw or "").strip().replace("\u00a0", "").replace(" ", "")
    s = re.sub(r"(?i)r\$", "", s)
    negative = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("-+()")
    if not s or not re.fullmatch(r"[\d.,]+", s):
        raise ValueError("Valor inválido")
    if "," in s and "." in s:
        decimal_separator = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if decimal_separator == "," else ",", "").replace(decimal_separator, ".")
    elif "," in s:
        s = s.replace(",", ".") if len(s.rsplit(",", 1)[-1]) <= 2 else s.replace(",", "")
    elif "." in s and len(s.rsplit(".", 1)[-1]) == 3:
        s = s.replace(".", "")
    try:
        cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except InvalidOperation as exc:
        raise ValueError("Valor inválido") from exc
    if cents == 0:
        raise ValueError("Valor zero")
    return -cents if negative else cents

def date_iso(raw):
    raw = str(raw or "").strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y%m%d"):
        try:
            return datetime.strptime(raw[:8] if pattern == "%Y%m%d" else raw[:10], pattern).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Data inválida")

def assign_fingerprints(rows):
    counts = defaultdict(int)
    for item in rows:
        if item.get("source_id"):
            key = "ofx|" + item["source_id"]
        else:
            base = "|".join(("csv", item["date"], normalize(item["description"]),
                             str(item["amount_cents"]), item["direction"]))
            idx = counts[base]
            counts[base] += 1
            key = base + "|" + str(idx)
        item["fingerprint"] = hashlib.sha256(key.encode()).hexdigest()
    return rows

def decode(data):
    if len(data) > MAX_BYTES:
        raise ValueError("Arquivo excede 3 MB")
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível ler o arquivo")

def parse_csv(data):
    text = decode(data)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    except csv.Error as exc:
        raise ValueError("CSV inválido") from exc
    if not reader.fieldnames:
        raise ValueError("CSV sem cabeçalho")
    columns = {normalize(k): k for k in reader.fieldnames if k}
    def val(row, *names):
        for name in names:
            if name in columns:
                return row.get(columns[name], "")
        return ""
    if not any(key in columns for key in ("data", "date", "data lancamento", "data da transacao")):
        raise ValueError("CSV sem coluna de data")
    if not any(key in columns for key in ("valor", "amount", "quantia", "credito", "debito")):
        raise ValueError("CSV sem coluna de valor")
    rows, errors = [], []
    for number, row in enumerate(reader, start=2):
        if number > MAX_ROWS + 1:
            raise ValueError("Limite de 3000 linhas excedido")
        if not row or not any(str(x or "").strip() for x in row.values()):
            continue
        try:
            date = date_iso(val(row, "data", "date", "data lancamento", "data da transacao"))
            description = str(val(row, "descricao", "description", "historico",
                                  "lancamento", "estabelecimento") or "Movimentação").strip()[:200]
            amount_str = val(row, "valor", "amount", "quantia")
            if not str(amount_str or "").strip():
                credit, debit = val(row, "credito"), val(row, "debito")
                amount = abs(money_cents(credit)) if str(credit or "").strip() else -abs(money_cents(debit))
            else:
                amount = money_cents(amount_str)
            declared = normalize(val(row, "tipo", "type", "natureza"))
            if declared in ("receita", "entrada", "credito", "income"):
                direction = "income"
            elif declared in ("despesa", "saida", "debito", "expense"):
                direction = "expense"
            else:
                direction = "income" if amount > 0 else "expense"
            rows.append({
                "date": date, "description": description, "amount_cents": abs(amount),
                "direction": direction,
                "category": str(val(row, "categoria", "category") or "Outros").strip()[:60] or "Outros",
            })
        except ValueError as exc:
            errors.append("Linha " + str(number) + ": " + str(exc))
    if not rows:
        raise ValueError("Nenhuma movimentação válida encontrada")
    return assign_fingerprints(rows), errors

def parse_ofx(data):
    text = decode(data)
    rows, errors = [], []
    for number, match in enumerate(re.finditer(r"<STMTTRN>(.*?)</STMTTRN>", text, re.I | re.S), start=1):
        if number > MAX_ROWS:
            raise ValueError("Limite de 3000 transações excedido")
        block = match.group(1)
        def tag(name):
            found = re.search(r"<" + name + r">\s*([^<\r\n]+)", block, re.I)
            return found.group(1).strip() if found else ""
        try:
            amount = money_cents(tag("TRNAMT"))
            rows.append({
                "date": date_iso(tag("DTPOSTED")[:8]),
                "description": (tag("NAME") or tag("MEMO") or "Movimentação")[:200],
                "amount_cents": abs(amount),
                "direction": "income" if amount > 0 else "expense",
                "category": "Outros",
                "source_id": tag("FITID") or None,
            })
        except ValueError as exc:
            errors.append("Transação " + str(number) + ": " + str(exc))
    if not rows:
        raise ValueError("OFX sem transações reconhecidas")
    return assign_fingerprints(rows), errors

def parse_statement(filename, data):
    name = filename.lower()
    if name.endswith(".csv"):
        return parse_csv(data)
    if name.endswith(".ofx"):
        return parse_ofx(data)
    raise ValueError("Use arquivos CSV ou OFX")
