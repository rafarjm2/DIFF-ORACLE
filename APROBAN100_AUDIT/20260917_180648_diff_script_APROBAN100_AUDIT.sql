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
WHERE owner = 'APROBAN100_AUDIT' AND table_name IN ('H_TB_ANEXO_NTFCO_PROCESSO_BNCRO','H_TB_MOVIMENTACAO_PROCESSO');
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
/* Table: H_TB_MOVIMENTACAO_PROCESSO                            */
/*==============================================================*/
CREATE TABLE "APROBAN100_AUDIT"."H_TB_MOVIMENTACAO_PROCESSO" 
   (	"ID_MOVIMENTACAO_PROCESSO" NUMBER(19,0) NOT NULL ENABLE, 
	"ID_PROCESSO_BANCARIO" NUMBER(19,0) NOT NULL ENABLE, 
	"IC_TIPO_MOVIMENTACAO" VARCHAR2(3) NOT NULL ENABLE, 
	"ID_SITUACAO_ORIGEM" NUMBER(19,0), 
	"ID_SITUACAO_DESTINO" NUMBER(19,0), 
	"NR_CPF_USUARIO_OPERACAO" NUMBER(11,0) NOT NULL ENABLE, 
	"NR_CPF_RESPONSAVEL_ANTERIOR" NUMBER(11,0), 
	"NR_CPF_RESPONSAVEL_NOVO" NUMBER(11,0), 
	"ID_DOCUMENTO_PROCESSO" NUMBER(19,0), 
	"DS_JUSTIFICATIVA" VARCHAR2(500), 
	"DS_OBSERVACAO" VARCHAR2(1000), 
	"DH_MOVIMENTACAO" TIMESTAMP (6) NOT NULL ENABLE, 
	"ID_CONTROLE_AUDITORIA" NUMBER(19,0) NOT NULL ENABLE, 
	 CONSTRAINT "PK_H_MOVIMENTACAO_PROCESSO" PRIMARY KEY ("ID_MOVIMENTACAO_PROCESSO", "ID_CONTROLE_AUDITORIA")
  USING INDEX  ENABLE, 
	 CONSTRAINT "FK_HMOVPROC_CTL_AUDITORIA" FOREIGN KEY ("ID_CONTROLE_AUDITORIA")
	  REFERENCES "APROBAN100_AUDIT"."TB_CONTROLE_AUDITORIA" ("ID_CONTROLE_AUDITORIA") ENABLE
   ) ;

comment on table APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO is
'Historico de auditoria de APROBAN100.TB_MOVIMENTACAO_PROCESSO';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.ID_MOVIMENTACAO_PROCESSO is
'Identificador da movimentacao de processo (origem)';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.ID_PROCESSO_BANCARIO is
'Identificador do processo bancario';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.IC_TIPO_MOVIMENTACAO is
'Indicador do tipo de movimentacao';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.ID_SITUACAO_ORIGEM is
'Identificador da situacao de origem';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.ID_SITUACAO_DESTINO is
'Identificador da situacao de destino';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.NR_CPF_USUARIO_OPERACAO is
'CPF do usuario que realizou a operacao';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.NR_CPF_RESPONSAVEL_ANTERIOR is
'CPF do responsavel anterior';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.NR_CPF_RESPONSAVEL_NOVO is
'CPF do novo responsavel';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.ID_DOCUMENTO_PROCESSO is
'Identificador do documento do processo';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.DS_JUSTIFICATIVA is
'Justificativa da movimentacao';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.DS_OBSERVACAO is
'Observacao da movimentacao';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.DH_MOVIMENTACAO is
'Data e hora da movimentacao';
comment on column APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO.ID_CONTROLE_AUDITORIA is
'Identificador do controle de auditoria';

grant INSERT,SELECT on APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO to APROBANUSR;

create or replace synonym APROBANUSR.H_TB_MOVIMENTACAO_PROCESSO
   for APROBAN100_AUDIT.H_TB_MOVIMENTACAO_PROCESSO;
