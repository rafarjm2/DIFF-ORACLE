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

Opcoes em [opcoes] do config.ini (todas opcionais):
    ignorar_objetos_sys = true    # ignora constraints/indices do SYS/SYSTEM e
                                  # de nome SYS_* (SYS_C, SYS_IL, SYS_NC...)

    script_idempotente  = true    # cada CREATE/ADD do script sai dentro de um bloco
                                  # PL/SQL que consulta DBA_* antes (roda 2x sem erro)

    gerar_drop_coluna   = false   # coluna que so existe no DESTINO: false = DROP COLUMN
                                  # sai COMENTADO no fim do script; true = sai ativo

    detectar_rename_tabela = true # tabela que falta no destino + tabela que so existe
                                  # no destino com colunas parecidas = RENAME (nao CREATE)

Constraints: alem de faltante, o relatorio aponta a de MESMO NOME com definicao
diferente (colunas, condicao do CHECK, tabela/colunas/ON DELETE da FK), com status
diferente (ENABLED/DISABLED) e a que so existe no destino. Definicao diferente e
"so no destino" saem COMENTADOS no script; status sai como ENABLE/DISABLE.

PK/UK/CHECK/FK/INDICE que existem nos dois bancos com a mesma definicao mas
nome diferente NAO geram CREATE (duplicaria o objeto): aparecem no relatorio
e no script como ALTER ... RENAME comentado, para voce decidir.

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


def schema_list_bind(schemas, prefix='s'):
    """Gera a clausula IN (:s0, :s1, ...) e o dict de binds."""
    placeholders = ", ".join(f":{prefix}{i}" for i in range(len(schemas)))
    binds = {f"{prefix}{i}": s.strip() for i, s in enumerate(schemas)}
    return placeholders, binds


class SchemaSnapshot:
    """Consulta um banco vivo e guarda tudo que precisamos comparar."""

    def __init__(self, conn, label, schemas, prefix, service_users=None):
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

        # O sinonimo pertence ao schema de SERVICO (ex.: ATURMAUSR), nao ao
        # schema de dados. Buscar so por table_owner deixava de enxergar o
        # sinonimo do destino quando ele aponta para outro dono (ex.: um
        # schema de outro ambiente) e o script o dava como "faltante".
        svc = sorted({u.strip() for u in (service_users or []) if u and u.strip()})
        syn_where = f"table_owner IN ({ph})"
        syn_binds = dict(binds)
        if svc:
            ph_svc, b_svc = schema_list_bind(svc, 'u')
            syn_where += f" OR owner IN ({ph_svc})"
            syn_binds.update(b_svc)
        self.synonyms = fetch_all(conn, f"""
            SELECT owner, synonym_name, table_owner, table_name
            FROM   {prefix}_synonyms
            WHERE  {syn_where}
        """, syn_binds)

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


SYS_OWNERS = ('SYS', 'SYSTEM')


def is_sys_object(owner, name):
    """Objeto do proprio Oracle: dono SYS/SYSTEM ou nome SYS_* (SYS_C,
    SYS_IL, SYS_NC, SYS_IOT...). Nao entra em faltante/extra/divergente."""
    return ((owner or '').upper() in SYS_OWNERS
            or (name or '').upper().startswith('SYS_'))


def norm_cond(text):
    """Condicao de CHECK sem diferenca de espaco/caixa."""
    text = read_long(text)
    return " ".join(text.upper().split()) if text else None


def _cols_of(sd, owner, cname):
    cols = sorted(sd.cons_cols_by_key.get((owner, cname), []), key=lambda x: x['POSITION'] or 0)
    return tuple(x['COLUMN_NAME'] for x in cols)


def cons_signature(sd, c):
    """Definicao da constraint independente do nome. None para tipos nao tratados.
    P/U: colunas | C: condicao | R: colunas, tabela+colunas referenciadas, ON DELETE."""
    t = c['CONSTRAINT_TYPE']
    if t in ('P', 'U'):
        return (t, c['TABLE_NAME'], _cols_of(sd, c['OWNER'], c['CONSTRAINT_NAME']))
    if t == 'C':
        return (t, c['TABLE_NAME'], norm_cond(c.get('SEARCH_CONDITION_VC')))
    if t == 'R':
        ref = sd.cons_by_key.get((c['R_OWNER'], c['R_CONSTRAINT_NAME']))
        if ref:
            alvo = (ref['OWNER'], ref['TABLE_NAME'], _cols_of(sd, ref['OWNER'], ref['CONSTRAINT_NAME']))
        else:  # pai fora dos schemas comparados: compara pelo nome da PK/UK referenciada
            alvo = (c['R_OWNER'], c['R_CONSTRAINT_NAME'], ())
        return (t, c['TABLE_NAME'], _cols_of(sd, c['OWNER'], c['CONSTRAINT_NAME']),
                alvo, c.get('DELETE_RULE'))
    return None


def sig_text(sig):
    """Texto curto da definicao, para relatorio e script."""
    if not sig:
        return ''
    t = sig[0]
    if t in ('P', 'U'):
        return ', '.join(sig[2])
    if t == 'C':
        return sig[2] or ''
    alvo = sig[3]
    return (f"({', '.join(sig[2])}) -> {alvo[0]}.{alvo[1]}({', '.join(alvo[2])}) "
            f"ON DELETE {sig[4] or 'NO ACTION'}")


