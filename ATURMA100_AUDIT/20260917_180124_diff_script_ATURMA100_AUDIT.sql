/*==============================================================*/
/* DIFF: ATURMA100_AUDIT - aplicar em HOMOL_DPF06H              */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

PROMPT ==========================================================
PROMPT DIAGNOSTICO - confirmar ausencia antes de criar
PROMPT ==========================================================
SELECT owner, table_name, status FROM dba_tables
WHERE owner = 'ATURMA100_AUDIT' AND table_name IN ('H_TB_LINK_MIDIA_TURMA');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Table: H_TB_LINK_MIDIA_TURMA                                 */
/*==============================================================*/
CREATE TABLE "ATURMA100_AUDIT"."H_TB_LINK_MIDIA_TURMA" 
   (	"ID_LINK_MIDIA_TURMA" NUMBER NOT NULL ENABLE, 
	"ID_TURMA" NUMBER NOT NULL ENABLE, 
	"NO_MIDIA" VARCHAR2(200) NOT NULL ENABLE, 
	"LK_MIDIA" VARCHAR2(500) NOT NULL ENABLE, 
	"DS_MIDIA" VARCHAR2(500), 
	"DT_INCLUSAO_MIDIA" DATE NOT NULL ENABLE, 
	"ID_CONTROLE_AUDITORIA" NUMBER NOT NULL ENABLE, 
	"TP_CONTROLE_AUDITORIA" NUMBER NOT NULL ENABLE, 
	 CONSTRAINT "CKC_TP_CTRL_AUDIT_H_LINK" CHECK (TP_CONTROLE_AUDITORIA in (0,1,2)) ENABLE, 
	 CONSTRAINT "PK_H_TB_LINK_MIDIA_TURMA" PRIMARY KEY ("ID_LINK_MIDIA_TURMA", "ID_CONTROLE_AUDITORIA")
  USING INDEX  ENABLE, 
	 CONSTRAINT "FK_H_LINK_MIDIA_CTRL_AUDIT" FOREIGN KEY ("ID_CONTROLE_AUDITORIA")
	  REFERENCES "ATURMA100_AUDIT"."TB_CONTROLE_AUDITORIA" ("ID_CONTROLE_AUDITORIA") ENABLE
   ) ;

comment on table ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA is
'Auditoria de ATURMA100.TB_LINK_MIDIA_TURMA (links de midia associados a uma turma).';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.ID_LINK_MIDIA_TURMA is
'Identificador unico do registro (sequencia numerica).';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.ID_TURMA is
'Referencia a turma associada, em TB_TURMA.';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.NO_MIDIA is
'Nome ou titulo da midia.';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.LK_MIDIA is
'Link (URL) de acesso a midia.';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.DS_MIDIA is
'Descricao complementar da midia (campo opcional).';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.DT_INCLUSAO_MIDIA is
'Data de inclusao do registro na tabela de origem.';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.ID_CONTROLE_AUDITORIA is
'Identificador da Tabela de Controle de Auditoria.';
comment on column ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA.TP_CONTROLE_AUDITORIA is
'Identifica o tipo de operacao realizada, adotando-se: 0- Registro adicionado, 1- Registro modificado ou 2- Registro deletado.';

grant INSERT,SELECT on ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA to ATURMAUSR;

create or replace synonym ATURMAUSR.H_TB_LINK_MIDIA_TURMA
   for ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA;

/*==============================================================*/
/* Ajustes de coluna (NOT NULL / tipo) - REVISAR antes de aplicar */
/* Direcao assumida: destino se alinha a origem.                  */
/*==============================================================*/
-- ATURMA100_AUDIT.H_TB_AVALIACAO_DOCUMENTO_TURMA.DH_AVALIACAO_DOCUMENTO_TURMA: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE ATURMA100_AUDIT.H_TB_AVALIACAO_DOCUMENTO_TURMA MODIFY (DH_AVALIACAO_DOCUMENTO_TURMA NULL);

-- ATURMA100_AUDIT.H_TB_CADASTRO_NACIONAL_VIGILANTE.DT_VALIDADE_REGISTRO_CNV: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE ATURMA100_AUDIT.H_TB_CADASTRO_NACIONAL_VIGILANTE MODIFY (DT_VALIDADE_REGISTRO_CNV NULL);

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do usuario de servico configurado, ou aponta   */
/* para objeto que precisa ser confirmado antes de criar)         */
/*==============================================================*/
-- PMRA5012148.H_TB_MUDANCA_PRAZO_NOTIFICACAO -> ATURMA100_AUDIT.H_TB_MUDANCA_PRAZO_NOTIFICACAO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100_AUDIT.H_TB_MUDANCA_PRAZO_NOTIFICACAO existe de fato antes de criar)
