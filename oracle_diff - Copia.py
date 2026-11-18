#!/usr/bin/env python3
"""
oracle_diff.py

Conecta em dois bancos Oracle (origem e destino), compara os schemas
indicados e gera:
  1. Um relatorio de diferencas (texto)
  2. Um script DDL pronto para aplicar no DESTINO, com o que falta
     para ele ficar igual a ORIGEM - incluindo o CREATE TABLE completo
     (via DBMS_METADATA.GET_DDL na origem, sem STORAGE/TABLESPACE),
     comentarios (convertidos para ASCII), grants, sequences e
     sinonimos. Compara tambem indices, texto de views, fontes
     PL/SQL, colunas faltantes, constraints (FK num bloco final) e a
     ordem fisica das colunas.

Ordem de aplicacao dentro de cada script: sequences, tabelas, colunas,
ajustes de coluna, indices, constraints PK/UK/CHECK, views, PL/SQL e,
por ultimo, as foreign keys.

Compatibilidade: usa TEXT_VC (DBA_VIEWS) e SEARCH_CONDITION_VC
(DBA_CONSTRAINTS), disponiveis a partir do 12.2.

Requisitos:
    pip install -r requirements.txt   (so precisa do pacote oracledb)

Uso:
    python3 oracle_diff.py --config config.ini \
        --report diff_report.txt --ddl diff_script.sql

O arquivo config.ini (veja config.ini.example) guarda usuario, senha,
dsn de cada ambiente e a lista de schemas a comparar.

Privilegio necessario: SELECT em DBA_TABLES, DBA_TAB_COLUMNS,
DBA_SEQUENCES, DBA_CONSTRAINTS, DBA_CONS_COLUMNS, DBA_SYNONYMS,
DBA_VIEWS, DBA_INDEXES, DBA_IND_COLUMNS, DBA_SOURCE, DBA_OBJECTS,
DBA_TAB_PRIVS, DBA_TAB_COMMENTS, DBA_COL_COMMENTS (ou o
SELECT_CATALOG_ROLE) na conexao de ORIGEM, para o DBMS_METADATA.GET_DDL
funcionar; no DESTINO basta enxergar as mesmas DBA_*/ALL_* para a
comparacao (defina usar_dba_views=false em config.ini se o usuario do
destino nao tiver privilegio DBA).
"""

import argparse
import configparser
import datetime
import os
import sys
import unicodedata
from collections import defaultdict

try:
    import oracledb
except ImportError:
    print("Falta o pacote 'oracledb'. Rode: pip install -r requirements.txt",
          file=sys.stderr)
    sys.exit(1)


# ----------------------------------------------------------------------
# Config e conexao
# ----------------------------------------------------------------------

def load_config(path):
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding='utf-8')
    return cfg


def connect(cfg, section):
    user = cfg[section]['user']
    password = cfg[section]['password']
    dsn = cfg[section]['dsn']
    label = cfg[section].get('label', section)
    print(f"Conectando em {label} ({dsn})...", file=sys.stderr)
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    return conn, label


def strip_accents(text):
    """Remove acentuacao, mantendo o texto legivel em ASCII puro -
    convencao firme para COMMENT ON no ambiente do usuario."""
    if text is None:
        return text
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def read_long(value):
    """DATA_DEFAULT vem como LONG (ou LOB, dependendo do driver/modo).
    Devolve sempre str ou None."""
    if value is None:
        return None
    if hasattr(value, 'read'):
        value = value.read()
    return str(value)


def norm_default(value):
    """Normaliza o DATA_DEFAULT para comparacao.

    O dicionario guarda o texto cru do DEFAULT, muitas vezes com
    espacos/quebra de linha no fim ('SYSDATE\\n'), e a mesma expressao
    pode ter sido escrita em caixa diferente nos dois ambientes
    ('sysdate' x 'SYSDATE'). Normalizamos so o que e seguro: apara
    espacos e, quando NAO ha literal entre aspas, compara sem caixa
    (dentro de aspas a caixa e dado, nao sintaxe).
    Devolve None quando nao ha default.
    """
    text = read_long(value)
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    if text.upper() == 'NULL':
        return None
    if "'" not in text:
        text = " ".join(text.upper().split())
    else:
        text = " ".join(text.split())
    return text


def default_literal(value):
    """Texto do DEFAULT para usar no DDL (sem normalizar caixa)."""
    text = read_long(value)
    return text.strip() if text and text.strip() else None


# ----------------------------------------------------------------------
# Extracao (funciona com DBA_* ou ALL_*, conforme config)
# ----------------------------------------------------------------------

def view_prefix(cfg):
    return 'DBA' if cfg['opcoes'].getboolean('usar_dba_views', fallback=True) else 'ALL'


def fetch_all(conn, sql, binds=None):
    cur = conn.cursor()
    cur.execute(sql, binds or {})
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    return rows


def schema_list_bind(schemas):
    """Gera a clausula IN (:s0, :s1, ...) e o dict de binds."""
    placeholders = ", ".join(f":s{i}" for i in range(len(schemas)))
    binds = {f"s{i}": s.strip() for i, s in enumerate(schemas)}
    return placeholders, binds