def compare(src: SchemaSnapshot, dst: SchemaSnapshot, ignore_sys=True):
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

    for s_key in sorted(src.syn_keys & dst.syn_keys):
        t_src, t_dst = src.syn_target.get(s_key), dst.syn_target.get(s_key)
        if t_src != t_dst:
            add('SINONIMO DIVERGENTE',
                f'{s_key[0]}.{s_key[1]}: {dst.label} aponta para {t_dst[0]}.{t_dst[1]} '
                f'vs {src.label} para {t_src[0]}.{t_src[1]}',
                ref=(s_key, t_src, t_dst))

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
                if (k[0], k[1]) not in sd.constraint_index_names
                and not (ignore_sys and is_sys_object(k[0], k[1]))}

    def index_full_sig(sd, key):
        i = sd.index_by_key[key]
        return (i['TABLE_OWNER'], i['TABLE_NAME']) + index_signature(sd, key)

    src_idx, dst_idx = real_indexes(src), real_indexes(dst)
    missing_indexes = sorted(k for k in src_idx - dst_idx
                             if (src.index_by_key[k]['TABLE_OWNER'],
                                 src.index_by_key[k]['TABLE_NAME']) in src.table_keys)

    # indice equivalente no destino, so com nome diferente: nao cria
    # (duplicaria a coluna indexada), so avisa e deixa o RENAME comentado
    idx_candidates = defaultdict(list)
    for k in sorted(dst_idx - src_idx):
        if k not in src.index_keys:
            idx_candidates[index_full_sig(dst, k)].append(k)
    renamed_src, renamed_dst = set(), set()
    for k in list(missing_indexes):
        pool = idx_candidates.get(index_full_sig(src, k))
        if not pool:
            continue
        dk = pool.pop(0)
        renamed_src.add(k)
        renamed_dst.add(dk)
        i = src.index_by_key[k]
        cols = ', '.join(src.index_columns.get(k, []))
        add('INDICE COM NOME DIFERENTE',
            f"{i['TABLE_OWNER']}.{i['TABLE_NAME']} ({cols}): {dst.label}={dk[1]} "
            f"vs {src.label}={k[1]} (mesma definicao, so o nome difere)",
            ref=('INDEX', k[0], i['TABLE_NAME'], dk[1], k[1], cols,
                 k in dst.index_keys))

    for k in missing_indexes:
        if k in renamed_src:
            continue
        i = src.index_by_key[k]
        add('INDICE FALTANTE',
            f"{k[0]}.{k[1]} em {i['TABLE_OWNER']}.{i['TABLE_NAME']} "
            f"({', '.join(src.index_columns.get(k, []))}) existe em {src.label}, "
            f"ausente em {dst.label}", ref=k)

    for k in sorted(dst_idx - src_idx):
        if k in renamed_dst:
            continue
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
                for c in sd.constraints
                if not is_system_generated(c['CONSTRAINT_NAME'])
                and not (ignore_sys and is_sys_object(c['OWNER'], c['CONSTRAINT_NAME']))}

    src_all_names = {(c['OWNER'], c['TABLE_NAME'], c['CONSTRAINT_NAME']) for c in src.constraints}
    src_named, dst_named = named_constraints(src), named_constraints(dst)
    missing_cons = [c for c in sorted(src_named - dst_named)
                    # so reporta se a tabela ja existe nos dois (senao a constraint
                    # falta so porque a tabela inteira falta - ja reportado acima)
                    if (c[0], c[1]) in common_tables]

    # candidatas no destino: PK/UK/CHECK/FK cujo nome nao existe na origem. Inclui as
    # de nome SYS_C, que sao o caso classico de "mesma regra, nome diferente".
    cons_candidates = defaultdict(list)
    for c in sorted(dst.constraints, key=lambda x: (x['OWNER'], x['TABLE_NAME'], x['CONSTRAINT_NAME'])):
        if (c['OWNER'], c['TABLE_NAME'], c['CONSTRAINT_NAME']) in src_all_names:
            continue
        sig = cons_signature(dst, c)
        if sig:
            cons_candidates[(c['OWNER'],) + sig].append(c)

    tipo_txt = {'P': 'PK', 'U': 'UK', 'C': 'CHECK', 'R': 'FK'}
    consumed_dst = set()
    for c in missing_cons:
        sc = src.cons_by_key.get((c[0], c[2]))
        sig = cons_signature(src, sc) if sc else None
        pool = cons_candidates.get((c[0],) + sig) if sig else None
        if pool:
            dc = pool.pop(0)
            consumed_dst.add((dc['OWNER'], dc['TABLE_NAME'], dc['CONSTRAINT_NAME']))
            detalhe = sig_text(sig)
            add('CONSTRAINT COM NOME DIFERENTE',
                f"{tipo_txt[sc['CONSTRAINT_TYPE']]} {c[0]}.{c[1]} ({detalhe}): "
                f"{dst.label}={dc['CONSTRAINT_NAME']} vs {src.label}={c[2]} "
                f"(mesma definicao, so o nome difere)",
                ref=(sc['CONSTRAINT_TYPE'], c[0], c[1], dc['CONSTRAINT_NAME'], c[2], detalhe,
                     (c[0], c[2]) in dst.cons_by_key))
        else:
            add('CONSTRAINT FALTANTE', f'{c[0]}.{c[1]}.{c[2]} existe em {src.label}, ausente em {dst.label}',
                ref=c)

    # mesmo nome nos dois lados: definicao ou status diferentes
    for k in sorted(src_named & dst_named):
        if (k[0], k[1]) not in common_tables:
            continue
        sc, dc = src.cons_by_key.get((k[0], k[2])), dst.cons_by_key.get((k[0], k[2]))
        if not sc or not dc:
            continue
        ss, ds = cons_signature(src, sc), cons_signature(dst, dc)
        rot = tipo_txt.get(sc['CONSTRAINT_TYPE'], sc['CONSTRAINT_TYPE'])
        if ss and ds and ss != ds:
            add('CONSTRAINT DIVERGENTE',
                f"{rot} {k[0]}.{k[1]}.{k[2]}: {dst.label}=[{sig_text(ds)}] "
                f"vs {src.label}=[{sig_text(ss)}]",
                ref=(k[0], k[1], k[2], sc['CONSTRAINT_TYPE'], sig_text(ss), sig_text(ds)))
        if sc['STATUS'] != dc['STATUS']:
            add('CONSTRAINT STATUS DIVERGENTE',
                f"{rot} {k[0]}.{k[1]}.{k[2]}: {dst.label}={dc['STATUS']} vs {src.label}={sc['STATUS']}",
                ref=(k[0], k[1], k[2], sc['CONSTRAINT_TYPE'], sc['STATUS'], dc['STATUS']))

    # so no destino (sem equivalente por definicao em outro nome)
    for k in sorted(dst_named - src_named):
        if k in consumed_dst or (k[0], k[1]) not in common_tables:
            continue
        dc = dst.cons_by_key.get((k[0], k[2]))
        if not dc:
            continue
        sig = cons_signature(dst, dc)
        add('CONSTRAINT EXTRA',
            f"{tipo_txt.get(dc['CONSTRAINT_TYPE'], dc['CONSTRAINT_TYPE'])} {k[0]}.{k[1]}.{k[2]}"
            f"{' (' + sig_text(sig) + ')' if sig else ''} existe em {dst.label}, ausente em {src.label}",
            ref=(k[0], k[1], k[2], dc['CONSTRAINT_TYPE'], sig_text(sig)))

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
             'SINONIMO FALTANTE', 'SINONIMO DIVERGENTE', 'COLUNA FALTANTE', 'COLUNA EXTRA', 'COLUNA DIVERGENTE',
             'ORDEM DE COLUNAS',
             'INDICE FALTANTE', 'INDICE EXTRA', 'INDICE DIVERGENTE', 'INDICE COM NOME DIFERENTE',
             'CONSTRAINT FALTANTE', 'CONSTRAINT COM NOME DIFERENTE', 'CONSTRAINT DIVERGENTE',
             'CONSTRAINT STATUS DIVERGENTE', 'CONSTRAINT EXTRA', 'OBJETO INVALIDO NO DESTINO']
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


def q_literal(text):
    """Literal q'..' com delimitador que nao aparece no texto (DDL tem aspas)."""
    for ini, fim in (('[', ']'), ('{', '}'), ('<', '>'), ('(', ')'), ('!', '!'), ('~', '~')):
        if f"{fim}'" not in text:
            return f"q'{ini}{text}{fim}'"
    return "'" + text.replace("'", "''") + "'"


def guarded_text(stmt, check_sql, label, run_if_zero=True, idem=True):
    """Bloco PL/SQL idempotente: consulta o dicionario e so executa o DDL quando
    preciso (run_if_zero=True: cria se a contagem for 0; False: altera se > 0).
    Erro inesperado expoe SQLCODE/SQLERRM e re-levanta (nunca engole)."""
    stmt = stmt.strip().rstrip(';').strip()
    if not idem:
        return stmt + ';'
    cond = '= 0' if run_if_zero else '> 0'
    lab = label.replace("'", "''")
    return (
        "DECLARE\n"
        "  v_qtd NUMBER;\n"
        "BEGIN\n"
        f"  {check_sql.replace('SELECT COUNT(*) FROM', 'SELECT COUNT(*) INTO v_qtd FROM', 1)};\n"
        f"  IF v_qtd {cond} THEN\n"
        f"    EXECUTE IMMEDIATE {q_literal(stmt)};\n"
        f"    DBMS_OUTPUT.PUT_LINE('APLICADO: {lab}');\n"
        "  ELSE\n"
        f"    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): {lab}');\n"
        "  END IF;\n"
        "EXCEPTION\n"
        "  WHEN OTHERS THEN\n"
        f"    DBMS_OUTPUT.PUT_LINE('ERRO em {lab}: ' || SQLCODE || ' - ' || SQLERRM);\n"
        "    RAISE;\n"
        "END;\n"
        "/")


def emit_guarded(out, ddl, check_sql, label, idem=True, run_if_zero=True):
    """Como emit_ddl, mas com o DDL protegido por consulta ao dicionario."""
    if ddl.lstrip().startswith('--'):
        out.append(ddl)
        return
    out.append(guarded_text(ddl, check_sql, label, run_if_zero, idem))


def comment_out(text):
    """Comenta um DDL inteiro linha a linha."""
    return "\n".join(l if l.lstrip().startswith('--') else f"-- {l}" for l in text.splitlines())


def diag_in(out, head, where, expr, literals):
    """SELECT de diagnostico em blocos de 500 (limite de 1000 do IN no Oracle)."""
    for i in range(0, len(literals), 500):
        out.append(head)
        out.append(f"{where} AND {expr} IN ({','.join(literals[i:i + 500])});")
    out.append("-- Esperado: 0 linhas.\n")


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


def build_add_column_statements(src: SchemaSnapshot, owner, table, columns, idem=False):
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
        add_stmt = f"ALTER TABLE {owner}.{table} ADD ({name} {render_column_type(col)});"
        lines.append(guarded_text(
            add_stmt,
            f"SELECT COUNT(*) FROM dba_tab_columns WHERE owner = '{owner}' "
            f"AND table_name = '{table}' AND column_name = '{name}'",
            f"ADD COLUMN {owner}.{table}.{name}", True, idem))
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


def build_synonym_statement(service_user, owner, name, target_name=None):
    """Sinonimo privado, com dono no schema do usuario de servico."""
    target_name = target_name or name
    return (f"create or replace synonym {service_user}.{name}\n"
            f"   for {owner}.{target_name};")


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
    out.append("SET DEFINE OFF")
    out.append("SET SERVEROUTPUT ON")
    out.append("SET SQLBLANKLINES ON\n")
    return out


def col_type_sig(c):
    return (c.get('DATA_TYPE'), c.get('DATA_LENGTH'), c.get('DATA_PRECISION'), c.get('DATA_SCALE'))


def pk_columns(sd, owner, table):
    """Colunas da PK da tabela (tupla vazia se nao houver)."""
    for (o, name), c in sd.cons_by_key.items():
        if o == owner and c.get('TABLE_NAME') == table and c.get('CONSTRAINT_TYPE') == 'P':
            return _cols_of(sd, owner, name)
    return ()


