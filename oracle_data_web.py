#!/usr/bin/env python3
"""
oracle_data_web.py

Interface local para comparar DADOS (nao estrutura) entre a base de
ORIGEM e a de DESTINO, e gerar o script de INSERT/UPDATE que deixa o
destino igual a origem.

Complementa o oracle_diff.py: aquele cuida de estrutura (tabelas,
colunas, indices, constraints, views, PL/SQL); este cuida do conteudo
de tabelas de dominio/parametrizacao.

Uso:
    python3 oracle_data_web.py --config config.ini [--porta 8765]

Abre em http://127.0.0.1:8765 - o servidor so escuta em localhost e
nao exige dependencia alem do 'oracledb' que o oracle_diff.py ja usa.
Encerre com Ctrl+C.

ESCOPO: pensado para tabela de dominio (dezenas a alguns milhares de
linhas). Existe um teto de linhas (limite_linhas em [opcoes], padrao
50000) - acima disso a tabela e recusada, porque a ferramenta certa
passa a ser Data Pump ou DBMS_COMPARISON.

O script gerado NUNCA contem DELETE. Linha que existe so no destino e
apenas reportada, para decisao humana.
"""

import argparse
import configparser
import datetime
import decimal
import json
import os
import sys
import threading
import unicodedata
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

try:
    import oracledb
except ImportError:
    print("Falta o pacote 'oracledb'. Rode: pip install -r requirements.txt",
          file=sys.stderr)
    sys.exit(1)


# ----------------------------------------------------------------------
# Conexao e metadados
# ----------------------------------------------------------------------

CFG = None
SAIDA = 'dados'
LIMITE_LINHAS = 50000


def conectar(secao):
    c = CFG[secao]
    return oracledb.connect(user=c['user'], password=c['password'], dsn=c['dsn'])


def rotulo(secao):
    return CFG[secao].get('label', secao)


def prefixo():
    return 'DBA' if CFG['opcoes'].getboolean('usar_dba_views', fallback=True) else 'ALL'


def consultar(conn, sql, binds=None):
    cur = conn.cursor()
    cur.execute(sql, binds or {})
    cols = [d[0] for d in cur.description]
    linhas = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return linhas


def listar_tabelas(conn, schema, filtro):
    """Tabelas do schema com a estimativa de linhas da estatistica
    (NUM_ROWS) - de graca, ao contrario de COUNT(*). Pode estar
    desatualizada; serve so para o usuario dimensionar a escolha."""
    binds = {'o': schema}
    where_like = ''
    if filtro:
        where_like = " AND t.table_name LIKE :f"
        binds['f'] = filtro.upper()
    return consultar(conn, f"""
        SELECT t.table_name, t.num_rows, t.last_analyzed,
               (SELECT COUNT(*) FROM {prefixo()}_tab_columns c
                 WHERE c.owner = t.owner AND c.table_name = t.table_name) AS n_colunas
        FROM   {prefixo()}_tables t
        WHERE  t.owner = :o {where_like}
        ORDER  BY t.table_name
    """, binds)


def colunas_da_tabela(conn, owner, table):
    return consultar(conn, f"""
        SELECT column_name, column_id, data_type, data_length, data_precision,
               data_scale, nullable, char_length, char_used
        FROM   {prefixo()}_tab_columns
        WHERE  owner = :o AND table_name = :t
        ORDER  BY column_id
    """, {'o': owner, 't': table})


def chaves_da_tabela(conn, owner, table):
    """Devolve PK e UKs com suas colunas, para sugerir a chave de
    comparacao. PK de uma coluna NUMBER alimentada por sequence e
    inutil aqui: o mesmo registro tem ID diferente em cada ambiente."""
    cons = consultar(conn, f"""
        SELECT c.constraint_name, c.constraint_type, cc.column_name, cc.position
        FROM   {prefixo()}_constraints c
        JOIN   {prefixo()}_cons_columns cc
               ON cc.owner = c.owner AND cc.constraint_name = c.constraint_name
        WHERE  c.owner = :o AND c.table_name = :t
        AND    c.constraint_type IN ('P', 'U')
        ORDER  BY c.constraint_type, c.constraint_name, cc.position
    """, {'o': owner, 't': table})
    agrupado = {}
    for r in cons:
        item = agrupado.setdefault(r['CONSTRAINT_NAME'],
                                   {'nome': r['CONSTRAINT_NAME'],
                                    'tipo': r['CONSTRAINT_TYPE'],
                                    'colunas': []})
        item['colunas'].append(r['COLUMN_NAME'])
    return list(agrupado.values())


PADROES_AUDITORIA = ('DT_ATUALIZACAO', 'DT_INCLUSAO', 'DT_ALTERACAO', 'DT_CADASTRO',
                     'NM_USUARIO', 'CD_USUARIO_ATUALIZACAO', 'ID_USUARIO_ATUALIZACAO',
                     'DT_ULTIMA', 'TS_ATUALIZACAO')