class SchemaSnapshot:
    """Consulta um banco vivo e guarda tudo que precisamos comparar."""

    def __init__(self, conn, label, schemas, prefix):
        self.label = label
        self.schemas = schemas
        ph, binds = schema_list_bind(schemas)

        self.tables = fetch_all(conn, f"""
            SELECT owner, table_name, tablespace_name, status
            FROM   {prefix}_tables
            WHERE  owner IN ({ph})
        """, binds)

        self.columns = fetch_all(conn, f"""
            SELECT owner, table_name, column_name, column_id, data_type,
                   data_length, data_precision, data_scale, nullable, data_default,
                   char_length, char_used
            FROM   {prefix}_tab_columns
            WHERE  owner IN ({ph})
        """, binds)

        self.sequences = fetch_all(conn, f"""
            SELECT sequence_owner AS owner, sequence_name, min_value, max_value,
                   increment_by, last_number, cache_size, cycle_flag
            FROM   {prefix}_sequences
            WHERE  sequence_owner IN ({ph})
        """, binds)

        self.constraints = fetch_all(conn, f"""
            SELECT owner, table_name, constraint_name, constraint_type,
                   status, r_owner, r_constraint_name, delete_rule,
                   search_condition_vc
            FROM   {prefix}_constraints
            WHERE  owner IN ({ph})
        """, binds)

        self.indexes = fetch_all(conn, f"""
            SELECT owner, index_name, table_owner, table_name, index_type,
                   uniqueness, status
            FROM   {prefix}_indexes
            WHERE  table_owner IN ({ph})
        """, binds)

        self.ind_columns = fetch_all(conn, f"""
            SELECT index_owner, index_name, table_owner, table_name,
                   column_name, column_position, descend
            FROM   {prefix}_ind_columns
            WHERE  table_owner IN ({ph})
        """, binds)

        # PL/SQL e afins: comparamos existencia e um hash do fonte
        # (soma de ORA_HASH por linha) - suficiente para saber que o
        # corpo divergiu, sem trazer o texto inteiro dos dois bancos.
        self.plsql = fetch_all(conn, f"""
            SELECT owner, name, type, COUNT(*) AS n_linhas,
                   SUM(ORA_HASH(TO_CHAR(line) || RTRIM(text))) AS src_hash
            FROM   {prefix}_source
            WHERE  owner IN ({ph})
            AND    type IN ('TRIGGER','PROCEDURE','FUNCTION','PACKAGE',
                            'PACKAGE BODY','TYPE','TYPE BODY')
            GROUP BY owner, name, type
        """, binds)

        self.invalid_objects = fetch_all(conn, f"""
            SELECT owner, object_name, object_type, status
            FROM   {prefix}_objects
            WHERE  owner IN ({ph}) AND status <> 'VALID'
        """, binds)

        self.cons_columns = fetch_all(conn, f"""
            SELECT owner, table_name, constraint_name, column_name, position
            FROM   {prefix}_cons_columns
            WHERE  owner IN ({ph})
        """, binds)

        self.synonyms = fetch_all(conn, f"""
            SELECT owner, synonym_name, table_owner, table_name
            FROM   {prefix}_synonyms
            WHERE  table_owner IN ({ph})
        """, binds)

        self.views = fetch_all(conn, f"""
            SELECT owner, view_name, text_vc
            FROM   {prefix}_views
            WHERE  owner IN ({ph})
        """, binds)

        self.grants = fetch_all(conn, f"""
            SELECT grantor, grantee, owner, table_name, privilege, grantable
            FROM   {prefix}_tab_privs
            WHERE  owner IN ({ph})
        """, binds)

        self.table_comments = fetch_all(conn, f"""
            SELECT owner, table_name, comments
            FROM   {prefix}_tab_comments
            WHERE  owner IN ({ph}) AND comments IS NOT NULL
        """, binds)

        self.col_comments = fetch_all(conn, f"""
            SELECT owner, table_name, column_name, comments
            FROM   {prefix}_col_comments
            WHERE  owner IN ({ph}) AND comments IS NOT NULL
        """, binds)

        # indices auxiliares
        self.table_keys = {(t['OWNER'], t['TABLE_NAME']) for t in self.tables}
        self.seq_keys = {(s['OWNER'], s['SEQUENCE_NAME']) for s in self.sequences}
        self.view_keys = {(v['OWNER'], v['VIEW_NAME']) for v in self.views}
        self.syn_keys = {(s['OWNER'], s['SYNONYM_NAME']) for s in self.synonyms}
        self.syn_target = {(s['OWNER'], s['SYNONYM_NAME']): (s['TABLE_OWNER'], s['TABLE_NAME'])
                            for s in self.synonyms}

        self.view_text = {(v['OWNER'], v['VIEW_NAME']): v.get('TEXT_VC') for v in self.views}

        self.index_keys = {(i['OWNER'], i['INDEX_NAME']) for i in self.indexes}
        self.index_by_key = {(i['OWNER'], i['INDEX_NAME']): i for i in self.indexes}

        ind_cols = defaultdict(list)
        for ic in self.ind_columns:
            ind_cols[(ic['INDEX_OWNER'], ic['INDEX_NAME'])].append(ic)
        self.index_columns = {
            k: [c['COLUMN_NAME'] + ('' if c.get('DESCEND') in (None, 'ASC') else ' DESC')
                for c in sorted(v, key=lambda x: x['COLUMN_POSITION'])]
            for k, v in ind_cols.items()
        }

        # indices criados implicitamente por PK/UK - nao geramos DDL
        # proprio para eles, vem junto com a constraint
        self.constraint_index_names = {
            (c['OWNER'], c['CONSTRAINT_NAME'])
            for c in self.constraints if c['CONSTRAINT_TYPE'] in ('P', 'U')
        }

        self.plsql_keys = {(p['OWNER'], p['TYPE'], p['NAME']) for p in self.plsql}
        self.plsql_hash = {(p['OWNER'], p['TYPE'], p['NAME']): (p['N_LINHAS'], p['SRC_HASH'])
                            for p in self.plsql}

        self.cols_by_table = defaultdict(list)
        for c in self.columns:
            self.cols_by_table[(c['OWNER'], c['TABLE_NAME'])].append(c)

        self.cons_by_table = defaultdict(list)
        for c in self.constraints:
            self.cons_by_table[(c['OWNER'], c['TABLE_NAME'])].append(c)

        self.cons_by_key = {(c['OWNER'], c['CONSTRAINT_NAME']): c for c in self.constraints}

        self.cons_cols_by_key = defaultdict(list)
        for cc in self.cons_columns:
            self.cons_cols_by_key[(cc['OWNER'], cc['CONSTRAINT_NAME'])].append(cc)

        self.grants_by_table = defaultdict(list)
        for g in self.grants:
            self.grants_by_table[(g['OWNER'], g['TABLE_NAME'])].append(g)

        self.tab_comment = {(t['OWNER'], t['TABLE_NAME']): t['COMMENTS'] for t in self.table_comments}
        self.col_comment = {(c['OWNER'], c['TABLE_NAME'], c['COLUMN_NAME']): c['COMMENTS']
                             for c in self.col_comments}


