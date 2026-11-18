/*==============================================================*/
/* DIFF: APROBAN100_AUDIT - aplicar em HOMOL_DPF06H             */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

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

/*==============================================================*/
/* Colunas faltantes em tabela existente                          */
/*==============================================================*/
ALTER TABLE APROBAN100_AUDIT.H_TB_INSTITUICAO_FINANCEIRA ADD (ID_PLANO_SEGURANCA NUMBER);

ALTER TABLE APROBAN100_AUDIT.H_TB_PLANO_SEGURANCA ADD (TP_DISP_PRIVACIDADE_GUICHE CHAR(1));
comment on column APROBAN100_AUDIT.H_TB_PLANO_SEGURANCA.TP_DISP_PRIVACIDADE_GUICHE is
'Indentifica o tipo de dispositivo de privacidade de guiche';

COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CAIXA_ELETRONICO"."IC_LOCALIZACAO_AUTOATENDIMENTO" IS 'Identifica se o caixa eletrônico é um auto atendimento externo S - Sim , N - Não .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CAIXA_ELETRONICO"."IC_LOCALIZACAO_INTERIOR" IS 'Identifica se o caixa eletrônico encontra-se no interior da agência. S - Sim , N - Não .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CAIXA_ELETRONICO"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CFTV"."ID_CFTV" IS 'Identificador único sequencial automático .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CFTV"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CNTO_FORNECEDOR_ALARME"."ID_CNTO_FORNECEDOR_ALARME" IS 'Identificador único sequencial automático .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_CNTO_FORNECEDOR_ALARME"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_FORNECEDOR_ALARME"."ID_FORNECEDOR_ALARME" IS 'Identificador único sequencial automático .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_FORNECEDOR_ALARME"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_GRU_PROCESSO_BANCARIO"."NR_ANO_VIGENCIA" IS 'Informação referente ao ano de vigência abrangido pela GRU. 1 - Primeiro ano de vigência, 2 - Segundo ano de vigência, 3 - Terceiro ano de vigência.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_HORARIO_FNCTO_AGENCIA"."ID_HORARIO_FNCTO_AGENCIA" IS 'Identificador único sequencial automático .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_HORARIO_FNCTO_AGENCIA"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_INSTALACAO_FISICA"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_PROCESSO_BANCARIO"."DS_JUSTIFICATIVA_RPRVCO_DELESP" IS 'Descrição da Justificativa de Reprovação da DELESP.';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_PROCESSO_BANCARIO"."DS_JUSTIFICATIVA_RPRVCO_DREX" IS 'Descrição da Justificativa de Reprovação da DREX .';
COMMENT ON COLUMN "APROBAN100_AUDIT"."H_TB_VISTORIA"."ID_PLANO_SEGURANCA" IS 'Chave primária da tabela de processo bancário. Campo populado por sequence. Utilizado como chave estrangeira.';
-- Nenhuma tabela de domínio configurada para o ambiente 'APROBAN100_AUDIT - Pré-homol_Homol'.