def fk_target_table(sd, owner, table, column):
    """Tabela referenciada por FK de coluna unica nessa coluna (ou None)."""
    for (o, name), c in sd.cons_by_key.items():
        if (o == owner and c.get('TABLE_NAME') == table and c.get('CONSTRAINT_TYPE') == 'R'
                and _cols_of(sd, owner, name) == (column,)):
            ref = sd.cons_by_key.get((c.get('R_OWNER'), c.get('R_CONSTRAINT_NAME')), {})
            return (ref.get('OWNER'), ref.get('TABLE_NAME'))
    return None


def pair_columns_common_table(src, dst, owner, table, only_new, only_old, table_renames,
                              min_name_ratio=0.8):
    """Coluna renomeada em tabela que existe nos dois lados. So pareia quando:
      1. as duas sao FK para a MESMA tabela logica (a tabela referenciada foi
         renomeada e o par esta em table_renames) - ex.: ID_RELATORIO_VISTORIA
         -> ID_VISTORIA_PROCESSO na TB_SECAO_CONFORMIDADE_VISTORIA;
      2. nomes muito parecidos (>= 80%) e mesmo tipo, par unico.
    Retorna [(coluna_antiga, coluna_nova)]."""
    import difflib
    new_cols = {c['COLUMN_NAME']: c for c in src.cols_by_table.get((owner, table), [])}
    old_cols = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get((owner, table), [])}
    pairs, used_new, used_old = [], set(), set()
    for nc in only_new:
        t_new = fk_target_table(src, owner, table, nc)
        if not t_new:
            continue
        for oc in only_old:
            if oc in used_old or col_type_sig(new_cols[nc]) != col_type_sig(old_cols[oc]):
                continue
            t_old = fk_target_table(dst, owner, table, oc)
            if t_old and (t_new == t_old or table_renames.get(t_new) == t_old):
                pairs.append((oc, nc))
                used_new.add(nc)
                used_old.add(oc)
                break
    cands = []
    for nc in only_new:
        for oc in only_old:
            if nc in used_new or oc in used_old:
                continue
            if col_type_sig(new_cols[nc]) != col_type_sig(old_cols[oc]):
                continue
            ratio = difflib.SequenceMatcher(None, oc, nc).ratio()
            if ratio >= min_name_ratio:
                cands.append((ratio, oc, nc))
    for ratio, oc, nc in sorted(cands, reverse=True):
        if oc in used_old or nc in used_new:
            continue
        rivals = [r for r, o, n in cands if (o == oc or n == nc) and (o, n) != (oc, nc)]
        if rivals and max(rivals) == ratio:
            continue
        pairs.append((oc, nc))
        used_old.add(oc)
        used_new.add(nc)
    return pairs


def pair_renamed_columns(src, dst, owner, new_table, old_table, only_new, only_old,
                         min_name_ratio=0.8, pk_choice=None):
    """Pareia colunas renomeadas entre a tabela antiga (destino) e a nova
    (origem). Regra conservadora - so pareia quando e seguro:
      1. PK de coluna unica dos dois lados, mesmo tipo (ex.: ID_RELATORIO_VISTORIA
         -> ID_VISTORIA_PROCESSO);
      2. nomes muito parecidos (>= 80%) e mesmo tipo, par unico
         (ex.: NR_MATRICULA_USUARIO_FINALIZAC -> NR_MATRICULA_USUARIO_FINALIZACAO).
    Mesmo tipo com nome diferente (ex.: ID_PROCESSO_BANCARIO x ID_PLANO_SEGURANCA)
    NAO e renome automatico: pode ser troca de vinculo, que exige migrar dado.
    Retorna [(coluna_antiga, coluna_nova)]."""
    import difflib
    new_cols = {c['COLUMN_NAME']: c for c in src.cols_by_table.get((owner, new_table), [])}
    old_cols = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get((owner, old_table), [])}
    pairs, used_new, used_old = [], set(), set()

    pk_new = pk_columns(src, owner, new_table)
    pk_old = pk_columns(dst, owner, old_table)
    if pk_choice is False:          # usuario recusou o rename da PK
        pk_new = pk_old = ()
    elif pk_choice:                 # usuario confirmou o par
        o_pk, n_pk = pk_choice
        if n_pk in only_new and o_pk in only_old:
            pairs.append((o_pk, n_pk))
            used_new.add(n_pk)
            used_old.add(o_pk)
        pk_new = pk_old = ()
    if (len(pk_new) == 1 and len(pk_old) == 1 and pk_new[0] in only_new and pk_old[0] in only_old
            and col_type_sig(new_cols[pk_new[0]]) == col_type_sig(old_cols[pk_old[0]])):
        pairs.append((pk_old[0], pk_new[0]))
        used_new.add(pk_new[0])
        used_old.add(pk_old[0])

    cands = []
    for nc in only_new:
        for oc in only_old:
            if nc in used_new or oc in used_old:
                continue
            if col_type_sig(new_cols[nc]) != col_type_sig(old_cols[oc]):
                continue
            ratio = difflib.SequenceMatcher(None, oc, nc).ratio()
            if ratio >= min_name_ratio:
                cands.append((ratio, oc, nc))
    for ratio, oc, nc in sorted(cands, reverse=True):
        if oc in used_old or nc in used_new:
            continue
        rivals = [r for r, o, n in cands if (o == oc or n == nc) and (o, n) != (oc, nc)]
        if rivals and max(rivals) == ratio:
            continue
        pairs.append((oc, nc))
        used_old.add(oc)
        used_new.add(nc)
    return pairs


def table_similarity(src, dst, new, old):
    """0..1: colunas de mesmo nome (mais ate as renomeadas de mesmo tipo)
    sobre o total distinto das duas tabelas."""
    new_cols = {c['COLUMN_NAME']: c for c in src.cols_by_table.get(new, [])}
    old_cols = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get(old, [])}
    if not new_cols or not old_cols:
        return 0.0
    common = set(new_cols) & set(old_cols)
    only_new = [new_cols[c] for c in set(new_cols) - common]
    only_old = [old_cols[c] for c in set(old_cols) - common]
    renamed = min(sum(1 for a in only_new
                      if any(col_type_sig(a) == col_type_sig(b) for b in only_old)), len(only_old))
    union = len(set(new_cols) | set(old_cols)) - renamed
    return (len(common) + renamed) / union if union else 0.0


def confirm_renames_interactive(src, dst, missing_tables, extra_tables, auto_renames,
                                min_show=0.3):
    """Para cada tabela que nao existe no destino, mostra na tela se o diff
    entende CREATE ou RENAME (com as candidatas e a similaridade) e pede
    confirmacao. Em RENAME, confirma tambem a troca de nome da PK.
    Retorna (renames {nova: antiga}, pk_choice {nova: (pk_antiga, pk_nova) | False})."""
    renames, pk_choice, used_old = {}, {}, set()
    if not missing_tables:
        return renames, pk_choice
    print()
    print('  ' + gradient("━" * (UI_W - 4), 'amarelo', 'rosa'))
    print('  ' + paint("TABELAS QUE NAO EXISTEM NO DESTINO  -  CREATE ou RENAME?", 'amarelo', bold=True))
    print('  ' + gradient("━" * (UI_W - 4), 'amarelo', 'rosa'))
    for new in missing_tables:
        cands = sorted(((table_similarity(src, dst, new, old), old) for old in extra_tables
                        if old[0] == new[0] and old not in used_old), reverse=True)
        cands = [(r, o) for r, o in cands if r >= min_show]
        sugerida = auto_renames.get(new)
        print(cor(f"\n{new[0]}.{new[1]}", 'ciano') + "  (existe so na origem)")
        if not cands:
            print("  Nenhuma tabela parecida no destino -> CREATE")
            continue
        for i, (r, old) in enumerate(cands, 1):
            marca = cor('  <- sugerida', 'verde') if old == sugerida else ''
            print(f"  {i} - RENAME de {old[1]}  ({r:.0%} das colunas batem){marca}")
        print(cor("  C - CREATE (tabela nova, vazia)", 'vermelho'))
        default = str([o for _r, o in cands].index(sugerida) + 1) if sugerida in [o for _r, o in cands] else 'C'
        while True:
            resp = input(f"  Opcao [{default}]: ").strip().upper() or default
            if resp == 'C':
                old = None
                break
            if resp.isdigit() and 1 <= int(resp) <= len(cands):
                old = cands[int(resp) - 1][1]
                break
            print("  Opcao invalida.")
        if not old:
            print(cor(f"  -> CREATE TABLE {new[1]}", 'vermelho'))
            continue
        renames[new] = old
        used_old.add(old)
        print(cor(f"  -> RENAME {old[1]} TO {new[1]}", 'verde'))

        pk_new = pk_columns(src, new[0], new[1])
        pk_old = pk_columns(dst, old[0], old[1])
        print(f"     PK origem : {', '.join(pk_new) or '(sem PK)'}")
        print(f"     PK destino: {', '.join(pk_old) or '(sem PK)'}")
        if len(pk_new) == 1 and len(pk_old) == 1 and pk_new != pk_old:
            nc = {c['COLUMN_NAME']: c for c in src.cols_by_table.get(new, [])}.get(pk_new[0])
            oc = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get(old, [])}.get(pk_old[0])
            if nc and oc and col_type_sig(nc) != col_type_sig(oc):
                print(cor("     ATENCAO: tipos diferentes - confira antes de renomear.", 'vermelho'))
            if ask_yes_no(f"     Renomear a coluna PK {pk_old[0]} -> {pk_new[0]}?", True):
                pk_choice[new] = (pk_old[0], pk_new[0])
            else:
                pk_choice[new] = False
        elif pk_new == pk_old and pk_new:
            print("     PK com o mesmo nome - nada a renomear.")
    print()
    return renames, pk_choice