# ----------------------------------------------------------------------
# Comparacao
# ----------------------------------------------------------------------

def col_signature(col):
    return (
        col.get('DATA_TYPE'),
        col.get('DATA_LENGTH'),
        col.get('DATA_PRECISION'),
        col.get('DATA_SCALE'),
        col.get('NULLABLE'),
        norm_default(col.get('DATA_DEFAULT')),
    )


def describe_col_diff(src_col, dst_col):
    """Lista em texto o que difere entre as duas colunas."""
    parts = []
    if (src_col.get('DATA_TYPE'), src_col.get('DATA_LENGTH'),
            src_col.get('DATA_PRECISION'), src_col.get('DATA_SCALE')) != \
       (dst_col.get('DATA_TYPE'), dst_col.get('DATA_LENGTH'),
            dst_col.get('DATA_PRECISION'), dst_col.get('DATA_SCALE')):
        parts.append('tipo/tamanho')
    if src_col.get('NULLABLE') != dst_col.get('NULLABLE'):
        parts.append('nullable')
    if norm_default(src_col.get('DATA_DEFAULT')) != norm_default(dst_col.get('DATA_DEFAULT')):
        parts.append('default')
    return ", ".join(parts) or 'indefinido'


def is_system_generated(name):
    return bool(name) and name.upper().startswith('SYS_C')


def compare(src: SchemaSnapshot, dst: SchemaSnapshot):
    report = []

    def add(section, msg, ref=None):
        report.append({'section': section, 'msg': msg, 'ref': ref})

    missing_tables = sorted(src.table_keys - dst.table_keys)
    for t in missing_tables:
        add('TABELA FALTANTE', f'{t[0]}.{t[1]} existe em {src.label}, ausente em {dst.label}', ref=t)

    extra_tables = sorted(dst.table_keys - src.table_keys)
    for t in extra_tables:
        add('TABELA EXTRA', f'{t[0]}.{t[1]} existe em {dst.label}, ausente em {src.label}', ref=t)

    missing_seq = sorted(src.seq_keys - dst.seq_keys)
    for s in missing_seq:
        add('SEQUENCE FALTANTE', f'{s[0]}.{s[1]} existe em {src.label}, ausente em {dst.label}', ref=s)

    missing_views = sorted(src.view_keys - dst.view_keys)
    for v in missing_views:
        add('VIEW FALTANTE', f'{v[0]}.{v[1]} existe em {src.label}, ausente em {dst.label}', ref=v)

    missing_syn = sorted(src.syn_keys - dst.syn_keys)
    for s in missing_syn:
        target = src.syn_target.get(s, ('?', '?'))
        add('SINONIMO FALTANTE',
            f'{s[0]}.{s[1]} -> {target[0]}.{target[1]} existe em {src.label}, ausente em {dst.label}',
            ref=(s, target))

    common_tables = src.table_keys & dst.table_keys
    column_diffs = []  # (owner, table, column, direction, src_col_or_none)
    for owner, table in sorted(common_tables):
        src_cols = {c['COLUMN_NAME']: c for c in src.cols_by_table.get((owner, table), [])}
        dst_cols = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get((owner, table), [])}

        for c in sorted(set(src_cols) - set(dst_cols)):
            add('COLUNA FALTANTE', f'{owner}.{table}.{c} existe em {src.label}, ausente em {dst.label}',
                ref=(owner, table, c))

        for c in sorted(set(dst_cols) - set(src_cols)):
            add('COLUNA EXTRA', f'{owner}.{table}.{c} existe em {dst.label}, ausente em {src.label}',
                ref=(owner, table, c))

        for c in sorted(set(src_cols) & set(dst_cols)):
            if col_signature(src_cols[c]) != col_signature(dst_cols[c]):
                add('COLUNA DIVERGENTE',
                    f'{owner}.{table}.{c} [{describe_col_diff(src_cols[c], dst_cols[c])}]: '
                    f'{dst.label}={col_signature(dst_cols[c])} '
                    f'vs {src.label}={col_signature(src_cols[c])}',
                    ref=(owner, table, c, src_cols[c], dst_cols[c]))
                column_diffs.append((owner, table, c, src_cols[c], dst_cols[c]))

        # ordem fisica das colunas (COLUMN_ID) - divergencia quebra
        # INSERT sem lista de colunas e SELECT *
        common_cols = set(src_cols) & set(dst_cols)
        src_order = [c for c in sorted(common_cols, key=lambda x: src_cols[x]['COLUMN_ID'])]
        dst_order = [c for c in sorted(common_cols, key=lambda x: dst_cols[x]['COLUMN_ID'])]
        if src_order != dst_order:
            add('ORDEM DE COLUNAS',
                f'{owner}.{table}: ordem diverge ({dst.label}={dst_order} vs {src.label}={src_order})',
                ref=(owner, table))

    # --- indices ---------------------------------------------------
    def index_signature(sd, key):
        i = sd.index_by_key[key]
        return (i['INDEX_TYPE'], i['UNIQUENESS'],
                tuple(sd.index_columns.get(key, [])))

    def real_indexes(sd):
        return {k for k in sd.index_keys
                if (k[0], k[1]) not in sd.constraint_index_names}

    src_idx, dst_idx = real_indexes(src), real_indexes(dst)
    missing_indexes = sorted(k for k in src_idx - dst_idx
                             if (src.index_by_key[k]['TABLE_OWNER'],
                                 src.index_by_key[k]['TABLE_NAME']) in common_tables
                             or (src.index_by_key[k]['TABLE_OWNER'],
                                 src.index_by_key[k]['TABLE_NAME']) in src.table_keys)
    for k in missing_indexes:
        i = src.index_by_key[k]
        add('INDICE FALTANTE',
            f"{k[0]}.{k[1]} em {i['TABLE_OWNER']}.{i['TABLE_NAME']} "
            f"({', '.join(src.index_columns.get(k, []))}) existe em {src.label}, "
            f"ausente em {dst.label}", ref=k)

    for k in sorted(dst_idx - src_idx):
        i = dst.index_by_key[k]
        add('INDICE EXTRA',
            f"{k[0]}.{k[1]} em {i['TABLE_OWNER']}.{i['TABLE_NAME']} existe em {dst.label}, "
            f"ausente em {src.label}", ref=k)

    for k in sorted(src_idx & dst_idx):
        if index_signature(src, k) != index_signature(dst, k):
            add('INDICE DIVERGENTE',
                f'{k[0]}.{k[1]}: {dst.label}={index_signature(dst, k)} '
                f'vs {src.label}={index_signature(src, k)}', ref=k)

    # --- views: texto ----------------------------------------------
    def norm_sql(text):
        text = read_long(text)
        return " ".join(text.upper().split()) if text else None

    for v in sorted(src.view_keys & dst.view_keys):
        if norm_sql(src.view_text.get(v)) != norm_sql(dst.view_text.get(v)):
            add('VIEW DIVERGENTE',
                f'{v[0]}.{v[1]}: texto difere entre {src.label} e {dst.label}', ref=v)

    # --- PL/SQL ----------------------------------------------------
    for p in sorted(src.plsql_keys - dst.plsql_keys):
        add('PLSQL FALTANTE',
            f'{p[1]} {p[0]}.{p[2]} existe em {src.label}, ausente em {dst.label}', ref=p)

    for p in sorted(dst.plsql_keys - src.plsql_keys):
        add('PLSQL EXTRA',
            f'{p[1]} {p[0]}.{p[2]} existe em {dst.label}, ausente em {src.label}', ref=p)

    for p in sorted(src.plsql_keys & dst.plsql_keys):
        if src.plsql_hash[p] != dst.plsql_hash[p]:
            add('PLSQL DIVERGENTE',
                f'{p[1]} {p[0]}.{p[2]}: fonte difere '
                f'({dst.label}={dst.plsql_hash[p][0]} linhas vs '
                f'{src.label}={src.plsql_hash[p][0]} linhas)', ref=p)

    for o in dst.invalid_objects:
        add('OBJETO INVALIDO NO DESTINO',
            f"{o['OBJECT_TYPE']} {o['OWNER']}.{o['OBJECT_NAME']} esta {o['STATUS']} em {dst.label}")

    def named_constraints(sd):
        return {(c['OWNER'], c['TABLE_NAME'], c['CONSTRAINT_NAME'])
                for c in sd.constraints if not is_system_generated(c['CONSTRAINT_NAME'])}

    missing_cons = sorted(named_constraints(src) - named_constraints(dst))
    for c in missing_cons:
        # so reporta se a tabela ja existe nos dois (senao a constraint
        # falta so porque a tabela inteira falta - ja reportado acima)
        if (c[0], c[1]) in common_tables:
            add('CONSTRAINT FALTANTE', f'{c[0]}.{c[1]}.{c[2]} existe em {src.label}, ausente em {dst.label}',
                ref=c)

    return report, column_diffs