def sugerir(colunas, chaves):
    """Sugere chave de comparacao e colunas a ignorar."""
    tipos = {c['COLUMN_NAME']: c['DATA_TYPE'] for c in colunas}
    pk = next((k for k in chaves if k['tipo'] == 'P'), None)
    uks = [k for k in chaves if k['tipo'] == 'U']

    aviso = None
    chave = None
    if pk:
        so_id = (len(pk['colunas']) == 1 and tipos.get(pk['colunas'][0]) == 'NUMBER')
        if so_id and uks:
            chave = uks[0]['colunas']
            aviso = (f"A PK {pk['nome']} e uma unica coluna NUMBER - provavelmente "
                     f"alimentada por sequence, com valor diferente em cada ambiente. "
                     f"Sugerido no lugar: {uks[0]['nome']} ({', '.join(uks[0]['colunas'])}).")
        elif so_id:
            chave = pk['colunas']
            aviso = (f"A PK {pk['nome']} e uma unica coluna NUMBER e a tabela nao tem "
                     f"chave unica de negocio. Se esse ID vier de sequence, a comparacao "
                     f"vai casar registros errados - escolha colunas de negocio na mao.")
        else:
            chave = pk['colunas']
    elif uks:
        chave = uks[0]['colunas']
    else:
        aviso = ("A tabela nao tem PK nem chave unica. Escolha manualmente as colunas "
                 "que identificam a linha - sem isso nao ha comparacao confiavel.")

    ignorar = [c['COLUMN_NAME'] for c in colunas
               if any(p in c['COLUMN_NAME'].upper() for p in PADROES_AUDITORIA)]
    # coluna de auditoria nunca pode ser chave
    ignorar = [c for c in ignorar if not chave or c not in chave]

    nao_comparaveis = [c['COLUMN_NAME'] for c in colunas
                       if c['DATA_TYPE'] in ('CLOB', 'BLOB', 'NCLOB', 'BFILE', 'LONG',
                                             'LONG RAW', 'XMLTYPE')]
    return {'chave': chave or [], 'ignorar': ignorar, 'aviso': aviso,
            'nao_comparaveis': nao_comparaveis}


# ----------------------------------------------------------------------
# Literais SQL
# ----------------------------------------------------------------------

MASCARA_DATA = 'DD/MM/YYYY HH24:MI:SS'
MASCARA_TS = 'DD/MM/YYYY HH24:MI:SS.FF6'


def literal(valor, tipo):
    """Converte um valor Python no literal SQL correspondente.

    Datas saem sempre com TO_DATE e mascara explicita: depender do
    NLS_DATE_FORMAT da sessao que vai aplicar o script e o erro mais
    comum nesse tipo de geracao.
    """
    if valor is None:
        return 'NULL'
    if tipo in ('DATE',):
        return f"TO_DATE('{valor.strftime('%d/%m/%Y %H:%M:%S')}', '{MASCARA_DATA}')"
    if tipo and tipo.startswith('TIMESTAMP'):
        return f"TO_TIMESTAMP('{valor.strftime('%d/%m/%Y %H:%M:%S.%f')}', '{MASCARA_TS}')"
    if isinstance(valor, (int, float, decimal.Decimal)):
        return str(valor)
    texto = str(valor).replace("'", "''")
    return f"'{texto}'"


def valor_comparavel(valor):
    """Normaliza para comparar: Decimal(10) e Decimal(10.00) sao o
    mesmo dado, e VARCHAR2 com espaco a direita costuma ser ruido."""
    if valor is None:
        return None
    if isinstance(valor, decimal.Decimal):
        return valor.normalize()
    if isinstance(valor, str):
        return valor.rstrip()
    return valor


def sem_acento_caixa(valor):
    """Normaliza o CONTEUDO para comparacao: sem acento e sem diferenca
    de maiuscula/minuscula. Vale para colunas de conteudo e tambem para o
    casamento da chave; os literais do script usam sempre o valor original."""
    valor = valor_comparavel(valor)
    if isinstance(valor, str):
        decomposto = unicodedata.normalize('NFKD', valor)
        puro = ''.join(ch for ch in decomposto if not unicodedata.combining(ch))
        return puro.casefold()
    return valor


# ----------------------------------------------------------------------
# Comparacao de dados
# ----------------------------------------------------------------------

def contar(conn, owner, table, where):
    sql = f"SELECT COUNT(*) AS N FROM {owner}.{table}"
    if where:
        sql += f" WHERE {where}"
    return consultar(conn, sql)[0]['N']


def carregar(conn, owner, table, colunas, chave, where):
    lista = ', '.join(colunas)
    sql = f"SELECT {lista} FROM {owner}.{table}"
    if where:
        sql += f" WHERE {where}"
    sql += f" ORDER BY {', '.join(chave)}"
    linhas = consultar(conn, sql)
    indexado = {}
    duplicadas = []
    for linha in linhas:
        k = tuple(sem_acento_caixa(linha[c]) for c in chave)
        if k in indexado:
            duplicadas.append(k)
        indexado[k] = linha
    return indexado, duplicadas


