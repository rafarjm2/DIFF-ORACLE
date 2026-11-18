/*==============================================================*/
/* DIFF: ATURMA100 - aplicar em HOMOL_DPF06H                    */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

PROMPT ==========================================================
PROMPT DIAGNOSTICO - confirmar ausencia antes de criar
PROMPT ==========================================================
SELECT owner, table_name, status FROM dba_tables
WHERE owner = 'ATURMA100' AND table_name IN ('TB_LINK_MIDIA_TURMA');
-- Esperado: 0 linhas.

SELECT sequence_owner, sequence_name FROM dba_sequences
WHERE sequence_owner = 'ATURMA100' AND sequence_name IN ('SQ_INSTRUTOR_TURMA_DISCIPLINA','SQ_LINK_MIDIA_TURMA','SQ_TB_LINK_MIDIA_TURMA');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Sequences                                                      */
/*==============================================================*/
create sequence ATURMA100.SQ_INSTRUTOR_TURMA_DISCIPLINA
increment by 1
start with 1065
nocycle
nocache;

grant SELECT on ATURMA100.SQ_INSTRUTOR_TURMA_DISCIPLINA to ATURMAUSR;
create or replace synonym ATURMAUSR.SQ_INSTRUTOR_TURMA_DISCIPLINA
   for ATURMA100.SQ_INSTRUTOR_TURMA_DISCIPLINA;

create sequence ATURMA100.SQ_LINK_MIDIA_TURMA
increment by 1
start with 17
nocycle
nocache;

grant SELECT on ATURMA100.SQ_LINK_MIDIA_TURMA to ATURMAUSR;
create or replace synonym ATURMAUSR.SQ_LINK_MIDIA_TURMA
   for ATURMA100.SQ_LINK_MIDIA_TURMA;

create sequence ATURMA100.SQ_TB_LINK_MIDIA_TURMA
increment by 1
start with 2
nocycle
nocache;

grant SELECT on ATURMA100.SQ_TB_LINK_MIDIA_TURMA to ATURMAUSR;
create or replace synonym ATURMAUSR.SQ_TB_LINK_MIDIA_TURMA
   for ATURMA100.SQ_TB_LINK_MIDIA_TURMA;

/*==============================================================*/
/* Table: TB_LINK_MIDIA_TURMA                                   */
/*==============================================================*/
CREATE TABLE "ATURMA100"."TB_LINK_MIDIA_TURMA" 
   (	"ID_LINK_MIDIA_TURMA" NUMBER NOT NULL ENABLE, 
	"ID_TURMA" NUMBER NOT NULL ENABLE, 
	"NO_MIDIA" VARCHAR2(200) NOT NULL ENABLE, 
	"LK_MIDIA" VARCHAR2(500) NOT NULL ENABLE, 
	"DS_MIDIA" VARCHAR2(500), 
	"DT_INCLUSAO_MIDIA" DATE DEFAULT SYSDATE NOT NULL ENABLE, 
	 CONSTRAINT "PK_TB_LINK_MIDIA_TURMA" PRIMARY KEY ("ID_LINK_MIDIA_TURMA")
  USING INDEX  ENABLE, 
	 CONSTRAINT "FK_LINK_MIDIA_TURMA_TURMA" FOREIGN KEY ("ID_TURMA")
	  REFERENCES "ATURMA100"."TB_TURMA" ("ID_TURMA") ENABLE
   ) ;

comment on table ATURMA100.TB_LINK_MIDIA_TURMA is
'Armazena links de midia (video, imagem, documento, etc) associados a uma turma.';
comment on column ATURMA100.TB_LINK_MIDIA_TURMA.ID_LINK_MIDIA_TURMA is
'Identificador unico do registro (sequencia numerica).';
comment on column ATURMA100.TB_LINK_MIDIA_TURMA.ID_TURMA is
'Referencia a turma associada, em TB_TURMA.';
comment on column ATURMA100.TB_LINK_MIDIA_TURMA.NO_MIDIA is
'Nome ou titulo da midia.';
comment on column ATURMA100.TB_LINK_MIDIA_TURMA.LK_MIDIA is
'Link (URL) de acesso a midia.';
comment on column ATURMA100.TB_LINK_MIDIA_TURMA.DS_MIDIA is
'Descricao complementar da midia (campo opcional).';
comment on column ATURMA100.TB_LINK_MIDIA_TURMA.DT_INCLUSAO_MIDIA is
'Data de inclusao do registro (default sysdate).';

grant DELETE,INSERT,SELECT,UPDATE on ATURMA100.TB_LINK_MIDIA_TURMA to ATURMAUSR;

create or replace synonym ATURMAUSR.TB_LINK_MIDIA_TURMA
   for ATURMA100.TB_LINK_MIDIA_TURMA;

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do usuario de servico configurado, ou aponta   */
/* para objeto que precisa ser confirmado antes de criar)         */
/*==============================================================*/
-- PMRA5012148.SQ_MUDANCA_PRAZO_NOTIFICACAO -> ATURMA100.SQ_MUDANCA_PRAZO_NOTIFICACAO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.SQ_MUDANCA_PRAZO_NOTIFICACAO existe de fato antes de criar)
-- PMRA5012148.TB_MUDANCA_PRAZO_NOTIFICACAO -> ATURMA100.TB_MUDANCA_PRAZO_NOTIFICACAO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.TB_MUDANCA_PRAZO_NOTIFICACAO existe de fato antes de criar)
