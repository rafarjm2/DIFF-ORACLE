#!/usr/bin/env python3
"""
Gerador de Relatório Semanal - Controle de Atendimentos
=========================================================

USO:
    python3 gerar_relatorio.py <caminho_da_planilha.xlsx> [saida.pdf]

FORMATO ESPERADO DA PLANILHA (aba "Controle Atendimentos"):
    Coluna A: Data
    Coluna B: Nº (numero do atendimento no dia)
    Coluna C: Sistema/Schema
    Coluna D: Solicitante
    Coluna E: Redmine
    Coluna F: Descrição/Script
    Coluna G: TICKET
    Coluna H: Status Geral (valores: "Fechado" ou "Pendente")
    Coluna I: Observações

Por padrão, gera o relatório da ÚLTIMA SEMANA com dados na planilha
(domingo a sábado). Para forçar outro período, ajuste FILTRAR_SEMANA.
"""
import sys
import json
import openpyxl
import pandas as pd
from datetime import timedelta
from weasyprint import HTML

DOW_MAP = {0: 'segunda', 1: 'terça', 2: 'quarta', 3: 'quinta', 4: 'sexta', 5: 'sábado', 6: 'domingo'}

FONT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
"""

BASE_CSS = """
@page { size: A4 landscape; margin: 10mm 8mm; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #ececeb; color: #1c1c1b; font-family: 'IBM Plex Sans', Helvetica, sans-serif; }
.sheet { background: #fbfbfa; border: 1px solid #d6d6d3; }
.header { display: flex; align-items: flex-end; justify-content: space-between; gap: 32px; padding: 22px 30px 18px; border-bottom: 2px solid #1c1c1b; }
.header-left { display: flex; flex-direction: column; gap: 6px; }
.eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: #0f766e; font-weight: 600; }
h1 { margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -.02em; line-height: 1.05; }
.header-right { display: flex; gap: 24px; font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #6b6b66; text-align: right; }
.header-right .col { display: flex; flex-direction: column; gap: 4px; }
.header-right .lbl { letter-spacing: .1em; text-transform: uppercase; font-size: 9px; }
.header-right .val { color: #1c1c1b; font-size: 12.5px; }
.kpis { display: flex; border-bottom: 1px solid #d6d6d3; }
.kpi { flex: 1; padding: 16px 18px 18px; border-right: 1px solid #e6e6e3; display: flex; flex-direction: column; gap: 8px; }
.kpi:last-child { border-right: none; }
.kpi .lbl { font-family: 'IBM Plex Mono', monospace; font-size: 9px; letter-spacing: .12em; text-transform: uppercase; color: #85857e; }
.kpi .val { font-size: 30px; font-weight: 600; letter-spacing: -.03em; line-height: 1; color: #1c1c1b; }
.kpi .note { font-size: 10.5px; color: #6b6b66; line-height: 1.35; }
.mid { display: flex; border-bottom: 1px solid #d6d6d3; }
.mid-left { flex: 1.15; padding: 18px 22px 18px; border-right: 1px solid #e6e6e3; }
.mid-right { flex: 1; padding: 18px 22px 18px; display: flex; gap: 24px; }
.section-title-row { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
h2 { margin: 0; font-size: 12px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }
.section-hint { font-family: 'IBM Plex Mono', monospace; font-size: 9.5px; color: #85857e; }
.bars { display: flex; gap: 14px; align-items: end; height: 120px; }
.bar-col { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; height: 100%; gap: 6px; }
.bar-total { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; text-align: center; }
.bar-fill { background: #0f766e; border-top: 3px solid #0b544e; display: flex; flex-direction: column; justify-content: flex-end; }
.bar-pend { background: #d97706; }
.bar-labels { display: flex; gap: 14px; margin-top: 8px; padding-top: 8px; border-top: 1px solid #1c1c1b; }
.bar-label-col { flex: 1; display: flex; flex-direction: column; gap: 2px; text-align: center; }
.bar-label-col .d { font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 500; }
.bar-label-col .w { font-size: 9.5px; color: #85857e; }
.legend { display: flex; gap: 18px; margin-top: 14px; font-size: 10px; color: #6b6b66; }
.legend .item { display: flex; align-items: center; gap: 6px; }
.legend .swatch { width: 9px; height: 9px; display: block; }
.rank-col { flex: 1; }
.rank-item { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.rank-row { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.rank-name { font-size: 11px; font-weight: 500; }
.rank-n { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #6b6b66; }
.rank-track { height: 5px; background: #e6e6e3; }
.rank-fill { height: 100%; background: #0f766e; }
.rank-fill.grey { background: #85857e; }
.records { padding: 20px 30px 24px; }
table { width: 100%; border-collapse: collapse; font-size: 10.5px; }
thead tr { background: #1c1c1b; color: #fbfbfa; }
th { text-align: left; padding: 8px 10px; font-weight: 500; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace; }
th.num { text-align: right; width: 34px; }
.day-row td { padding: 14px 10px 6px; border-bottom: 2px solid #1c1c1b; }
.day-line { display: flex; align-items: baseline; gap: 10px; }
.day-date { font-family: 'IBM Plex Mono', monospace; font-size: 12.5px; font-weight: 600; letter-spacing: .02em; }
.day-dow { font-size: 10.5px; color: #85857e; text-transform: lowercase; }
.day-summary { margin-left: auto; font-family: 'IBM Plex Mono', monospace; font-size: 10px; letter-spacing: .08em; text-transform: uppercase; color: #0f766e; }
td { padding: 7px 10px; border-bottom: 1px solid #e6e6e3; vertical-align: top; }
td.num { text-align: right; font-family: 'IBM Plex Mono', monospace; color: #85857e; font-size: 10px; }
td.sistema { font-weight: 500; }
td.redmine, td.ticket { font-family: 'IBM Plex Mono', monospace; font-size: 10px; }
td.descricao { color: #4a4a45; }
td.obs { font-size: 10px; color: #6b6b66; }
.status-badge { display: inline-block; padding: 2px 8px; font-size: 9px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace; }
tr.record-row { page-break-inside: avoid; }
"""

def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def fmt_num(v):
    """Formata Redmine/Ticket: remove .0 de floats, trata vazio/zero como travessão."""
    if pd.isna(v):
        return '—'
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return '—' if s in ('0', '', 'nan') else s

def carregar_dados(caminho_xlsx):
    wb = openpyxl.load_workbook(caminho_xlsx, data_only=True)
    # Usa a primeira aba (ou "Controle Atendimentos" se existir)
    aba = 'Controle Atendimentos' if 'Controle Atendimentos' in wb.sheetnames else wb.sheetnames[0]
    ws = wb[aba]

    dados = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:  # precisa ter data
            dados.append({
                'data': row[0], 'numero': row[1], 'sistema': row[2],
                'solicitante': row[3], 'redmine': row[4], 'descricao': row[5],
                'ticket': row[6], 'status': row[7], 'observacoes': row[8]
            })

    df = pd.DataFrame(dados)
    df['data'] = pd.to_datetime(df['data'])
    df['solicitante'] = df['solicitante'].astype(str).str.strip()
    return df

def filtrar_ultima_semana(df):
    """Filtra domingo-sábado da semana mais recente com dados."""
    max_date = df['data'].max()
    dias_desde_domingo = max_date.weekday() + 1
    domingo = max_date - timedelta(days=dias_desde_domingo if dias_desde_domingo != 7 else 0)
    sabado = domingo + timedelta(days=6)
    return df[(df['data'] >= domingo) & (df['data'] <= sabado)].copy()

def montar_dados_template(df_periodo):
    dias_unicos = sorted(df_periodo['data'].dt.date.unique())
    total = len(df_periodo)
    fechados = len(df_periodo[df_periodo['status'] == 'Fechado'])
    pendentes = total - fechados
    n_dias = len(dias_unicos)
    media_dia = round(total / n_dias, 1) if n_dias else 0
    pct_fechados = round((fechados / total) * 100) if total else 0

    sist_counts_full = df_periodo['sistema'].value_counts()
    sistema_top = sist_counts_full.idxmax() if len(sist_counts_full) else '—'
    sistema_top_n = int(sist_counts_full.max()) if len(sist_counts_full) else 0

    kpis = [
        {"label": "Total no período", "value": str(total),
         "note": f"{n_dias} dias úteis · média de {str(media_dia).replace('.', ',')}/dia"},
        {"label": "Fechados", "value": str(fechados), "note": f"{pct_fechados}% de conclusão"},
        {"label": "Pendentes", "value": str(pendentes),
         "note": "nenhum em aberto" if pendentes == 0 else f"{pendentes} chamado(s) em aberto"},
        {"label": "Sistemas atendidos", "value": str(df_periodo['sistema'].nunique()),
         "note": f"{sistema_top} concentra {sistema_top_n} chamados"},
        {"label": "Com dependência externa", "value": "0", "note": "sem dependência externa"},
    ]

    # Volume por dia
    by_day = {}
    for d in dias_unicos:
        df_d = df_periodo[df_periodo['data'].dt.date == d]
        by_day[d] = {"total": len(df_d), "pend": len(df_d[df_d['status'] == 'Pendente'])}
    max_dia = max(v['total'] for v in by_day.values()) if by_day else 1

    dias = []
    for d in dias_unicos:
        v = by_day[d]
        dias.append({
            "data": d.strftime('%d/%m'), "dow": DOW_MAP[d.weekday()], "total": v['total'],
            "pct": round((v['total'] / max_dia) * 100) if max_dia else 0,
            "pendPct": round((v['pend'] / v['total']) * 100) if v['total'] else 0
        })

    # Sistemas e solicitantes (top 7)
    def ranking(series):
        counts = series.value_counts()
        if len(counts) == 0:
            return []
        maxv = counts.max()
        return [{"nome": k, "n": int(v), "pct": round((v / maxv) * 100)} for k, v in counts.items()][:7]

    sistemas = ranking(df_periodo['sistema'])
    solicitantes = ranking(df_periodo['solicitante'])

    # Grupos (tabela detalhada)
    grupos = []
    for d in dias_unicos:
        df_d = df_periodo[df_periodo['data'].dt.date == d].reset_index(drop=True)
        v = by_day[d]
        resumo = f"{v['total']} atendimentos" + (
            f" · {v['pend']} pendente" + ("s" if v['pend'] > 1 else "") if v['pend'] else "")

        linhas = []
        for i, row in df_d.iterrows():
            status = row['status'] if pd.notna(row['status']) else 'Fechado'
            obs = '' if pd.isna(row['observacoes']) else str(row['observacoes'])
            linhas.append({
                "num": i + 1, "sistema": row['sistema'], "solicitante": row['solicitante'],
                "redmine": fmt_num(row['redmine']), "descricao": row['descricao'] if pd.notna(row['descricao']) else '—',
                "ticket": fmt_num(row['ticket']), "status": status, "obs": obs,
                "bg": "#f4f4f2" if i == 0 else ("#fbfbfa" if i % 2 == 0 else "#ffffff"),
                "corGrupo": "#0f766e" if i == 0 else "#1c1c1b",
                "statusFg": "#8a4b00" if status == "Pendente" else "#0b544e",
                "statusBg": "#fde8c8" if status == "Pendente" else "#dcefec",
            })
        grupos.append({"data": d.strftime('%d/%m/%Y'), "dow": DOW_MAP[d.weekday()],
                        "resumo": resumo, "linhas": linhas})

    periodo_str = f"{dias_unicos[0].strftime('%d/%m')} – {dias_unicos[-1].strftime('%d/%m/%Y')}" if dias_unicos else '—'

    return {"periodo": periodo_str, "registros": total, "kpis": kpis, "dias": dias,
            "sistemas": sistemas, "solicitantes": solicitantes, "grupos": grupos}

def montar_html(D):
    kpi_html = "".join(f"""
    <div class="kpi"><span class="lbl">{esc(k['label'])}</span>
      <span class="val">{esc(k['value'])}</span><span class="note">{esc(k['note'])}</span></div>"""
        for k in D['kpis'])

    bars_html = "".join(f"""
      <div class="bar-col"><span class="bar-total">{d['total']}</span>
        <div class="bar-fill" style="height: {d['pct']}%;">
          <div class="bar-pend" style="height: {d['pendPct']}%;"></div></div></div>"""
        for d in D['dias'])

    bar_labels_html = "".join(f"""
      <div class="bar-label-col"><span class="d">{esc(d['data'])}</span><span class="w">{esc(d['dow'])}</span></div>"""
        for d in D['dias'])

    def rank_html(items, grey=False):
        cls = "rank-fill grey" if grey else "rank-fill"
        return "".join(f"""
        <div class="rank-item"><div class="rank-row"><span class="rank-name">{esc(s['nome'])}</span>
          <span class="rank-n">{s['n']}</span></div>
          <div class="rank-track"><div class="{cls}" style="width: {s['pct']}%;"></div></div></div>"""
            for s in items)

    sistemas_html = rank_html(D['sistemas'])
    solicitantes_html = rank_html(D['solicitantes'], grey=True)

    rows_html = ""
    for g in D['grupos']:
        rows_html += f"""
      <tr><td colspan="8" class="day-row"><div class="day-line">
        <span class="day-date">{esc(g['data'])}</span><span class="day-dow">{esc(g['dow'])}</span>
        <span class="day-summary">{esc(g['resumo'])}</span></div></td></tr>"""
        for l in g['linhas']:
            rows_html += f"""
      <tr class="record-row" style="background: {l['bg']};">
        <td class="num">{l['num']}</td>
        <td class="sistema" style="color: {l['corGrupo']};">{esc(l['sistema'])}</td>
        <td>{esc(l['solicitante'])}</td>
        <td class="redmine">{esc(l['redmine'])}</td>
        <td class="descricao">{esc(l['descricao'])}</td>
        <td class="ticket">{esc(l['ticket'])}</td>
        <td><span class="status-badge" style="color: {l['statusFg']}; background: {l['statusBg']};">{esc(l['status'])}</span></td>
        <td class="obs">{esc(l['obs'])}</td></tr>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{FONT_CSS}{BASE_CSS}</style></head><body><div class="sheet">
  <div class="header">
    <div class="header-left"><span class="eyebrow">Sustentação · Banco de Dados</span>
      <h1>Controle de Atendimentos</h1></div>
    <div class="header-right">
      <div class="col"><span class="lbl">Período</span><span class="val">{esc(D['periodo'])}</span></div>
      <div class="col"><span class="lbl">Registros</span><span class="val">{D['registros']}</span></div>
    </div></div>
  <div class="kpis">{kpi_html}</div>
  <div class="mid">
    <div class="mid-left">
      <div class="section-title-row"><h2>Volume por dia</h2>
        <span class="section-hint">atendimentos concluídos + pendentes</span></div>
      <div class="bars">{bars_html}</div>
      <div class="bar-labels">{bar_labels_html}</div>
      <div class="legend"><span class="item"><span class="swatch" style="background:#0f766e;"></span>Fechado</span>
        <span class="item"><span class="swatch" style="background:#d97706;"></span>Pendente</span></div>
    </div>
    <div class="mid-right">
      <div class="rank-col"><h2 style="margin-bottom:14px;">Sistema / Schema</h2>{sistemas_html}</div>
      <div class="rank-col"><h2 style="margin-bottom:14px;">Solicitantes</h2>{solicitantes_html}</div>
    </div></div>
  <div class="records">
    <div class="section-title-row"><h2>Registro de atendimentos</h2>
      <span class="section-hint">agrupado por data · Nº reinicia a cada dia</span></div>
    <table><thead><tr>
      <th class="num">Nº</th><th>Sistema / Schema</th><th>Solicitante</th>
      <th style="width:80px;">Redmine</th><th>Descrição / Script</th>
      <th style="width:100px;">Ticket</th><th style="width:90px;">Status</th>
      <th style="width:130px;">Observações</th></tr></thead>
      <tbody>{rows_html}</tbody></table>
  </div>
</div></body></html>"""

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 gerar_relatorio.py <planilha.xlsx> [saida.pdf]")
        sys.exit(1)

    caminho_xlsx = sys.argv[1]
    saida_pdf = sys.argv[2] if len(sys.argv) > 2 else "Controle_de_Atendimentos_Semanal.pdf"

    df = carregar_dados(caminho_xlsx)
    df_semana = filtrar_ultima_semana(df)
    dados_template = montar_dados_template(df_semana)
    html = montar_html(dados_template)

    html_path = "/tmp/_relatorio_tmp.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    HTML(filename=html_path).write_pdf(saida_pdf)
    print(f"✓ Relatório gerado: {saida_pdf}")
    print(f"  Período: {dados_template['periodo']} | Registros: {dados_template['registros']}")

if __name__ == "__main__":
    main()