def detect_table_renames(src, dst, missing_tables, extra_tables, min_ratio=0.5):
    """Pareia tabela FALTANTE no destino (existe so na origem) com tabela EXTRA
    (existe so no destino) do mesmo owner quando as colunas sao parecidas -
    provavel RENAME. Similaridade = colunas de mesmo nome / total distinto
    (Jaccard), aceitando ate 1 coluna renomeada de mesmo tipo (ex.: a PK).
    So pareia quando o melhor candidato e unico. Retorna {nova: antiga}."""
    scores = []
    for new in missing_tables:
        new_cols = {c['COLUMN_NAME']: c for c in src.cols_by_table.get(new, [])}
        for old in extra_tables:
            if old[0] != new[0]:
                continue
            old_cols = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get(old, [])}
            if not new_cols or not old_cols:
                continue
            common = set(new_cols) & set(old_cols)
            only_new = [new_cols[c] for c in set(new_cols) - common]
            only_old = [old_cols[c] for c in set(old_cols) - common]
            renamed = sum(1 for a in only_new
                          if any(col_type_sig(a) == col_type_sig(b) for b in only_old))
            matched = len(common) + min(renamed, len(only_old))
            union = len(set(new_cols) | set(old_cols)) - min(renamed, len(only_old))
            ratio = matched / union if union else 0
            if ratio >= min_ratio:
                scores.append((ratio, new, old))
    renames, used_new, used_old = {}, set(), set()
    for ratio, new, old in sorted(scores, reverse=True):
        if new in used_new or old in used_old:
            continue
        rivals = [r for r, n, o in scores if (n == new or o == old) and (n, o) != (new, old)]
        if rivals and max(rivals) == ratio:
            continue  # empate: nao arrisca
        renames[new] = old
        used_new.add(new)
        used_old.add(old)
    return renames


