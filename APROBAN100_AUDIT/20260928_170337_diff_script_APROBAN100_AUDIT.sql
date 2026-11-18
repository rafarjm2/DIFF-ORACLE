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
