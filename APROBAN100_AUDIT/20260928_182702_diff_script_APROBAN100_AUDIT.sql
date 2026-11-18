/*==============================================================*/
/* DIFF: APROBAN100_AUDIT - aplicar em HOMOL_DPF06H             */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

PROMPT ==========================================================
PROMPT DIAGNOSTICO - confirmar ausencia antes de criar
PROMPT ==========================================================
SELECT owner, table_name, status FROM dba_tables
WHERE owner = 'APROBAN100_AUDIT' AND table_name IN ('H_TB_ANEXO_NTFCO_PROCESSO_BNCRO');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Table: H_TB_ANEXO_NTFCO_PROCESSO_BNCRO                       */
/*==============================================================*/
CREATE TABLE "APROBAN100_AUDIT"."H_TB_ANEXO_NTFCO_PROCESSO_BNCRO" 
   (	"ID_CONTROLE_AUDITORIA" NUMBER(10,0) NOT NULL ENABLE, 
	"IC_CONTROLE_AUDITORIA" VARCHAR2(1) NOT NULL ENABLE, 
	"ID_NOTIFICACAO_PROCESSO_BANCARIO" NUMBER, 
	"ID_ANEXO" NUMBER, 
	 CONSTRAINT "CK_ID_ANEXO_NOTIF" CHECK ("ID_ANEXO" IS NOT NULL) ENABLE, 
	 CONSTRAINT "CK_ID_NOTIF_PROCESSO" CHECK ("ID_NOTIFICACAO_PROCESSO_BANCARIO" IS NOT NULL) ENABLE, 
	 CONSTRAINT "CC_ANEXO_NOTIF_PROCNACARIO_CTRLE_ADIT" CHECK (IC_CONTROLE_AUDITORIA IN (0, 1, 2)) ENABLE, 
	 CONSTRAINT "FK_ANEXO_CNTRE_ADIT_PROC_BANCARIO" FOREIGN KEY ("ID_CONTROLE_AUDITORIA")
	  REFERENCES "APROBAN100_AUDIT"."TB_CONTROLE_AUDITORIA" ("ID_CONTROLE_AUDITORIA") ENABLE
   ) ;

comment on table APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO is
'Tabela associativa que relaciona os anexos as notificacoes de processos bancarios';
comment on column APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO.ID_CONTROLE_AUDITORIA is
'Identificador da Tabela de Controle de Auditoria.';
comment on column APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO.IC_CONTROLE_AUDITORIA is
'Identifica o tipo de operacao realizada, adotando-se: 0- Registro adicionado, 1- Registro modificado ou 2- Registro deletado.';
comment on column APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO.ID_NOTIFICACAO_PROCESSO_BANCARIO is
'Identificador da notificacao do processo bancario';
comment on column APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO.ID_ANEXO is
'Identificador do anexo vinculado a notificacao';

grant INSERT,SELECT on APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO to APROBANUSR;

create or replace synonym APROBANUSR.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO
   for APROBAN100_AUDIT.H_TB_ANEXO_NTFCO_PROCESSO_BNCRO;

/*==============================================================*/
/* Colunas faltantes em tabela existente                          */
/*==============================================================*/
ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (IC_ORIGEM_RELATORIO NUMBER(1));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.IC_ORIGEM_RELATORIO is
'Origem do Relatorio de Vistoria: 1 = gerado automaticamente pelo GESP3 na Renovacao do Plano de Seguranca (1o Ano de Vigencia); 2 = gerado automaticamente pelo GESP3 na Renovacao do Plano de Seguranca (2o Ano de Vigencia); 3 = relatorio criado pelo analista ou anexado externamente (default)';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (IC_AVALIACAO VARCHAR2(1));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.IC_AVALIACAO is
'Avaliacao do Relatorio de Vistoria finalizado: S=Aprovado, N=Reprovado';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (DS_JUSTIFICATIVA_AVALIACAO VARCHAR2(4000));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.DS_JUSTIFICATIVA_AVALIACAO is
'Justificativa obrigatoria quando IC_AVALIACAO = N (Reprovado)';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (NR_CPF_USUARIO_AVALIACAO VARCHAR2(11));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.NR_CPF_USUARIO_AVALIACAO is
'CPF do analista que registrou a avaliacao do relatorio';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (DH_AVALIACAO TIMESTAMP(6));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.DH_AVALIACAO is
'Data/hora do registro da avaliacao do relatorio';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (NO_USUARIO_FINALIZACAO VARCHAR2(200));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.NO_USUARIO_FINALIZACAO is
'Nome do analista que finalizou o Relatorio de Vistoria, registrado no momento da finalizacao';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (NR_MATRICULA_USUARIO_FINALIZACAO VARCHAR2(20));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.NR_MATRICULA_USUARIO_FINALIZACAO is
'Matricula do analista que finalizou o Relatorio de Vistoria, registrada no momento da finalizacao';

ALTER TABLE APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO ADD (SG_UNIDADE_USUARIO_FINALIZACAO VARCHAR2(100));
comment on column APROBAN100_AUDIT.H_TB_RELATORIO_VISTORIA_PROCESSO.SG_UNIDADE_USUARIO_FINALIZACAO is
'Sigla da unidade (lotacao ou exercicio) do analista que finalizou o Relatorio de Vistoria, registrada no momento da finalizacao';

/*==============================================================*/
/* Ajustes de coluna (DEFAULT / NOT NULL / tipo) - REVISAR       */
/* Direcao assumida: destino se alinha a origem.                  */
/*==============================================================*/
-- APROBAN100_AUDIT.H_TB_ALARME.DS_TP_ACIONA_ALARME_REDUNDANTE: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE APROBAN100_AUDIT.H_TB_ALARME MODIFY (DS_TP_ACIONA_ALARME_REDUNDANTE NULL);

/*==============================================================*/
/* Ordem fisica das colunas diverge - NAO ha ALTER que reordene.  */
/* Impacto: INSERT sem lista de colunas e SELECT *. Corrigir      */
/* exige recriar a tabela (CTAS + rename) em janela controlada.   */
/*==============================================================*/
-- APROBAN100_AUDIT.H_TB_PLANO_SEGURANCA: conferir ordem no relatorio de diferencas