def comparar_tabela(conn_src, conn_dst, owner, table, chave, ignorar, where,
                    colunas_meta):
    """Compara o conteudo e devolve os tres baldes + o texto do script."""
    tipos = {c['COLUMN_NAME']: c['DATA_TYPE'] for c in colunas_meta}
    todas = [c['COLUMN_NAME'] for c in colunas_meta]

    ignorados = set(i.upper() for i in ignorar)
    comparar = [c for c in todas if c not in ignorados]
    faltando = [c for c in chave if c not in comparar]
    if faltando:
        raise ValueError(f"coluna de chave fora da comparacao: {', '.join(faltando)}")

    n_src = contar(conn_src, owner, table, where)
    n_dst = contar(conn_dst, owner, table, where)
    if max(n_src, n_dst) > LIMITE_LINHAS:
        raise ValueError(f"{owner}.{table} tem {max(n_src, n_dst)} linhas, acima do "
                         f"limite de {LIMITE_LINHAS}. Use Data Pump ou DBMS_COMPARISON, "
                         f"ou restrinja com um filtro WHERE.")

    src, dup_src = carregar(conn_src, owner, table, comparar, chave, where)
    dst, dup_dst = carregar(conn_dst, owner, table, comparar, chave, where)

    if dup_src or dup_dst:
        raise ValueError(f"a chave {', '.join(chave)} nao e unica em "
                         f"{'origem' if dup_src else 'destino'} - escolha outra chave.")

    nao_chave = [c for c in comparar if c not in chave]

    inserir = [k for k in src if k not in dst]
    so_destino = [k for k in dst if k not in src]
    atualizar = []
    for k in src:
        if k not in dst:
            continue
        difs = [c for c in nao_chave
                if sem_acento_caixa(src[k][c]) != sem_acento_caixa(dst[k][c])]
        if difs:
            atualizar.append((k, difs))

    linhas = montar_script(owner, table, chave, comparar, nao_chave, tipos,
                           src, dst, inserir, atualizar, so_destino, where,
                           n_src, n_dst)

    return {'inserir': len(inserir), 'atualizar': len(atualizar),
            'so_destino': len(so_destino), 'origem': n_src, 'destino': n_dst,
            'script': "\n".join(linhas)}


def condicao_chave(chave, valores, tipos):
    return " AND ".join(f"{c} = {literal(v, tipos.get(c))}"
                        for c, v in zip(chave, valores))


def montar_script(owner, table, chave, comparar, nao_chave, tipos, src, dst,
                  inserir, atualizar, so_destino, where, n_src, n_dst):
    ts = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    out = [
        "/*==============================================================*/",
        f"/* DADOS: {owner}.{table}"[:64].ljust(64) + "*/",
        f"/* Gerado em {ts} por oracle_data_web.py"[:64].ljust(64) + "*/",
        f"/* Origem: {n_src} linhas | Destino: {n_dst} linhas"[:64].ljust(64) + "*/",
        f"/* Chave: {', '.join(chave)}"[:64].ljust(64) + "*/",
        "/* Revise antes de aplicar. Commit fica no fim, uma unica vez.    */",
        "/*==============================================================*/",
        "",
    ]
    if where:
        out.append(f"-- Filtro aplicado na comparacao: WHERE {where}")
        out.append("-- Linhas fora desse filtro NAO foram comparadas.")
        out.append("")

    if so_destino:
        out.append("/*--------------------------------------------------------------*/")
        out.append("/* Existem so no DESTINO - nenhum DELETE e gerado. Decida.       */")
        out.append("/*--------------------------------------------------------------*/")
        for k in so_destino:
            out.append(f"-- {condicao_chave(chave, tuple(dst[k][c] for c in chave), tipos)}")
        out.append("")

    if inserir:
        out.append("/*--------------------------------------------------------------*/")
        out.append(f"/* INSERT - {len(inserir)} linha(s)"[:64].ljust(64) + "*/")
        out.append("/*--------------------------------------------------------------*/")
        lista_cols = ", ".join(comparar)
        for k in inserir:
            linha = src[k]
            valores = ", ".join(literal(linha[c], tipos.get(c)) for c in comparar)
            out.append(f"INSERT INTO {owner}.{table} ({lista_cols})")
            out.append(f"VALUES ({valores});")
        out.append("")

    if atualizar:
        out.append("/*--------------------------------------------------------------*/")
        out.append(f"/* UPDATE - {len(atualizar)} linha(s)"[:64].ljust(64) + "*/")
        out.append("/* O valor atual do destino fica no comentario acima de cada    */")
        out.append("/* comando, para permitir reverter.                             */")
        out.append("/*--------------------------------------------------------------*/")
        for k, difs in atualizar:
            atual = ", ".join(f"{c}={literal(dst[k][c], tipos.get(c))}" for c in difs)
            out.append(f"-- destino hoje: {atual}")
            sets = ", ".join(f"{c} = {literal(src[k][c], tipos.get(c))}" for c in difs)
            out.append(f"UPDATE {owner}.{table} SET {sets}")
            out.append(f" WHERE {condicao_chave(chave, tuple(dst[k][c] for c in chave), tipos)};")
        out.append("")

    if not inserir and not atualizar:
        out.append("-- Nenhuma diferenca de dados: nada a aplicar.")
        out.append("")
    else:
        out.append("-- Confira o resultado antes de confirmar:")
        out.append(f"-- SELECT COUNT(*) FROM {owner}.{table};")
        out.append("commit;")

    return out