def print_report(report, out=sys.stdout):
    if not report:
        print("Nenhuma diferenca encontrada.", file=out)
        return
    by_section = defaultdict(list)
    for item in report:
        by_section[item['section']].append(item['msg'])
    order = ['TABELA FALTANTE', 'TABELA EXTRA', 'SEQUENCE FALTANTE',
             'VIEW FALTANTE', 'VIEW DIVERGENTE',
             'PLSQL FALTANTE', 'PLSQL EXTRA', 'PLSQL DIVERGENTE',
             'SINONIMO FALTANTE', 'COLUNA FALTANTE', 'COLUNA EXTRA', 'COLUNA DIVERGENTE',
             'ORDEM DE COLUNAS',
             'INDICE FALTANTE', 'INDICE EXTRA', 'INDICE DIVERGENTE',
             'CONSTRAINT FALTANTE', 'OBJETO INVALIDO NO DESTINO']
    for section in by_section:
        if section not in order:
            order.append(section)
    for section in order:
        if section not in by_section:
            continue
        print(f"\n=== {section} ({len(by_section[section])}) ===", file=out)
        for msg in by_section[section]:
            print(f"  - {msg}", file=out)


# ----------------------------------------------------------------------
# Geracao do script DDL (usa DBMS_METADATA.GET_DDL na origem para
# tabelas/sequences faltantes, ja sem STORAGE/TABLESPACE)
# ----------------------------------------------------------------------

def configure_metadata_session(conn):
    """Ajusta o DBMS_METADATA para nao trazer clausulas fisicas -
    equivalente a 'so estrutura logica' da convencao do usuario."""
    cur = conn.cursor()
    for param, value in [('STORAGE', False), ('TABLESPACE', False),
                          ('SEGMENT_ATTRIBUTES', False), ('SQLTERMINATOR', True),
                          ('PRETTY', True)]:
        cur.execute(
            "BEGIN DBMS_METADATA.SET_TRANSFORM_PARAM("
            "DBMS_METADATA.SESSION_TRANSFORM, :p, :v); END;",
            p=param, v=value)
    cur.close()


def get_table_ddl(conn, owner, table):
    cur = conn.cursor()
    cur.execute(
        "SELECT DBMS_METADATA.GET_DDL('TABLE', :t, :o) FROM dual",
        t=table, o=owner)
    (lob,) = cur.fetchone()
    ddl = lob.read() if hasattr(lob, 'read') else lob
    cur.close()
    return ddl.strip()