def generate_ddl_scripts_by_schema(conn_src, src: SchemaSnapshot, dst: SchemaSnapshot,
                                    report, column_diffs, service_users=None,
                                    idempotent=True, drop_columns=False,
                                    detect_renames=True, renames_override=None,
                                    pk_choices=None):
    """Retorna um dict {schema: texto_do_script}, um script por schema
    comparado. Grants e sinonimos de objetos novos (tabela/sequence
    faltante) sao gerados SEMPRE para o usuario de servico configurado
    em service_users[schema] (config.ini, secao [usuarios_servico]) -
    nao para qualquer conta que aparecer nos grants/sinonimos da
    origem. Schema sem usuario de servico configurado nao recebe
    grant/sinonimo automatico, so o CREATE TABLE/CREATE SEQUENCE."""
    service_users = service_users or {}

    missing_tables = sorted(src.table_keys - dst.table_keys)
    extra_tables = sorted(dst.table_keys - src.table_keys)
    pk_choices = pk_choices or {}
    if renames_override is not None:
        table_renames = dict(renames_override)
    else:
        table_renames = (detect_table_renames(src, dst, missing_tables, extra_tables)
                         if detect_renames else {})
    missing_tables = [t for t in missing_tables if t not in table_renames]
    missing_seq = sorted(src.seq_keys - dst.seq_keys)
    missing_syn = sorted(src.syn_keys - dst.syn_keys)
    missing_views = sorted(src.view_keys - dst.view_keys)
    diverging_views = sorted(ref for ref in refs_of(report, 'VIEW DIVERGENTE'))
    missing_plsql = sorted(src.plsql_keys - dst.plsql_keys)
    diverging_plsql = sorted(ref for ref in refs_of(report, 'PLSQL DIVERGENTE'))
    missing_indexes = sorted(refs_of(report, 'INDICE FALTANTE'))
    order_issues = sorted(refs_of(report, 'ORDEM DE COLUNAS'))
    renames_cons = sorted(refs_of(report, 'CONSTRAINT COM NOME DIFERENTE'))
    renames_idx = sorted(refs_of(report, 'INDICE COM NOME DIFERENTE'))
    cons_div = sorted(refs_of(report, 'CONSTRAINT DIVERGENTE'))
    cons_status = sorted(refs_of(report, 'CONSTRAINT STATUS DIVERGENTE'))
    cons_extra = sorted(refs_of(report, 'CONSTRAINT EXTRA'))

    # colunas faltantes em tabela que ja existe nos dois lados
    missing_cols = defaultdict(list)
    for owner, table, col in refs_of(report, 'COLUNA FALTANTE'):
        col_row = next((c for c in src.cols_by_table.get((owner, table), [])
                        if c['COLUMN_NAME'] == col), None)
        if col_row:
            missing_cols[(owner, table)].append(col_row)

    # colunas que so existem no destino (vao virar DROP COLUMN no fim)
    extra_cols = sorted(refs_of(report, 'COLUNA EXTRA'))

    # coluna renomeada em tabela comum -> RENAME COLUMN (sai de ADD e de DROP)
    common_col_renames = defaultdict(list)
    extra_by_table = defaultdict(list)
    for o, t, c in extra_cols:
        extra_by_table[(o, t)].append(c)
    for key in sorted(set(missing_cols) & set(extra_by_table)):
        only_new = [c['COLUMN_NAME'] for c in missing_cols[key]]
        pairs = pair_columns_common_table(src, dst, key[0], key[1], only_new,
                                          extra_by_table[key], table_renames)
        if pairs:
            common_col_renames[key] = pairs
            new_done = {n for _o, n in pairs}
            old_done = {o for o, _n in pairs}
            missing_cols[key] = [c for c in missing_cols[key] if c['COLUMN_NAME'] not in new_done]
            if not missing_cols[key]:
                del missing_cols[key]
            extra_cols = [r for r in extra_cols if not ((r[0], r[1]) == key and r[2] in old_done)]

    def type_sig(c):
        return (c.get('DATA_TYPE'), c.get('DATA_LENGTH'), c.get('DATA_PRECISION'), c.get('DATA_SCALE'))

    # constraints faltantes: PK/UK/CHECK vao no corpo, FK num bloco
    # final (depois que todas as tabelas e colunas ja existem)
    missing_cons_normal, missing_cons_fk = [], []
    for key in refs_of(report, 'CONSTRAINT FALTANTE'):
        cons = src.cons_by_key.get((key[0], key[2]))
        if not cons:
            continue
        (missing_cons_fk if cons['CONSTRAINT_TYPE'] == 'R'
         else missing_cons_normal).append(key)

    plsql_names = {(p[0], p[2]) for p in src.plsql_keys}

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
        new_object_names = ({t[1] for t in sch_missing_tables} | {s[1] for s in sch_missing_seq}
                            | {v[1] for v in missing_views if v[0] == schema})

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
                out.append(guarded_text(
                    get_sequence_ddl_from_row(seq_by_key[key]),
                    f"SELECT COUNT(*) FROM dba_sequences WHERE sequence_owner = '{schema}' "
                    f"AND sequence_name = '{key[1]}'",
                    f"SEQUENCE {schema}.{key[1]}", True, idempotent))
                out.append("")
                if service_user:
                    out.append(f"grant SELECT on {schema}.{key[1]} to {service_user};")
                    out.append(build_synonym_statement(service_user, schema, key[1]))
                    out.append("")
            wrote_anything = True

        sch_renames = sorted((n, o) for n, o in table_renames.items() if n[0] == schema)
        if sch_renames:
            out.append("/*==============================================================*/")
            out.append("/* Tabelas RENOMEADAS (detectado por semelhanca de colunas)       */")
            out.append("/* RENAME preserva dados, grants, indices e constraints.          */")
            out.append("/* Confira o par antes de aplicar. Depois RODE O DIFF DE NOVO     */")
            out.append("/* para alinhar constraints, indices e nomes restantes.           */")
            out.append("/*==============================================================*/")
            for (owner, new), (_o, old) in sch_renames:
                new_cols = {c['COLUMN_NAME']: c for c in src.cols_by_table.get((owner, new), [])}
                old_cols = {c['COLUMN_NAME']: c for c in dst.cols_by_table.get((owner, old), [])}
                only_new = sorted(set(new_cols) - set(old_cols))
                only_old = sorted(set(old_cols) - set(new_cols))
                out.append(f"-- {owner}.{old} ({dst.label})  ->  {owner}.{new} ({src.label})")
                out.append(guarded_text(
                    f"ALTER TABLE {owner}.{old} RENAME TO {new};",
                    f"SELECT COUNT(*) FROM dba_tables t WHERE t.owner = '{owner}' "
                    f"AND t.table_name = '{old}' AND NOT EXISTS (SELECT 1 FROM dba_tables n "
                    f"WHERE n.owner = '{owner}' AND n.table_name = '{new}')",
                    f"RENAME TABLE {owner}.{old} TO {new}", False, idempotent))
                out.append("")

                # colunas renomeadas: so PK x PK ou nomes muito parecidos
                col_pairs = pair_renamed_columns(src, dst, owner, new, old, only_new, only_old,
                                                 pk_choice=pk_choices.get((owner, new)))
                for oc, nc in col_pairs:
                    out.append(guarded_text(
                        f"ALTER TABLE {owner}.{new} RENAME COLUMN {oc} TO {nc};",
                        f"SELECT COUNT(*) FROM dba_tab_columns WHERE owner = '{owner}' "
                        f"AND table_name = '{new}' AND column_name = '{oc}'",
                        f"RENAME COLUMN {owner}.{new}.{oc} TO {nc}", False, idempotent))
                    out.append("")
                done_new = {nc for _oc, nc in col_pairs}
                done_old = {oc for oc, _nc in col_pairs}

                add_cols = [new_cols[c] for c in only_new if c not in done_new]
                if add_cols:
                    out.append(f"-- colunas que existem so em {src.label}:")
                    out.extend(build_add_column_statements(src, owner, new, add_cols, idem=idempotent))
                left_new = [c for c in only_new if c not in done_new]
                for oc in [c for c in only_old if c not in done_old]:
                    same_type = [nc for nc in left_new
                                 if col_type_sig(new_cols[nc]) == col_type_sig(old_cols[oc])]
                    if same_type:
                        out.append(f"-- VERIFIQUE: {oc} tem o mesmo tipo de {', '.join(same_type)} "
                                   f"(gerada como ADD). Se for so troca de nome, use RENAME COLUMN; "
                                   f"se for troca de vinculo, migre o dado antes do DROP.")
                    out.append(f"-- coluna {oc} existe so em {dst.label} - revisar "
                               f"(o diff seguinte vai lista-la para DROP):")
                    out.append(f"-- ALTER TABLE {owner}.{new} DROP COLUMN {oc} CASCADE CONSTRAINTS;")
                out.append("")

                comments = build_comment_statements(src, owner, new)
                if comments:
                    out.append(comments)
                    out.append("")
                if service_user:
                    out.append(build_synonym_statement(service_user, owner, new))
                    out.append(guarded_text(
                        f"DROP SYNONYM {service_user}.{old};",
                        f"SELECT COUNT(*) FROM dba_synonyms WHERE owner = '{service_user}' "
                        f"AND synonym_name = '{old}'",
                        f"DROP SYNONYM {service_user}.{old}", False, idempotent))
                    out.append("")
            wrote_anything = True

        for owner, table in sch_missing_tables:
            out.append("/*==============================================================*/")
            out.append(f"/* Table: {table}"[:64].ljust(64) + "*/")
            out.append("/*==============================================================*/")
            ddl = get_table_ddl(conn_src, owner, table)
            emit_guarded(out, ddl,
                         f"SELECT COUNT(*) FROM dba_tables WHERE owner = '{owner}' "
                         f"AND table_name = '{table}'",
                         f"TABLE {owner}.{table}", idempotent)
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

        sch_col_ren = {k: v for k, v in common_col_renames.items() if k[0] == schema}
        if sch_col_ren:
            out.append("/*==============================================================*/")
            out.append("/* Colunas RENOMEADAS em tabela existente                         */")
            out.append("/* (FK para a mesma tabela logica ou nome quase igual)            */")
            out.append("/* RENAME preserva dado, PK/FK/UK, indices e comentario.          */")
            out.append("/*==============================================================*/")
            for (owner, table), pairs in sorted(sch_col_ren.items()):
                for oc, nc in pairs:
                    out.append(f"-- {owner}.{table}: {oc} ({dst.label}) -> {nc} ({src.label})")
                    out.append(guarded_text(
                        f"ALTER TABLE {owner}.{table} RENAME COLUMN {oc} TO {nc};",
                        f"SELECT COUNT(*) FROM dba_tab_columns WHERE owner = '{owner}' "
                        f"AND table_name = '{table}' AND column_name = '{oc}'",
                        f"RENAME COLUMN {owner}.{table}.{oc} TO {nc}", False, idempotent))
                    comment = src.col_comment.get((owner, table, nc))
                    if comment:
                        out.append(f"comment on column {owner}.{table}.{nc} is\n"
                                   f"'{strip_accents(comment)}';")
                    out.append("")
            wrote_anything = True

        sch_missing_cols = {k: v for k, v in missing_cols.items() if k[0] == schema}
        if sch_missing_cols:
            out.append("PROMPT DIAGNOSTICO - colunas a adicionar")
            diag_in(out, "SELECT table_name, column_name FROM dba_tab_columns",
                    f"WHERE owner = '{schema}'", "(table_name, column_name)",
                    [f"('{t}','{c['COLUMN_NAME']}')" for (_o, t), cs in sorted(sch_missing_cols.items())
                     for c in cs])
            out.append("/*==============================================================*/")
            out.append("/* Colunas faltantes em tabela existente                          */")
            out.append("/*==============================================================*/")
            for (owner, table), cols in sorted(sch_missing_cols.items()):
                out.extend(build_add_column_statements(src, owner, table, cols, idem=idempotent))
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
                    out.append(guarded_text(
                        f"ALTER TABLE {owner}.{table} MODIFY ({col} {new_state});",
                        f"SELECT COUNT(*) FROM dba_tab_columns WHERE owner = '{owner}' "
                        f"AND table_name = '{table}' AND column_name = '{col}' "
                        f"AND nullable = '{'Y' if new_state == 'NOT NULL' else 'N'}'",
                        f"{new_state} {owner}.{table}.{col}", False, idempotent))
                    out.append("")
            wrote_anything = True

        # --- mesma definicao, nome diferente: so comentado -----------
        sch_renames = [r for r in renames_cons + renames_idx if r[1] == schema]
        if sch_renames:
            out.append("/*==============================================================*/")
            out.append("/* PK / UK / CHECK / INDICE equivalentes com NOME DIFERENTE       */")
            out.append("/* Nada foi criado (duplicaria o objeto). Renomeacao COMENTADA -  */")
            out.append("/* descomente so se o nome da origem tambem for o desejado.       */")
            out.append("/*==============================================================*/")
            for tipo, owner, table, dst_name, src_name, detalhe, conflito in sch_renames:
                rotulo = {'P': 'PK', 'U': 'UK', 'C': 'CHECK', 'R': 'FK', 'INDEX': 'INDICE'}[tipo]
                out.append(f"-- {rotulo} {owner}.{table} ({detalhe}): "
                           f"destino={dst_name} | origem={src_name}")
                if conflito:
                    out.append(f"-- ATENCAO: o nome {src_name} ja existe no destino em outro "
                               f"objeto - o RENAME abaixo falharia.")
                if tipo == 'INDEX':
                    out.append(f"-- ALTER INDEX {owner}.{dst_name} RENAME TO {src_name};")
                else:
                    out.append(f"-- ALTER TABLE {owner}.{table} RENAME CONSTRAINT "
                               f"{dst_name} TO {src_name};")
                    if tipo in ('P', 'U'):
                        out.append(f"-- conferir o indice de suporte apos o rename: SELECT index_name "
                                   f"FROM dba_constraints WHERE owner = '{owner}' "
                                   f"AND constraint_name = '{src_name}';")
                out.append("")
            wrote_anything = True

        # --- indices (depois de tabelas e colunas existirem) --------
        sch_indexes = [k for k in missing_indexes if k[0] == schema]
        if sch_indexes:
            out.append("PROMPT DIAGNOSTICO - indices a criar")
            diag_in(out, "SELECT owner, index_name FROM dba_indexes",
                    f"WHERE owner = '{schema}'", "index_name",
                    [f"'{n}'" for _o, n in sch_indexes])
            out.append("/*==============================================================*/")
            out.append("/* Indices faltantes                                              */")
            out.append("/*==============================================================*/")
            for owner, name in sch_indexes:
                info = src.index_by_key[(owner, name)]
                out.append(f"-- {owner}.{name} em {info['TABLE_OWNER']}.{info['TABLE_NAME']} "
                           f"({', '.join(src.index_columns.get((owner, name), []))})")
                emit_guarded(out, get_object_ddl(conn_src, 'INDEX', owner, name),
                             f"SELECT COUNT(*) FROM dba_indexes WHERE owner = '{owner}' "
                             f"AND index_name = '{name}'",
                             f"INDEX {owner}.{name}", idempotent)
                out.append("")
            wrote_anything = True

        # --- constraints nao-FK ------------------------------------
        sch_cons = [k for k in missing_cons_normal if k[0] == schema]
        if sch_cons:
            out.append("PROMPT DIAGNOSTICO - constraints a criar")
            diag_in(out, "SELECT owner, table_name, constraint_name, status FROM dba_constraints",
                    f"WHERE owner = '{schema}'", "constraint_name",
                    [f"'{n}'" for _o, _t, n in sch_cons])
            out.append("/*==============================================================*/")
            out.append("/* Constraints faltantes (PK / UK / CHECK)                        */")
            out.append("/*==============================================================*/")
            for owner, table, name in sch_cons:
                out.append(f"-- {owner}.{table}.{name}")
                emit_guarded(out, get_object_ddl(conn_src, 'CONSTRAINT', owner, name),
                             f"SELECT COUNT(*) FROM dba_constraints WHERE owner = '{owner}' "
                             f"AND constraint_name = '{name}'",
                             f"CONSTRAINT {owner}.{name}", idempotent)
                out.append("")
            wrote_anything = True

        # --- constraints: mesmo nome, definicao diferente (COMENTADO) ---
        sch_cdiv = [r for r in cons_div if r[0] == schema]
        if sch_cdiv:
            out.append("/*==============================================================*/")
            out.append("/* Constraints com MESMO NOME e definicao diferente - COMENTADO.  */")
            out.append("/* Oracle nao tem ALTER da regra: e DROP + recriar. Confira antes */")
            out.append("/* se a tabela tem dado que viola a definicao da origem.          */")
            out.append("/*==============================================================*/")
            for owner, table, name, tipo, txt_src, txt_dst in sch_cdiv:
                out.append(f"-- {owner}.{table}.{name}: destino=[{txt_dst}] | origem=[{txt_src}]")
                out.append(f"-- ALTER TABLE {owner}.{table} DROP CONSTRAINT {name};")
                obj = 'REF_CONSTRAINT' if tipo == 'R' else 'CONSTRAINT'
                out.append(comment_out(get_object_ddl(conn_src, obj, owner, name)))
                out.append("")
            wrote_anything = True

        sch_cextra = [r for r in cons_extra if r[0] == schema]
        if sch_cextra:
            out.append("/*==============================================================*/")
            out.append("/* Constraints que existem SO NO DESTINO - decida (nada e gerado) */")
            out.append("/*==============================================================*/")
            for owner, table, name, tipo, txt in sch_cextra:
                out.append(f"-- {owner}.{table}.{name}" + (f" ({txt})" if txt else ""))
                out.append(f"-- ALTER TABLE {owner}.{table} DROP CONSTRAINT {name};")
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
        handled_owner = (service_user or '').upper()
        sch_missing_syn = [s for s in missing_syn
                           if src.syn_target[s][0] == schema
                           and src.syn_target[s][1] not in new_object_names]

        def target_exists(target):
            return (target in dst.table_keys or target in dst.seq_keys
                    or target in dst.view_keys or target in plsql_names)

        # sinonimo do usuario de servico para objeto
        # que ja existe no destino: cria. Antes ficava de fora do script.
        auto_syn = [s for s in sch_missing_syn
                    if service_user and s[0].upper() == handled_owner
                    and target_exists(src.syn_target[s])]
        leftover_syn = [s for s in sch_missing_syn if s not in auto_syn]

        if auto_syn:
            out.append("/*==============================================================*/")
            out.append("/* Sinonimos faltantes no schema de servico - objeto ja existe    */")
            out.append("/*==============================================================*/")
            for owner, syn in auto_syn:
                target = src.syn_target[(owner, syn)]
                out.append(f"-- {owner}.{syn} -> {target[0]}.{target[1]}")
                out.append(build_synonym_statement(service_user, target[0], syn,
                                                   target_name=target[1]))
                out.append("")
            wrote_anything = True

        sch_div_syn = [r for r in refs_of(report, 'SINONIMO DIVERGENTE') if r[1][0] == schema]
        if sch_div_syn:
            out.append("/*==============================================================*/")
            out.append("/* Sinonimos que existem nos dois lados mas apontam para alvos    */")
            out.append("/* diferentes - COMENTADO: repontar muda o comportamento.         */")
            out.append("/*==============================================================*/")
            for (owner, syn), t_src, t_dst in sch_div_syn:
                out.append(f"-- {owner}.{syn}: destino={t_dst[0]}.{t_dst[1]} | origem={t_src[0]}.{t_src[1]}")
                out.append("-- " + build_synonym_statement(owner, t_src[0], syn, t_src[1]).replace("\n", "\n-- "))
                out.append("")
            wrote_anything = True

        if leftover_syn:
            out.append("/*==============================================================*/")
            out.append("/* Sinonimos faltantes NAO tratados automaticamente - revisar     */")
            out.append("/* (dono diferente do configurado, ou aponta para objeto que      */")
            out.append("/* precisa ser confirmado antes de criar)                         */")
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
            out.append("PROMPT DIAGNOSTICO - foreign keys a criar")
            diag_in(out, "SELECT owner, table_name, constraint_name, status FROM dba_constraints",
                    f"WHERE owner = '{schema}'", "constraint_name",
                    [f"'{n}'" for _o, _t, n in sch_fk])
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
                emit_guarded(out, get_object_ddl(conn_src, 'REF_CONSTRAINT', owner, name),
                             f"SELECT COUNT(*) FROM dba_constraints WHERE owner = '{owner}' "
                             f"AND constraint_name = '{name}'",
                             f"FK {owner}.{name}", idempotent)
                out.append("")
            wrote_anything = True

        sch_status = [r for r in cons_status if r[0] == schema]
        if sch_status:
            ordem_on = {'P': 0, 'U': 1, 'C': 2, 'R': 3}
            out.append("/*==============================================================*/")
            out.append("/* Status de constraint diverge (ENABLED / DISABLED) - REVISAR    */")
            out.append("/* ENABLE falha se ja houver dado que viola a regra.              */")
            out.append("/*==============================================================*/")
            desligar = sorted((r for r in sch_status if r[4] == 'DISABLED'),
                              key=lambda r: -ordem_on.get(r[3], 9))
            ligar = sorted((r for r in sch_status if r[4] == 'ENABLED'),
                           key=lambda r: ordem_on.get(r[3], 9))
            for owner, table, name, tipo, st_src, st_dst in desligar + ligar:
                acao = 'ENABLE' if st_src == 'ENABLED' else 'DISABLE'
                out.append(f"-- {owner}.{table}.{name}: destino={st_dst} | origem={st_src}")
                out.append(guarded_text(
                    f"ALTER TABLE {owner}.{table} {acao} CONSTRAINT {name};",
                    f"SELECT COUNT(*) FROM dba_constraints WHERE owner = '{owner}' "
                    f"AND constraint_name = '{name}' AND status = '{st_dst}'",
                    f"{acao} CONSTRAINT {owner}.{name}", False, idempotent))
                out.append("")
            wrote_anything = True

        # --- colunas que so existem no destino (sempre por ultimo) --
        # DROP vem depois das FKs e do ADD das colunas novas, para dar
        # tempo de migrar o dado da coluna antiga para a nova.
        sch_extra_cols = [r for r in extra_cols if r[0] == schema]
        if sch_extra_cols:
            out.append("/*==============================================================*/")
            out.append("/* Colunas que existem SO NO DESTINO - DROP COLUMN               */")
            out.append("/* ATENCAO: apaga o dado. Antes, migre o conteudo para a coluna   */")
            out.append("/* nova (se houver) e confira se nao e um RENAME.                 */")
            if not drop_columns:
                out.append("/* Saiu COMENTADO (gerar_drop_coluna = false no config.ini).      */")
            out.append("/*==============================================================*/")
            for owner, table, col in sch_extra_cols:
                dst_col = next((c for c in dst.cols_by_table.get((owner, table), [])
                                if c['COLUMN_NAME'] == col), {})
                cands = [m['COLUMN_NAME'] for m in missing_cols.get((owner, table), [])
                         if type_sig(m) == type_sig(dst_col)]
                out.append(f"-- {owner}.{table}.{col} {render_column_type(dst_col) if dst_col else ''} "
                           f"existe so no destino")
                if len(cands) == 1:
                    out.append(f"-- VERIFIQUE: mesmo tipo de {cands[0]} (gerada como ADD acima). "
                               f"Se for so troca de nome, use RENAME no lugar de ADD + DROP:")
                    out.append(f"-- ALTER TABLE {owner}.{table} RENAME COLUMN {col} TO {cands[0]};")
                bloco = guarded_text(
                    f"ALTER TABLE {owner}.{table} DROP COLUMN {col} CASCADE CONSTRAINTS;",
                    f"SELECT COUNT(*) FROM dba_tab_columns WHERE owner = '{owner}' "
                    f"AND table_name = '{table}' AND column_name = '{col}'",
                    f"DROP COLUMN {owner}.{table}.{col}", False, idempotent)
                out.append(bloco if drop_columns else comment_out(bloco))
                out.append("")
            wrote_anything = True

        if wrote_anything:
            scripts[schema] = "\n".join(out)

    return scripts


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