def gravar_script(owner, table, texto):
    pasta = os.path.join(SAIDA, owner)
    os.makedirs(pasta, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    caminho = os.path.join(pasta, f"{ts}_dados_{table}.sql")
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(texto)
    return caminho


# ----------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):  # silencia o log por requisicao
        pass

    def _responder(self, corpo, tipo='application/json; charset=utf-8', status=200):
        dados = corpo.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _json(self, obj, status=200):
        self._responder(json.dumps(obj, default=str), status=status)

    def _erro(self, msg, status=400):
        self._json({'erro': str(msg)}, status=status)

    # -- GET ----------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        try:
            if url.path == '/':
                return self._responder(PAGINA, 'text/html; charset=utf-8')

            if url.path == '/api/ambiente':
                return self._json({
                    'origem': rotulo('origem'),
                    'destino': rotulo('destino'),
                    'schemas': [s.strip() for s in CFG['opcoes']['schemas'].split(',')],
                    'limite': LIMITE_LINHAS,
                })

            if url.path == '/api/tabelas':
                schema = q.get('schema', [''])[0].upper()
                filtro = q.get('filtro', [''])[0]
                with conectar('origem') as conn:
                    return self._json({'tabelas': listar_tabelas(conn, schema, filtro)})

            if url.path == '/api/detalhe':
                owner = q.get('owner', [''])[0].upper()
                table = q.get('tabela', [''])[0].upper()
                with conectar('origem') as conn:
                    colunas = colunas_da_tabela(conn, owner, table)
                    if not colunas:
                        return self._erro(f'{owner}.{table} nao existe na origem.', 404)
                    chaves = chaves_da_tabela(conn, owner, table)
                return self._json({'colunas': colunas, 'chaves': chaves,
                                   'sugestao': sugerir(colunas, chaves)})

            return self._erro('rota desconhecida', 404)
        except Exception as exc:  # noqa: BLE001
            return self._erro(exc, 500)

    # -- POST ---------------------------------------------------------
    def do_POST(self):
        url = urlparse(self.path)
        tamanho = int(self.headers.get('Content-Length') or 0)
        try:
            pedido = json.loads(self.rfile.read(tamanho) or b'{}')
        except json.JSONDecodeError as exc:
            return self._erro(f'corpo invalido: {exc}')

        if url.path != '/api/comparar':
            return self._erro('rota desconhecida', 404)

        resultados = []
        try:
            conn_src = conectar('origem')
            conn_dst = conectar('destino')
        except Exception as exc:  # noqa: BLE001
            return self._erro(f'falha ao conectar: {exc}', 500)

        try:
            for item in pedido.get('tabelas', []):
                owner = str(item['owner']).upper()
                table = str(item['tabela']).upper()
                try:
                    colunas_meta = colunas_da_tabela(conn_src, owner, table)
                    validos = {c['COLUMN_NAME'] for c in colunas_meta}
                    chave = [c.upper() for c in item.get('chave', [])]
                    ignorar = [c.upper() for c in item.get('ignorar', [])]
                    desconhecidas = [c for c in chave + ignorar if c not in validos]
                    if desconhecidas:
                        raise ValueError(f"coluna inexistente: {', '.join(desconhecidas)}")
                    if not chave:
                        raise ValueError('nenhuma coluna de chave escolhida')

                    r = comparar_tabela(conn_src, conn_dst, owner, table, chave,
                                        ignorar, (item.get('where') or '').strip(),
                                        colunas_meta)
                    caminho = gravar_script(owner, table, r.pop('script'))
                    r.update({'owner': owner, 'tabela': table, 'arquivo': caminho,
                              'ok': True})
                    resultados.append(r)
                except Exception as exc:  # noqa: BLE001
                    resultados.append({'owner': owner, 'tabela': table, 'ok': False,
                                       'erro': str(exc)})
        finally:
            conn_src.close()
            conn_dst.close()

        return self._json({'resultados': resultados})


# ----------------------------------------------------------------------
# Frontend
# ----------------------------------------------------------------------

PAGINA = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comparar dados entre bases</title>
<style>
  :root {
    --tinta: #16202b;
    --papel: #f7f8f9;
    --painel: #ffffff;
    --linha: #d5dbe0;
    --suave: #64717d;
    --acento: #1f5f8b;
    --alerta: #8a5a00;
    --erro: #9b2c2c;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--papel);
    color: var(--tinta);
    font: 15px/1.55 ui-sans-serif, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  code, .mono, td.mono { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; }
  header {
    background: var(--tinta);
    color: #eef2f5;
    padding: 18px 24px;
  }
  header h1 { margin: 0; font-size: 19px; font-weight: 600; letter-spacing: .01em; }
  header p { margin: 4px 0 0; color: #a9b7c4; font-size: 13.5px; }
  header .fluxo { font-family: ui-monospace, Consolas, monospace; color: #7fb5da; }
  main { max-width: 1140px; margin: 0 auto; padding: 24px; }
  section { background: var(--painel); border: 1px solid var(--linha); margin-bottom: 20px; }
  section > h2 {
    margin: 0; padding: 12px 16px; font-size: 14px; font-weight: 600;
    border-bottom: 1px solid var(--linha); background: #eef1f4;
  }
  .corpo { padding: 16px; }
  label { display: block; font-size: 13px; color: var(--suave); margin-bottom: 4px; }
  input, select, textarea {
    font: inherit; padding: 6px 8px; border: 1px solid var(--linha);
    background: #fff; color: inherit; border-radius: 2px;
  }
  input:focus, select:focus, textarea:focus, button:focus {
    outline: 2px solid var(--acento); outline-offset: 1px;
  }
  .filtros { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; }
  button {
    font: inherit; padding: 7px 16px; border: 1px solid var(--acento);
    background: var(--acento); color: #fff; border-radius: 2px; cursor: pointer;
  }
  button.secundario { background: #fff; color: var(--acento); }
  button[disabled] { opacity: .5; cursor: default; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #e7ebee; }
  th { color: var(--suave); font-weight: 600; font-size: 12.5px; }
  td.num, th.num { text-align: right; }
  tbody tr:hover { background: #f2f6f9; }
  .vazio { color: var(--suave); padding: 16px; }
  .tabela-rolagem { max-height: 340px; overflow: auto; }
  .escolhida { border: 1px solid var(--linha); margin-bottom: 14px; }
  .escolhida > .topo {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 12px; background: #f4f7f9; border-bottom: 1px solid var(--linha);
  }
  .escolhida .nome { font-family: ui-monospace, Consolas, monospace; font-weight: 600; }
  .escolhida .grade { padding: 12px; display: grid; gap: 14px; grid-template-columns: 1fr 1fr; }
  .caixa-colunas {
    border: 1px solid var(--linha); max-height: 170px; overflow: auto; padding: 6px 8px;
    font-family: ui-monospace, Consolas, monospace; font-size: 12.5px;
  }
  .caixa-colunas div { padding: 1px 0; }
  .aviso { border-left: 3px solid var(--alerta); background: #fdf7ea; padding: 8px 12px;
           margin: 0 12px 12px; font-size: 13px; }
  .erro { border-left: 3px solid var(--erro); background: #fdf0f0; padding: 8px 12px;
          font-size: 13px; }
  button.link { background: none; border: none; color: var(--acento); padding: 0 2px;
                text-decoration: underline; cursor: pointer; font-size: 12.5px; }
  button.link:hover { color: #144462; }
  .acoes-grupo { display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
                 margin-bottom: 6px; font-size: 12.5px; }
  .acoes-grupo .contador { margin-left: auto; color: var(--suave); }
  .barra-global { display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
                  padding: 8px 12px; margin-bottom: 14px; background: #eef4f8;
                  border: 1px solid var(--linha); font-size: 13px; }
  .barra-global button { padding: 4px 12px; font-size: 13px; }
  .col-item { display: flex; gap: 6px; color: inherit; margin: 0; cursor: pointer; }
  .col-item .tipo { color: var(--suave); }
  .aviso.perigo { border-left-color: var(--erro); background: #fdf0f0; }
  .remover { background: none; border: none; color: var(--erro); cursor: pointer; padding: 2px 6px; }
  .rodape-acao { display: flex; gap: 12px; align-items: center; }
  .status { color: var(--suave); font-size: 13px; }
  @media (max-width: 760px) { .escolhida .grade { grid-template-columns: 1fr; } }
  @media (prefers-reduced-motion: no-preference) { tbody tr { transition: background .12s; } }
</style>
</head>
<body>
<header>
  <h1>Comparar dados entre bases</h1>
  <p>Escolha as tabelas do schema de origem. O script de INSERT e UPDATE sai por tabela.
     <span class="fluxo" id="fluxo"></span></p>
</header>

<main>
  <section>
    <h2>Tabelas da origem</h2>
    <div class="corpo">
      <div class="filtros">
        <div>
          <label for="schema">Schema</label>
          <select id="schema"></select>
        </div>
        <div>
          <label for="filtro">Nome contém (opcional, use % do Oracle)</label>
          <input id="filtro" placeholder="TB_%" size="22">
        </div>
        <button id="btn-listar">Listar tabelas</button>
        <span class="status" id="status-lista"></span>
      </div>
    </div>
    <div class="tabela-rolagem">
      <table id="lista">
        <thead>
          <tr><th>Tabela</th><th class="num">Linhas (estimativa)</th>
              <th class="num">Colunas</th><th>Estatística de</th><th></th></tr>
        </thead>
        <tbody><tr><td colspan="5" class="vazio">Liste um schema para começar.</td></tr></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Tabelas escolhidas</h2>
    <div class="corpo" id="escolhidas">
      <p class="vazio" style="padding:0">Nenhuma tabela escolhida ainda.</p>
    </div>
    <div class="corpo" style="border-top:1px solid var(--linha)">
      <div class="rodape-acao">
        <button id="btn-comparar" disabled>Comparar e gerar scripts</button>
        <span class="status" id="status-comparar"></span>
      </div>
    </div>
  </section>

  <section id="sec-resultado" hidden>
    <h2>Resultado</h2>
    <div class="corpo">
      <table id="resultado">
        <thead>
          <tr><th>Tabela</th><th class="num">Inserir</th><th class="num">Atualizar</th>
              <th class="num">Só no destino</th><th>Arquivo gerado</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </section>
</main>

<script>
const escolhidas = new Map();
let limite = 0;

async function api(rota, opcoes) {
  const r = await fetch(rota, opcoes);
  const dados = await r.json();
  if (!r.ok) throw new Error(dados.erro || 'falha na requisição');
  return dados;
}

function texto(el, msg) { el.textContent = msg || ''; }

async function iniciar() {
  const amb = await api('/api/ambiente');
  limite = amb.limite;
  document.getElementById('fluxo').textContent = `${amb.origem} → ${amb.destino}`;
  const sel = document.getElementById('schema');
  sel.innerHTML = amb.schemas.map(s => `<option>${s}</option>`).join('');
}

async function listar() {
  const schema = document.getElementById('schema').value;
  const filtro = document.getElementById('filtro').value.trim();
  const st = document.getElementById('status-lista');
  texto(st, 'consultando…');
  const corpo = document.querySelector('#lista tbody');
  try {
    const d = await api(`/api/tabelas?schema=${encodeURIComponent(schema)}&filtro=${encodeURIComponent(filtro)}`);
    texto(st, `${d.tabelas.length} tabelas`);
    if (!d.tabelas.length) {
      corpo.innerHTML = '<tr><td colspan="5" class="vazio">Nenhuma tabela com esse filtro.</td></tr>';
      return;
    }
    corpo.innerHTML = d.tabelas.map(t => {
      const linhas = t.NUM_ROWS === null ? 'sem estatística' : Number(t.NUM_ROWS).toLocaleString('pt-BR');
      const grande = t.NUM_ROWS !== null && t.NUM_ROWS > limite;
      const quando = t.LAST_ANALYZED ? String(t.LAST_ANALYZED).slice(0, 10) : '—';
      return `<tr><td class="mono">${t.TABLE_NAME}</td>
        <td class="num">${linhas}${grande ? ' ⚠' : ''}</td>
        <td class="num">${t.N_COLUNAS}</td>
        <td>${quando}</td>
        <td><button class="secundario" data-tabela="${t.TABLE_NAME}">Escolher</button></td></tr>`;
    }).join('');
    corpo.querySelectorAll('button[data-tabela]').forEach(b =>
      b.addEventListener('click', () => escolher(schema, b.dataset.tabela)));
  } catch (e) {
    texto(st, '');
    corpo.innerHTML = `<tr><td colspan="5"><div class="erro">${e.message}</div></td></tr>`;
  }
}

async function escolher(owner, tabela) {
  const id = `${owner}.${tabela}`;
  if (escolhidas.has(id)) return;
  const d = await api(`/api/detalhe?owner=${owner}&tabela=${tabela}`);
  const e = { owner, tabela, ...d, where: '' };
  e.sel = {
    chave: new Set(d.sugestao.chave),
    ignorar: new Set([...d.sugestao.ignorar, ...d.sugestao.nao_comparaveis])
  };
  escolhidas.set(id, e);
  desenharEscolhidas();
}

const nomesColunas = e => e.colunas.map(c => c.COLUMN_NAME);
const comparaveis = e => nomesColunas(e).filter(n => !e.sugestao.nao_comparaveis.includes(n));

function caixaColunas(id, e, grupo) {
  const naoComp = e.sugestao.nao_comparaveis;
  return `<div class="caixa-colunas">` + e.colunas.map(c => {
    const nome = c.COLUMN_NAME;
    const bloqueado = naoComp.includes(nome) ? 'disabled' : '';
    return `<div><label class="col-item">
      <input type="checkbox" data-id="${id}" data-grupo="${grupo}" value="${nome}" ${bloqueado}>
      <span>${nome}<span class="tipo"> ${c.DATA_TYPE}</span></span>
    </label></div>`;
  }).join('') + `</div>`;
}

function barraAcoes(id, grupo) {
  const b = (acao, rotulo, dica) =>
    `<button type="button" class="link" data-acao="${acao}" data-id="${id}"
             data-grupo="${grupo}" title="${dica}">${rotulo}</button>`;
  return `<div class="acoes-grupo">
    ${b('todas', 'Marcar todas', 'Marca todas as colunas comparáveis')}
    ${b('nenhuma', 'Limpar', 'Desmarca todas')}
    ${b('inverter', 'Inverter', 'Marca o que está desmarcado e vice-versa')}
    ${b('sugerida', 'Sugestão', 'Volta ao que a ferramenta sugeriu')}
    <span class="contador" data-contador="${grupo}"></span>
  </div>`;
}

function aplicarAcao(id, grupo, acao) {
  const e = escolhidas.get(id);
  if (!e) return;
  const s = e.sel;
  const naoComp = e.sugestao.nao_comparaveis;
  if (grupo === 'chave') {
    const comp = comparaveis(e);
    if (acao === 'todas') s.chave = new Set(comp);
    else if (acao === 'nenhuma') s.chave = new Set();
    else if (acao === 'inverter') s.chave = new Set(comp.filter(n => !s.chave.has(n)));
    else s.chave = new Set(e.sugestao.chave);
    // coluna de chave nunca pode estar em "ignorar"
    s.chave.forEach(n => s.ignorar.delete(n));
  } else {
    const livres = nomesColunas(e).filter(n => !s.chave.has(n));
    if (acao === 'todas') s.ignorar = new Set(livres);
    else if (acao === 'nenhuma') s.ignorar = new Set();
    else if (acao === 'inverter') s.ignorar = new Set(livres.filter(n => !s.ignorar.has(n)));
    else s.ignorar = new Set([...e.sugestao.ignorar].filter(n => !s.chave.has(n)));
    // tipos grandes (LOB etc.) ficam sempre fora da comparação
    naoComp.forEach(n => s.ignorar.add(n));
  }
  atualizarCard(id);
}

function atualizarCard(id) {
  const e = escolhidas.get(id);
  const card = document.querySelector(`[data-card="${id}"]`);
  if (!e || !card) return;
  card.querySelectorAll('input[type=checkbox][data-grupo]').forEach(i => {
    i.checked = e.sel[i.dataset.grupo].has(i.value);
  });
  const comp = comparaveis(e);
  card.querySelector('[data-contador="chave"]').textContent =
    `${e.sel.chave.size} de ${comp.length} marcadas`;
  card.querySelector('[data-contador="ignorar"]').textContent =
    `${e.sel.ignorar.size} de ${e.colunas.length} marcadas`;
  const msg = card.querySelector('[data-msg]');
  if (!e.sel.chave.size) {
    msg.className = 'aviso perigo';
    msg.textContent = 'Marque ao menos uma coluna de chave, senão não há como comparar.';
    msg.hidden = false;
  } else if (comp.every(n => e.sel.chave.has(n))) {
    msg.className = 'aviso';
    msg.textContent = 'Todas as colunas comparáveis são chave: nunca haverá UPDATE. ' +
      'Uma linha com qualquer diferença aparece como INSERT (origem) e como "só no destino".';
    msg.hidden = false;
  } else {
    msg.hidden = true;
  }
}

function desenharEscolhidas() {
  const alvo = document.getElementById('escolhidas');
  document.getElementById('btn-comparar').disabled = escolhidas.size === 0;
  if (!escolhidas.size) {
    alvo.innerHTML = '<p class="vazio" style="padding:0">Nenhuma tabela escolhida ainda.</p>';
    return;
  }
  const global = escolhidas.size > 1 ? `<div class="barra-global">
      <strong>Em todas as tabelas:</strong>
      <button type="button" class="secundario" data-global="todas">Chave = todas as colunas</button>
      <button type="button" class="secundario" data-global="sugerida">Voltar à sugestão</button>
    </div>` : '';
  alvo.innerHTML = global + [...escolhidas.entries()].map(([id, e]) => {
    const naoComp = e.sugestao.nao_comparaveis;
    return `<div class="escolhida" data-card="${id}">
      <div class="topo">
        <span class="nome">${id}</span>
        <button class="remover" data-remover="${id}">remover</button>
      </div>
      ${e.sugestao.aviso ? `<div class="aviso">${e.sugestao.aviso}</div>` : ''}
      ${naoComp.length ? `<div class="aviso">Colunas de tipo grande não são comparadas
         e ficam de fora do script: ${naoComp.join(', ')}.</div>` : ''}
      <div class="aviso" data-msg hidden></div>
      <div class="grade">
        <div>
          <label>Chave de comparação — identifica a mesma linha nos dois bancos</label>
          ${barraAcoes(id, 'chave')}
          ${caixaColunas(id, e, 'chave')}
        </div>
        <div>
          <label>Ignorar na comparação — colunas de auditoria já vêm marcadas</label>
          ${barraAcoes(id, 'ignorar')}
          ${caixaColunas(id, e, 'ignorar')}
        </div>
      </div>
      <div class="grade" style="grid-template-columns:1fr">
        <div>
          <label>Filtro opcional (WHERE, aplicado nos dois lados)</label>
          <input data-where="${id}" style="width:100%" placeholder="FL_ATIVO = 'S'">
        </div>
      </div>
    </div>`;
  }).join('');

  for (const [id, e] of escolhidas) {
    alvo.querySelector(`[data-where="${id}"]`).value = e.where;
    atualizarCard(id);
  }
  alvo.querySelectorAll('[data-remover]').forEach(b =>
    b.addEventListener('click', () => { escolhidas.delete(b.dataset.remover); desenharEscolhidas(); }));
}

// Eventos delegados: valem para qualquer tabela escolhida, sem redesenhar a tela
(function () {
  const alvo = document.getElementById('escolhidas');

  alvo.addEventListener('change', ev => {
    const i = ev.target;
    if (!i.matches('input[type=checkbox][data-grupo]')) return;
    const e = escolhidas.get(i.dataset.id);
    const g = i.dataset.grupo;
    const outro = g === 'chave' ? 'ignorar' : 'chave';
    if (i.checked) { e.sel[g].add(i.value); e.sel[outro].delete(i.value); }
    else e.sel[g].delete(i.value);
    atualizarCard(i.dataset.id);
  });

  alvo.addEventListener('click', ev => {
    const b = ev.target.closest('button');
    if (!b) return;
    if (b.dataset.acao) aplicarAcao(b.dataset.id, b.dataset.grupo, b.dataset.acao);
    else if (b.dataset.global) {
      for (const id of escolhidas.keys()) {
        aplicarAcao(id, 'chave', b.dataset.global);
        if (b.dataset.global === 'sugerida') aplicarAcao(id, 'ignorar', 'sugerida');
      }
    }
  });

  alvo.addEventListener('input', ev => {
    const id = ev.target.dataset && ev.target.dataset.where;
    if (id && escolhidas.has(id)) escolhidas.get(id).where = ev.target.value;
  });
})();

function coletar() {
  return [...escolhidas.values()].map(e => {
    const ordenar = conj => nomesColunas(e).filter(n => conj.has(n));
    return { owner: e.owner, tabela: e.tabela, chave: ordenar(e.sel.chave),
             ignorar: ordenar(e.sel.ignorar), where: e.where };
  });
}

async function comparar() {
  const botao = document.getElementById('btn-comparar');
  const st = document.getElementById('status-comparar');
  botao.disabled = true;
  texto(st, 'comparando — pode levar alguns minutos em tabela grande…');
  try {
    const d = await api('/api/comparar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tabelas: coletar() })
    });
    document.getElementById('sec-resultado').hidden = false;
    document.querySelector('#resultado tbody').innerHTML = d.resultados.map(r => {
      if (!r.ok) return `<tr><td class="mono">${r.owner}.${r.tabela}</td>
        <td colspan="4"><div class="erro">${r.erro}</div></td></tr>`;
      return `<tr><td class="mono">${r.owner}.${r.tabela}</td>
        <td class="num">${r.inserir}</td><td class="num">${r.atualizar}</td>
        <td class="num">${r.so_destino}</td><td class="mono">${r.arquivo}</td></tr>`;
    }).join('');
    texto(st, 'concluído');
  } catch (e) {
    texto(st, e.message);
  } finally {
    botao.disabled = false;
  }
}

document.getElementById('btn-listar').addEventListener('click', listar);
document.getElementById('btn-comparar').addEventListener('click', comparar);
iniciar();
</script>
</body>
</html>
"""


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    global CFG, SAIDA, LIMITE_LINHAS

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default='config.ini')
    ap.add_argument('--porta', type=int, default=8765)
    ap.add_argument('--saida', default='dados', help='pasta raiz dos scripts gerados')
    ap.add_argument('--sem-navegador', action='store_true')
    args = ap.parse_args()

    CFG = configparser.ConfigParser()
    CFG.read(args.config, encoding='utf-8')
    if 'origem' not in CFG or 'destino' not in CFG:
        print(f"{args.config} nao tem as secoes [origem] e [destino].", file=sys.stderr)
        sys.exit(1)

    SAIDA = args.saida
    LIMITE_LINHAS = CFG['opcoes'].getint('limite_linhas', fallback=50000)

    # falha cedo: melhor descobrir problema de conexao agora do que no
    # primeiro clique do usuario
    for secao in ('origem', 'destino'):
        try:
            conectar(secao).close()
        except Exception as exc:  # noqa: BLE001
            print(f"Nao conectou em [{secao}]: {exc}", file=sys.stderr)
            sys.exit(1)

    endereco = f"http://127.0.0.1:{args.porta}"
    servidor = ThreadingHTTPServer(('127.0.0.1', args.porta), Handler)
    print(f"Origem: {rotulo('origem')} | Destino: {rotulo('destino')}")
    print(f"Scripts vao para ./{SAIDA}/<SCHEMA>/")
    print(f"Abra {endereco} - Ctrl+C para encerrar.")
    if not args.sem_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(endereco)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
        servidor.shutdown()


if __name__ == '__main__':
    main()