def get_object_ddl(conn, obj_type, owner, name):
    """GET_DDL generico, com mensagem de erro em comentario em vez de
    derrubar a execucao inteira (objeto pode ter dependencia quebrada)."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT DBMS_METADATA.GET_DDL(:k, :n, :o) FROM dual",
                    k=obj_type, n=name, o=owner)
        (lob,) = cur.fetchone()
        ddl = lob.read() if hasattr(lob, 'read') else lob
        cur.close()
        return ddl.strip()
    except Exception as exc:  # noqa: BLE001 - queremos seguir o resto
        return f"-- FALHA ao extrair DDL de {obj_type} {owner}.{name}: {exc}"


def emit_ddl(out, ddl, plsql=False):
    """Acrescenta o DDL a saida com o terminador certo - e sem
    terminador nenhum quando o GET_DDL falhou e devolveu comentario."""
    if ddl.lstrip().startswith('--'):
        out.append(ddl)
        return
    if plsql:
        out.append(ddl)
        out.append("/")
    else:
        out.append(ddl if ddl.rstrip().endswith(';') else ddl + ';')


def render_column_type(col):
    """Reconstroi a clausula de tipo a partir do dicionario, para o
    ALTER TABLE ... ADD de coluna faltante."""
    dt = col['DATA_TYPE']
    if dt in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR', 'RAW'):
        size = col.get('CHAR_LENGTH') or col.get('DATA_LENGTH')
        unit = ' CHAR' if col.get('CHAR_USED') == 'C' else ''
        clause = f"{dt}({size}{unit})"
    elif dt == 'NUMBER':
        p, s = col.get('DATA_PRECISION'), col.get('DATA_SCALE')
        if p is None:
            clause = 'NUMBER'
        elif s in (None, 0):
            clause = f"NUMBER({p})"
        else:
            clause = f"NUMBER({p},{s})"
    else:
        clause = dt
    default = default_literal(col.get('DATA_DEFAULT'))
    if default:
        clause += f" DEFAULT {default}"
    if col.get('NULLABLE') == 'N':
        clause += " NOT NULL"
    return clause


def build_add_column_statements(src: SchemaSnapshot, owner, table, columns):
    """Colunas novas entram sempre no fim da tabela - o Oracle nao
    permite escolher a posicao. Coluna NOT NULL sem default falha se a
    tabela ja tiver linhas, entao esse caso vira aviso."""
    lines = []
    for col in sorted(columns, key=lambda c: c['COLUMN_ID'] or 0):
        name = col['COLUMN_NAME']
        if col.get('NULLABLE') == 'N' and not default_literal(col.get('DATA_DEFAULT')):
            lines.append(f"-- ATENCAO: {name} e NOT NULL sem DEFAULT - o ADD falha se "
                         f"{owner}.{table} ja tiver linhas. Avalie adicionar como NULL, "
                         f"popular e so depois aplicar o NOT NULL.")
        lines.append(f"ALTER TABLE {owner}.{table} ADD ({name} {render_column_type(col)});")
        comment = src.col_comment.get((owner, table, name))
        if comment:
            lines.append(f"comment on column {owner}.{table}.{name} is\n"
                         f"'{strip_accents(comment)}';")
        lines.append("")
    return lines


def get_sequence_ddl_from_row(seq_row):
    """Sequences sao mais simples de reconstruir na mao a partir dos
    dados do dicionario do que via GET_DDL (evita herdar o valor atual
    de last_number como start with cru - somamos 1 para nao colidir
    com a proxima insercao da aplicacao)."""
    owner = seq_row['OWNER']
    name = seq_row['SEQUENCE_NAME']
    try:
        start = int(seq_row['LAST_NUMBER']) + 1
    except (TypeError, ValueError):
        start = 1
    cycle = 'cycle' if seq_row.get('CYCLE_FLAG') == 'Y' else 'nocycle'
    cache = seq_row.get('CACHE_SIZE')
    cache_clause = f"cache {cache}" if cache and str(cache) != '0' else 'nocache'
    return (f"create sequence {owner}.{name}\n"
            f"increment by {seq_row.get('INCREMENT_BY', 1)}\n"
            f"start with {start}\n"
            f"{cycle}\n"
            f"{cache_clause};")


def build_comment_statements(src: SchemaSnapshot, owner, table):
    lines = []
    tab_comment = src.tab_comment.get((owner, table))
    if tab_comment:
        lines.append(f"comment on table {owner}.{table} is\n'{strip_accents(tab_comment)}';")
    for (o, t, c), comment in src.col_comment.items():
        if o == owner and t == table:
            lines.append(f"comment on column {owner}.{table}.{c} is\n'{strip_accents(comment)}';")
    return "\n".join(lines)


def build_grant_statements(src: SchemaSnapshot, owner, table, service_user):
    """Gera GRANT so para o usuario de servico configurado no
    config.ini - ignora qualquer outra conta que aparece nos grants
    da origem (contas pessoais, integracoes pontuais, etc).

    Se a origem ja tiver grant registrado para esse usuario nessa
    tabela, replica exatamente os privilegios encontrados. Se nao
    houver nenhum registro (tabela nova, ainda sem grant em lugar
    nenhum), aplica um padrao so para tabelas de dado normal
    (DELETE,INSERT,SELECT,UPDATE - o padrao observado em praticamente
    toda tabela do schema); para tabelas de auditoria (schema
    terminado em _AUDIT ou nome comecando com H_TB_) o privilegio
    minimo varia bastante na pratica (algumas tem so INSERT,SELECT,
    outras tem tambem DELETE/UPDATE) - nesse caso o script NAO
    adivinha, so avisa com um TODO para voce decidir."""
    grants_by_grantee = defaultdict(set)
    for g in src.grants_by_table.get((owner, table), []):
        grants_by_grantee[g['GRANTEE'].upper()].add(g['PRIVILEGE'])

    privs = grants_by_grantee.get(service_user.upper())
    is_audit = owner.upper().endswith('_AUDIT') or table.upper().startswith('H_TB_')

    if privs:
        priv_list = ",".join(sorted(privs))
        return f"grant {priv_list} on {owner}.{table} to {service_user};"

    if is_audit:
        return (f"-- TODO: {owner}.{table} e tabela de auditoria e nao tem grant "
                f"registrado na origem para {service_user} - privilegio minimo "
                f"varia por tabela (algumas so INSERT,SELECT, outras tambem "
                f"DELETE,UPDATE). Confirme manualmente antes de aplicar:\n"
                f"-- grant INSERT,SELECT on {owner}.{table} to {service_user};")

    return f"grant DELETE,INSERT,SELECT,UPDATE on {owner}.{table} to {service_user};"


def build_synonym_statement(service_user, owner, name):
    return (f"create or replace synonym {service_user}.{name}\n"
            f"   for {owner}.{name};")


def refs_of(report, section):
    """Extrai as referencias (ref) de uma secao do relatorio."""
    return [item['ref'] for item in report
            if item['section'] == section and item['ref'] is not None]


def _header(schema, src_label, dst_label):
    out = []
    out.append("/*==============================================================*/")
    out.append(f"/* DIFF: {schema} - aplicar em {dst_label.upper()}"[:64].ljust(64) + "*/")
    out.append(f"/* Origem: {src_label} (conexao direta via DBMS_METADATA)"[:64].ljust(64) + "*/")
    out.append("/* Gerado automaticamente por oracle_diff.py - revise antes de     */")
    out.append("/* aplicar, principalmente nomes de constraint auto-gerados e      */")
    out.append("/* grants que dependam de usuario que so existe num dos ambientes. */")
    out.append("/*==============================================================*/\n")
    return out


def generate_ddl_scripts_by_schema(conn_src, src: SchemaSnapshot, dst: SchemaSnapshot,
                                    report, column_diffs, service_users=None):
    """Retorna um dict {schema: texto_do_script}, um script por schema
    comparado. Grants e sinonimos de objetos novos (tabela/sequence
    faltante) sao gerados SEMPRE para o usuario de servico configurado
    em service_users[schema] (config.ini, secao [usuarios_servico]) -
    nao para qualquer conta que aparecer nos grants/sinonimos da
    origem. Schema sem usuario de servico configurado nao recebe
    grant/sinonimo automatico, so o CREATE TABLE/CREATE SEQUENCE."""
    service_users = service_users or {}

    missing_tables = sorted(src.table_keys - dst.table_keys)
    missing_seq = sorted(src.seq_keys - dst.seq_keys)
    missing_syn = sorted(src.syn_keys - dst.syn_keys)
    missing_views = sorted(src.view_keys - dst.view_keys)
    diverging_views = sorted(ref for ref in refs_of(report, 'VIEW DIVERGENTE'))
    missing_plsql = sorted(src.plsql_keys - dst.plsql_keys)
    diverging_plsql = sorted(ref for ref in refs_of(report, 'PLSQL DIVERGENTE'))
    missing_indexes = sorted(refs_of(report, 'INDICE FALTANTE'))
    order_issues = sorted(refs_of(report, 'ORDEM DE COLUNAS'))

    # colunas faltantes em tabela que ja existe nos dois lados
    missing_cols = defaultdict(list)
    for owner, table, col in refs_of(report, 'COLUNA FALTANTE'):
        col_row = next((c for c in src.cols_by_table.get((owner, table), [])
                        if c['COLUMN_NAME'] == col), None)
        if col_row:
            missing_cols[(owner, table)].append(col_row)

    # constraints faltantes: PK/UK/CHECK vao no corpo, FK num bloco
    # final (depois que todas as tabelas e colunas ja existem)
    missing_cons_normal, missing_cons_fk = [], []
    for key in refs_of(report, 'CONSTRAINT FALTANTE'):
        cons = src.cons_by_key.get((key[0], key[2]))
        if not cons:
            continue
        (missing_cons_fk if cons['CONSTRAINT_TYPE'] == 'R'
         else missing_cons_normal).append(key)

    schemas = sorted(src.schemas)
    scripts = {}

    seq_by_key = {(s['OWNER'], s['SEQUENCE_NAME']): s for s in src.sequences}

    for schema in schemas:
        out = _header(schema, src.label, dst.label)
        wrote_anything = False
        service_user = service_users.get(schema)

        sch_missing_tables = [t for t in missing_tables if t[0] == schema]
        sch_missing_seq = [s for s in missing_seq if s[0] == schema]
        sch_column_diffs = [d for d in column_diffs if d[0] == schema]

        # nomes que ja vao ganhar sinonimo por serem objeto novo -
        # usado abaixo para nao duplicar aviso de sinonimo "faltante"
        # detectado por comparacao quando ja tratamos via objeto novo
        new_object_names = {t[1] for t in sch_missing_tables} | {s[1] for s in sch_missing_seq}

        if not service_user:
            out.append(f"-- AVISO: nenhum usuario de servico configurado para {schema} em "
                       f"[usuarios_servico] no config.ini - grants e sinonimos NAO foram "
                       f"gerados automaticamente para este schema.\n")

        if sch_missing_tables or sch_missing_seq:
            out.append("PROMPT ==========================================================")
            out.append("PROMPT DIAGNOSTICO - confirmar ausencia antes de criar")
            out.append("PROMPT ==========================================================")
            if sch_missing_tables:
                names = ",".join(f"'{t[1]}'" for t in sch_missing_tables)
                out.append("SELECT owner, table_name, status FROM dba_tables")
                out.append(f"WHERE owner = '{schema}' AND table_name IN ({names});")
                out.append("-- Esperado: 0 linhas.\n")
            if sch_missing_seq:
                names = ",".join(f"'{s[1]}'" for s in sch_missing_seq)
                out.append("SELECT sequence_owner, sequence_name FROM dba_sequences")
                out.append(f"WHERE sequence_owner = '{schema}' AND sequence_name IN ({names});")
                out.append("-- Esperado: 0 linhas.\n")
            wrote_anything = True

        if sch_missing_seq:
            out.append("/*==============================================================*/")
            out.append("/* Sequences                                                      */")
            out.append("/*==============================================================*/")
            for key in sch_missing_seq:
                out.append(get_sequence_ddl_from_row(seq_by_key[key]))
                out.append("")
                if service_user:
                    out.append(f"grant SELECT on {schema}.{key[1]} to {service_user};")
                    out.append(build_synonym_statement(service_user, schema, key[1]))
                    out.append("")
            wrote_anything = True

        for owner, table in sch_missing_tables:
            out.append("/*==============================================================*/")
            out.append(f"/* Table: {table}"[:64].ljust(64) + "*/")
            out.append("/*==============================================================*/")
            ddl = get_table_ddl(conn_src, owner, table)
            out.append(ddl if ddl.rstrip().endswith(';') else ddl + ';')
            out.append("")
            comments = build_comment_statements(src, owner, table)
            if comments:
                out.append(comments)
                out.append("")
            if service_user:
                out.append(build_grant_statements(src, owner, table, service_user))
                out.append("")
                out.append(build_synonym_statement(service_user, owner, table))
                out.append("")
            wrote_anything = True

        sch_missing_cols = {k: v for k, v in missing_cols.items() if k[0] == schema}
        if sch_missing_cols:
            out.append("/*==============================================================*/")
            out.append("/* Colunas faltantes em tabela existente                          */")
            out.append("/*==============================================================*/")
            for (owner, table), cols in sorted(sch_missing_cols.items()):
                out.extend(build_add_column_statements(src, owner, table, cols))
            wrote_anything = True

        if sch_column_diffs:
            out.append("/*==============================================================*/")
            out.append("/* Ajustes de coluna (DEFAULT / NOT NULL / tipo) - REVISAR       */")
            out.append("/* Direcao assumida: destino se alinha a origem.                  */")
            out.append("/*==============================================================*/")
            for owner, table, col, src_col, dst_col in sch_column_diffs:
                src_null = src_col.get('NULLABLE')
                dst_null = dst_col.get('NULLABLE')
                same_type = (src_col.get('DATA_TYPE'), src_col.get('DATA_LENGTH'),
                             src_col.get('DATA_PRECISION'), src_col.get('DATA_SCALE')) == \
                            (dst_col.get('DATA_TYPE'), dst_col.get('DATA_LENGTH'),
                             dst_col.get('DATA_PRECISION'), dst_col.get('DATA_SCALE'))
                src_def = norm_default(src_col.get('DATA_DEFAULT'))
                dst_def = norm_default(dst_col.get('DATA_DEFAULT'))

                if not same_type:
                    out.append(f"-- {owner}.{table}.{col}: divergencia de TIPO/TAMANHO - "
                                f"revisar manualmente (destino={col_signature(dst_col)} "
                                f"origem={col_signature(src_col)})")
                    if src_def != dst_def or src_null != dst_null:
                        out.append("-- (default/nullable tambem divergem - tratar junto com o tipo)")
                    out.append("")
                    continue

                if src_def != dst_def:
                    literal = default_literal(src_col.get('DATA_DEFAULT'))
                    out.append(f"-- {owner}.{table}.{col}: default diverge "
                                f"({dst.label}={dst_def or 'sem default'} vs "
                                f"{src.label}={src_def or 'sem default'})")
                    out.append("-- OBS: DEFAULT so vale para linhas novas - nao altera dado ja gravado.")
                    if literal:
                        out.append(f"ALTER TABLE {owner}.{table} MODIFY ({col} DEFAULT {literal});")
                    else:
                        out.append(f"ALTER TABLE {owner}.{table} MODIFY ({col} DEFAULT NULL);")
                    out.append("")

                if src_null != dst_null:
                    new_state = 'NULL' if src_null == 'Y' else 'NOT NULL'
                    out.append(f"-- {owner}.{table}.{col}: nullable diverge ({dst.label}={dst_null} "
                                f"vs {src.label}={src_null})")
                    if new_state == 'NOT NULL':
                        out.append("-- ATENCAO: checar dados com NULL antes de aplicar NOT NULL:")
                        out.append(f"-- SELECT COUNT(*) FROM {owner}.{table} WHERE {col} IS NULL;")
                    out.append(f"ALTER TABLE {owner}.{table} MODIFY ({col} {new_state});\n")
            wrote_anything = True

        # --- indices (depois de tabelas e colunas existirem) --------
        sch_indexes = [k for k in missing_indexes if k[0] == schema]
        if sch_indexes:
            out.append("/*==============================================================*/")
            out.append("/* Indices faltantes                                              */")
            out.append("/*==============================================================*/")
            for owner, name in sch_indexes:
                info = src.index_by_key[(owner, name)]
                out.append(f"-- {owner}.{name} em {info['TABLE_OWNER']}.{info['TABLE_NAME']} "
                           f"({', '.join(src.index_columns.get((owner, name), []))})")
                emit_ddl(out, get_object_ddl(conn_src, 'INDEX', owner, name))
                out.append("")
            wrote_anything = True

        # --- constraints nao-FK ------------------------------------
        sch_cons = [k for k in missing_cons_normal if k[0] == schema]
        if sch_cons:
            out.append("/*==============================================================*/")
            out.append("/* Constraints faltantes (PK / UK / CHECK)                        */")
            out.append("/*==============================================================*/")
            for owner, table, name in sch_cons:
                out.append(f"-- {owner}.{table}.{name}")
                emit_ddl(out, get_object_ddl(conn_src, 'CONSTRAINT', owner, name))
                out.append("")
            wrote_anything = True

        # --- views --------------------------------------------------
        sch_views_new = [v for v in missing_views if v[0] == schema]
        sch_views_diff = [v for v in diverging_views if v[0] == schema]
        if sch_views_new or sch_views_diff:
            out.append("/*==============================================================*/")
            out.append("/* Views - CREATE OR REPLACE a partir da origem                   */")
            out.append("/*==============================================================*/")
            for owner, name in sch_views_new + sch_views_diff:
                marca = 'ausente no destino' if (owner, name) in missing_views else 'texto divergente'
                out.append(f"-- {owner}.{name} ({marca})")
                emit_ddl(out, get_object_ddl(conn_src, 'VIEW', owner, name))
                out.append("")
                if service_user and (owner, name) in missing_views:
                    out.append(f"grant SELECT on {owner}.{name} to {service_user};")
                    out.append(build_synonym_statement(service_user, owner, name))
                    out.append("")
            wrote_anything = True

        # --- PL/SQL -------------------------------------------------
        sch_plsql = [p for p in missing_plsql + diverging_plsql if p[0] == schema]
        if sch_plsql:
            out.append("/*==============================================================*/")
            out.append("/* PL/SQL - REVISAR: sobrescreve o objeto no destino              */")
            out.append("/*==============================================================*/")
            for owner, obj_type, name in sch_plsql:
                marca = 'ausente no destino' if (owner, obj_type, name) in missing_plsql \
                        else 'fonte divergente'
                out.append(f"-- {obj_type} {owner}.{name} ({marca})")
                emit_ddl(out, get_object_ddl(conn_src, obj_type.replace(' ', '_'), owner, name),
                         plsql=True)
                out.append("")
            wrote_anything = True

        # --- ordem de colunas (so aviso, nao ha DDL seguro) ---------
        sch_order = [o for o in order_issues if o[0] == schema]
        if sch_order:
            out.append("/*==============================================================*/")
            out.append("/* Ordem fisica das colunas diverge - NAO ha ALTER que reordene.  */")
            out.append("/* Impacto: INSERT sem lista de colunas e SELECT *. Corrigir      */")
            out.append("/* exige recriar a tabela (CTAS + rename) em janela controlada.   */")
            out.append("/*==============================================================*/")
            for owner, table in sch_order:
                out.append(f"-- {owner}.{table}: conferir ordem no relatorio de diferencas")
            out.append("")
            wrote_anything = True

        # Sinonimos que a comparacao encontrou faltando na origem mas
        # que NAO correspondem a um objeto novo ja tratado acima - ou
        # sao para um dono diferente do usuario de servico, ou apontam
        # para objeto que pode nem existir de verdade (ver o caso
        # TB_HISTORICO_SITUACAO_PF: sinonimo orfao na propria origem).
        # Aqui so avisa, nao cria - decisao fica com quem revisa.
        sch_missing_syn = [s for s in missing_syn if src.syn_target[s][0] == schema]
        leftover_syn = [s for s in sch_missing_syn
                        if src.syn_target[s][1] not in new_object_names
                        and (not service_user or s[0].upper() != service_user.upper())]
        if leftover_syn:
            out.append("/*==============================================================*/")
            out.append("/* Sinonimos faltantes NAO tratados automaticamente - revisar     */")
            out.append("/* (dono diferente do usuario de servico configurado, ou aponta   */")
            out.append("/* para objeto que precisa ser confirmado antes de criar)         */")
            out.append("/*==============================================================*/")
            for owner, syn in leftover_syn:
                target = src.syn_target[(owner, syn)]
                out.append(f"-- {owner}.{syn} -> {target[0]}.{target[1]} (existe em {src.label}, "
                           f"ausente em {dst.label} - confirme se {target[0]}.{target[1]} "
                           f"existe de fato antes de criar)")
            out.append("")
            wrote_anything = True

        # --- FKs por ultimo: dependem de todas as tabelas e das PKs
        # referenciadas ja existirem. Se a tabela pai estiver em outro
        # schema, aplique os scripts na ordem e este bloco por ultimo.
        sch_fk = [k for k in missing_cons_fk if k[0] == schema]
        if sch_fk:
            out.append("/*==============================================================*/")
            out.append("/* Foreign keys - aplicar POR ULTIMO                              */")
            out.append("/* (depende das tabelas e das PKs referenciadas ja existirem;     */")
            out.append("/* se a tabela pai fica em outro schema, rode aquele script antes)*/")
            out.append("/*==============================================================*/")
            for owner, table, name in sch_fk:
                cons = src.cons_by_key.get((owner, name), {})
                ref = src.cons_by_key.get((cons.get('R_OWNER'), cons.get('R_CONSTRAINT_NAME')), {})
                alvo = f"{ref.get('OWNER', '?')}.{ref.get('TABLE_NAME', '?')}"
                out.append(f"-- {owner}.{table}.{name} -> {alvo}")
                out.append(f"-- confirme que {alvo} existe no destino antes de aplicar")
                emit_ddl(out, get_object_ddl(conn_src, 'REF_CONSTRAINT', owner, name))
                out.append("")
            wrote_anything = True

        if wrote_anything:
            scripts[schema] = "\n".join(out)

    return scripts


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--config', default='config.ini', help='arquivo de configuracao (default: config.ini)')
    ap.add_argument('--report', default=None, help='arquivo de saida do relatorio (default: stdout)')
    ap.add_argument('--ddl', default=None,
                     help='nome base do script DDL a aplicar no destino - '
                          'um arquivo e gerado POR SCHEMA, com o nome do '
                          'schema inserido antes da extensao '
                          '(ex.: --ddl diff.sql gera diff_ATURMA100.sql, '
                          'diff_ATURMA100_AUDIT.sql, etc.)')
    args = ap.parse_args()

    cfg = load_config(args.config)
    schemas = [s.strip() for s in cfg['opcoes']['schemas'].split(',')]
    prefix = view_prefix(cfg)

    service_users = {}
    if cfg.has_section('usuarios_servico'):
        service_users = {k.upper(): v.strip() for k, v in cfg['usuarios_servico'].items()}

    conn_src, label_src = connect(cfg, 'origem')
    conn_dst, label_dst = connect(cfg, 'destino')

    print(f"Extraindo metadados de {label_src}...", file=sys.stderr)
    src = SchemaSnapshot(conn_src, label_src, schemas, prefix)
    print(f"Extraindo metadados de {label_dst}...", file=sys.stderr)
    dst = SchemaSnapshot(conn_dst, label_dst, schemas, prefix)

    report, column_diffs = compare(src, dst)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.report:
        rep_dir, rep_file = os.path.split(args.report)
        report_path = os.path.join(rep_dir, f"{timestamp}_{rep_file}")
        with open(report_path, 'w', encoding='utf-8') as f:
            print_report(report, out=f)
        print(f"Relatorio gravado em {report_path}")
    else:
        print_report(report)

    if args.ddl:
        configure_metadata_session(conn_src)
        scripts = generate_ddl_scripts_by_schema(conn_src, src, dst, report, column_diffs,
                                                  service_users=service_users)
        if not scripts:
            print("Nenhuma diferenca para gerar script (todos os schemas ja batem).")
        base, ext = os.path.splitext(args.ddl)
        ext = ext or '.sql'
        base_name = os.path.basename(base)
        for schema, ddl_text in scripts.items():
            # pasta com o nome do schema - se ja existir, so usa (nao recria)
            os.makedirs(schema, exist_ok=True)
            out_path = os.path.join(schema, f"{timestamp}_{base_name}_{schema}{ext}")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(ddl_text)
            print(f"Script DDL de {schema} gravado em {out_path}")

    conn_src.close()
    conn_dst.close()


if __name__ == '__main__':
    main()