# ======================================================================
# UI do terminal - cores truecolor, caixas e banner.
# Sem dependencia externa. Se a saida nao for um terminal (redirecionada
# para arquivo), tudo sai em texto puro.
# ======================================================================
import re as _re
import threading as _threading
import time as _time

if os.name == 'nt':
    os.system('')  # liga o suporte a cores ANSI no cmd/PowerShell (Windows 10+)
try:
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')
except Exception:
    pass

FANCY = sys.stdout.isatty()
_RESET, _BOLD, _DIM = '\033[0m', '\033[1m', '\033[2m'
_ANSI = _re.compile(r'\033\[[0-9;]*m')

PALETA = {
    'ciano':    (0, 212, 255),
    'azul':     (90, 140, 255),
    'roxo':     (167, 112, 255),
    'rosa':     (255, 70, 170),
    'verde':    (46, 230, 140),
    'amarelo':  (255, 205, 60),
    'laranja':  (255, 140, 50),
    'vermelho': (255, 85, 95),
    'cinza':    (125, 135, 160),
    'branco':   (238, 242, 252),
}
UI_W = 70  # largura das caixas


def _rgb(c):
    return f"\033[38;2;{c[0]};{c[1]};{c[2]}m"


def paint(texto, nome, bold=False):
    """Texto numa cor da PALETA."""
    if not FANCY:
        return texto
    return f"{_BOLD if bold else ''}{_rgb(PALETA[nome])}{texto}{_RESET}"


def cor(texto, nome):
    """Compatibilidade: cor em negrito."""
    return paint(texto, nome, bold=True)


def gradient(texto, c1, c2, shift=0.0):
    """Degrade horizontal entre duas cores (c1/c2 = nomes da PALETA)."""
    if not FANCY:
        return texto
    a, b = PALETA[c1], PALETA[c2]
    n = max(len(texto) - 1, 1)
    out = []
    for i, ch in enumerate(texto):
        t = min(max(i / n + shift, 0), 1)
        c = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
        out.append(f"{_rgb(c)}{ch}")
    return _BOLD + ''.join(out) + _RESET


def _vlen(s):
    return len(_ANSI.sub('', s))


def box(linhas, cor_borda='roxo', titulo=None, largura=UI_W):
    """Caixa com borda colorida e titulo embutido."""
    inner = largura - 2
    if titulo:
        t = f" {titulo} "
        top = '┌─' + t + '─' * max(inner - 1 - len(t), 0) + '┐'
        top = paint('┌─', cor_borda) + paint(t, cor_borda, bold=True) + \
            paint('─' * max(inner - 1 - len(t), 0) + '┐', cor_borda)
    else:
        top = paint('┌' + '─' * inner + '┐', cor_borda)
    out = [top]
    lado = paint('│', cor_borda)
    for l in linhas:
        pad = max(inner - 2 - _vlen(l), 0)
        out.append(f"{lado} {l}{' ' * pad} {lado}")
    out.append(paint('└' + '─' * inner + '┘', cor_borda))
    return '\n'.join(out)


_FONTE = {
    'O': [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    'R': ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    'A': [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    'C': [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
    'L': ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
    'E': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    'D': ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    'I': ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    'F': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "██║     ", "╚═╝     "],
    ' ': ["  ", "  ", "  ", "  ", "  ", "  "],
}


def banner():
    """Logo ORACLE DIFF em degrade diagonal ciano -> roxo -> rosa."""
    if not FANCY:
        print("\n=== ORACLE DIFF ===")
        return
    linhas = [''.join(_FONTE[ch][r] for ch in "ORACLE DIFF") for r in range(6)]
    print()
    for r, l in enumerate(linhas):
        meio = len(l) // 2
        print('  ' + gradient(l[:meio], 'ciano', 'roxo', shift=r * 0.04) +
              gradient(l[meio:], 'roxo', 'rosa', shift=r * 0.04))
    sub = "schema diff  ·  Oracle 19c  ·  padrao DIGED / PF"
    print('  ' + paint(sub.center(len(linhas[0])), 'cinza'))
    print()


def prompt(texto, hint=''):
    seta = paint('»', 'rosa', bold=True) if FANCY else '>'
    h = f" {paint(hint, 'amarelo', bold=True)}" if hint else ''
    return f"\n {seta} {paint(texto, 'branco', bold=True)}{h} "


class Spinner:
    """Animacao enquanto o banco responde (le metadados, compara...)."""
    _FRAMES = '▁▂▃▄▅▆▇█▇▆▅▄▃▂'

    def __init__(self, msg):
        self.msg = msg
        self._stop = False
        self._t = None
        self._ini = 0

    def __enter__(self):
        self._ini = _time.time()
        if not FANCY:
            print(f"  ... {self.msg}", file=sys.stderr)
            return self
        self._t = _threading.Thread(target=self._run, daemon=True)
        self._t.start()
        return self

    def _run(self):
        i = 0
        while not self._stop:
            barra = ''.join(self._FRAMES[(i + k) % len(self._FRAMES)] for k in range(6))
            sys.stderr.write(f"\r  {gradient(barra, 'ciano', 'rosa')}  {paint(self.msg, 'branco')}   ")
            sys.stderr.flush()
            _time.sleep(0.07)
            i += 1

    def __exit__(self, exc_type, *a):
        if not FANCY:
            return False
        self._stop = True
        self._t.join()
        seg = _time.time() - self._ini
        if exc_type:
            sys.stderr.write(f"\r  {paint('FALHOU', 'vermelho', bold=True)}  {self.msg}{' ' * 12}\n")
        else:
            sys.stderr.write(f"\r  {paint('  OK  ', 'verde', bold=True)}  {self.msg} "
                             f"{paint(f'({seg:.1f}s)', 'cinza')}{' ' * 12}\n")
        sys.stderr.flush()
        return False


def ask_yes_no(question, default=True):
    """Pergunta S/N no terminal. ENTER assume o default."""
    hint = '[S/n]' if default else '[s/N]'
    while True:
        resp = input(prompt(question, hint)).strip().upper()
        if not resp:
            return default
        if resp in ('S', 'SIM', 'Y'):
            return True
        if resp in ('N', 'NAO', 'NÃO'):
            return False
        print(paint("   Responda S ou N.", 'vermelho'))


def parse_schema_list(text, all_schemas):
    """Converte '3,4' ou 'aproban100, 2' em nomes de schema validos.
    Retorna (escolhidos, invalidos)."""
    chosen, invalid = [], []
    for item in text.split(','):
        item = item.strip().upper()
        if not item:
            continue
        if item.isdigit():
            idx = int(item)
            if 1 <= idx <= len(all_schemas):
                chosen.append(all_schemas[idx - 1])
            else:
                invalid.append(item)
        elif item in all_schemas:
            chosen.append(item)
        else:
            invalid.append(item)
    return list(dict.fromkeys(chosen)), invalid


def add_audit_pairs(chosen, all_schemas):
    """Inclui o <SCHEMA>_AUDIT de cada schema escolhido, se existir no config.ini."""
    result = []
    for s in chosen:
        result.append(s)
        audit = f"{s}_AUDIT"
        if not s.endswith('_AUDIT') and audit in all_schemas:
            result.append(audit)
    return list(dict.fromkeys(result))


def menu_schemas(all_schemas, label_src, label_dst):
    """Menu interativo. Retorna a lista de schemas a comparar ou None para sair."""
    while True:
        banner()
        print(box([
            f"{paint('●', 'verde')} {paint('ORIGEM ', 'cinza')}  {paint(label_src, 'branco', bold=True)}",
            f"{paint('●', 'rosa')} {paint('DESTINO', 'cinza')}  {paint(label_dst, 'branco', bold=True)}"
            f"   {paint('<- o script sera aplicado aqui', 'rosa')}",
        ], 'ciano', 'CONEXOES'))

        linhas = []
        for i, s in enumerate(all_schemas, 1):
            audit = s.endswith('_AUDIT')
            num = paint(f"{i:02d}", 'amarelo', bold=True)
            icone = paint('◇', 'cinza') if audit else paint('◆', 'ciano')
            nome = paint(s, 'cinza') if audit else paint(s, 'branco', bold=True)
            linhas.append(f" {num}   {icone}  {nome}")
        linhas.append('')
        linhas.append(f" {paint(' T ', 'verde', bold=True)}  Todos          "
                      f"{paint(' 0 ', 'vermelho', bold=True)}  Sair")
        print(box(linhas, 'roxo', 'SCHEMAS'))

        resp = input(prompt("Escolha", "(numeros ou nomes, separados por virgula)")).strip().upper()
        if resp in ('0', 'S', 'SAIR', 'Q'):
            return None
        if resp in ('T', 'TODOS', ''):
            chosen = list(all_schemas)
        else:
            chosen, invalid = parse_schema_list(resp, all_schemas)
            if invalid:
                print(paint(f"   Opcao invalida: {', '.join(invalid)}", 'vermelho', bold=True))
                _time.sleep(1.2)
                continue
            if not chosen:
                continue

        faltam_audit = [s for s in chosen
                        if not s.endswith('_AUDIT') and f"{s}_AUDIT" in all_schemas
                        and f"{s}_AUDIT" not in chosen]
        if faltam_audit and ask_yes_no("Incluir tambem o _AUDIT dos schemas escolhidos?", True):
            chosen = add_audit_pairs(chosen, all_schemas)

        print()
        print(box([f"{paint('◆', 'ciano')} {paint(s, 'branco', bold=True)}" for s in chosen],
                  'verde', 'VAI COMPARAR'))
        if ask_yes_no("Confirma a comparacao?", True):
            return chosen


def run_comparison(cfg, args, schemas, conn_src, label_src, conn_dst, label_dst,
                   prefix, service_users, drop_columns=None, interactive=False,
                   check_renames=None):
    """Extrai metadados dos schemas escolhidos, compara e grava relatorio/scripts."""
    print()
    with Spinner(f"Lendo metadados de {label_src}"):
        src = SchemaSnapshot(conn_src, label_src, schemas, prefix,
                             service_users=service_users.values())
    with Spinner(f"Lendo metadados de {label_dst}"):
        dst = SchemaSnapshot(conn_dst, label_dst, schemas, prefix,
                             service_users=service_users.values())

    ignore_sys = cfg['opcoes'].getboolean('ignorar_objetos_sys', fallback=True)
    idempotent = cfg['opcoes'].getboolean('script_idempotente', fallback=True)
    if drop_columns is None:
        drop_columns = cfg['opcoes'].getboolean('gerar_drop_coluna', fallback=False)
    detect_renames = cfg['opcoes'].getboolean('detectar_rename_tabela', fallback=True)

    with Spinner("Comparando estruturas"):
        report, column_diffs = compare(src, dst, ignore_sys=ignore_sys)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.report:
        rep_dir, rep_file = os.path.split(args.report)
        report_path = os.path.join(rep_dir, f"{timestamp}_{rep_file}")
        with open(report_path, 'w', encoding='utf-8') as f:
            print_report(report, out=f)
        gerados = [('RELATORIO', report_path)]
    else:
        gerados = []
        print_report(report)

    if args.ddl:
        configure_metadata_session(conn_src)
        renames_override, pk_choices = None, None
        if check_renames is False:      # menu: N = CREATE TABLE direto
            renames_override, pk_choices = {}, {}
        elif interactive and detect_renames:
            missing_t = sorted(src.table_keys - dst.table_keys)
            extra_t = sorted(dst.table_keys - src.table_keys)
            auto = detect_table_renames(src, dst, missing_t, extra_t)
            renames_override, pk_choices = confirm_renames_interactive(src, dst, missing_t,
                                                                       extra_t, auto)
        with Spinner("Gerando scripts DDL"):
            scripts = generate_ddl_scripts_by_schema(conn_src, src, dst, report, column_diffs,
                                                  service_users=service_users,
                                                  idempotent=idempotent,
                                                  drop_columns=drop_columns,
                                                  detect_renames=detect_renames,
                                                  renames_override=renames_override,
                                                  pk_choices=pk_choices)
        if not scripts:
            print(box([paint("Nenhuma diferenca: os schemas escolhidos ja batem.", 'verde', bold=True)],
                      'verde', 'TUDO CERTO'))
        base, ext = os.path.splitext(args.ddl)
        ext = ext or '.sql'
        base_name = os.path.basename(base)
        for schema, ddl_text in scripts.items():
            # pasta com o nome do schema - se ja existir, so usa (nao recria)
            os.makedirs(schema, exist_ok=True)
            out_path = os.path.join(schema, f"{timestamp}_{base_name}_{schema}{ext}")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(ddl_text)
            gerados.append((schema, out_path))

    if gerados:
        linhas = []
        for nome, caminho in gerados:
            linhas.append(f"{paint('■', 'verde')} {paint(nome.ljust(18), 'branco', bold=True)} "
                          f"{paint(caminho, 'cinza')}")
        print()
        print(box(linhas, 'verde', 'ARQUIVOS GERADOS', largura=max(UI_W, max(_vlen(l) for l in linhas) + 6)))


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
    ap.add_argument('--schemas', default=None,
                     help='schemas a comparar, separados por virgula (ex.: APROBAN100,APROBAN100_AUDIT). '
                          'Informado: roda direto, sem menu. Omitido: abre o menu.')
    ap.add_argument('--drop-coluna', dest='drop_coluna', choices=['S', 'N', 's', 'n'], default=None,
                     help='S = DROP COLUMN (colunas so no destino) sai ATIVO no script; '
                          'N = sai COMENTADO. Omitido: usa gerar_drop_coluna do config.ini '
                          '(no menu, pergunta).')
    args = ap.parse_args()

    cfg = load_config(args.config)
    all_schemas = [s.strip().upper() for s in cfg['opcoes']['schemas'].split(',') if s.strip()]
    prefix = view_prefix(cfg)

    service_users = {}
    if cfg.has_section('usuarios_servico'):
        service_users = {k.upper(): v.strip() for k, v in cfg['usuarios_servico'].items()}

    # modo direto (sem menu): valida antes de conectar
    if args.schemas:
        schemas, invalid = parse_schema_list(args.schemas, all_schemas)
        if invalid or not schemas:
            sys.exit(f"Schema(s) fora do config.ini: {', '.join(invalid) or args.schemas}. "
                     f"Opcoes: {', '.join(all_schemas)}")

    conn_src, label_src = connect(cfg, 'origem')
    conn_dst, label_dst = connect(cfg, 'destino')
    try:
        if args.schemas:
            banner()
            print(box([f"{paint('◆', 'ciano')} {paint(s, 'branco', bold=True)}" for s in schemas],
                      'verde', 'VAI COMPARAR'))
            drop = None if args.drop_coluna is None else args.drop_coluna.upper() == 'S'
            run_comparison(cfg, args, schemas, conn_src, label_src, conn_dst, label_dst,
                           prefix, service_users, drop_columns=drop)
        else:
            while True:
                schemas = menu_schemas(all_schemas, label_src, label_dst)
                if schemas is None:
                    break
                drop_default = cfg['opcoes'].getboolean('gerar_drop_coluna', fallback=False)
                print()
                print(box([
                    paint("Colunas que existem SO NO DESTINO  -  DROP COLUMN apaga o dado", 'branco', bold=True),
                    "",
                    f"{paint(' S ', 'vermelho', bold=True)}  {paint('DROP pronto para executar', 'vermelho')}",
                    f"{paint(' N ', 'verde', bold=True)}  {paint('DROP comentado, para revisar  (recomendado)', 'verde')}",
                ], 'laranja', 'DROP COLUMN'))
                drop = ask_yes_no("Gerar DROP COLUMN ativo?", drop_default)

                print()
                print(box([
                    paint("!!  TABELAS QUE NAO EXISTEM NO DESTINO  !!", 'amarelo', bold=True),
                    "",
                    f"{paint(' S ', 'verde', bold=True)}  {paint('VERIFICAR RENAME', 'verde', bold=True)}"
                    f"{paint(' - mostra cada tabela, sugere o RENAME', 'verde')}",
                    f"      {paint('e pede confirmacao. Preserva os dados.', 'verde')}",
                    f"{paint(' N ', 'vermelho', bold=True)}  {paint('CREATE TABLE direto', 'vermelho', bold=True)}"
                    f"{paint(' - tabela nova VAZIA.', 'vermelho')}",
                    f"      {paint('Se for um rename, os dados ficam na antiga!', 'vermelho')}",
                ], 'amarelo', 'RENAME ou CREATE'))
                check_ren = ask_yes_no("Verificar RENAME de tabelas?", True)
                run_comparison(cfg, args, schemas, conn_src, label_src, conn_dst, label_dst,
                               prefix, service_users, drop_columns=drop, interactive=True,
                               check_renames=check_ren)
                if not ask_yes_no("\nComparar outro schema?", False):
                    break
    except KeyboardInterrupt:
        print(paint("\n  Interrompido pelo usuario.", 'amarelo', bold=True))
    finally:
        conn_src.close()
        conn_dst.close()
        print()
        print('  ' + gradient("━" * (UI_W - 4), 'ciano', 'rosa'))
        print('  ' + paint("Conexoes encerradas. Ate a proxima!", 'cinza'))
        print()


if __name__ == '__main__':
    main()
