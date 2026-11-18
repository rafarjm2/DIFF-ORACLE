/*==============================================================*/
/* DIFF: ATURMA100 - aplicar em HOMOL_DPF06H                    */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

SET DEFINE OFF
SET SERVEROUTPUT ON
SET SQLBLANKLINES ON

PROMPT ==========================================================
PROMPT DIAGNOSTICO - confirmar ausencia antes de criar
PROMPT ==========================================================
SELECT owner, table_name, status FROM dba_tables
WHERE owner = 'ATURMA100' AND table_name IN ('TB_SITUACAO_VERIFICACAO');
-- Esperado: 0 linhas.

SELECT sequence_owner, sequence_name FROM dba_sequences
WHERE sequence_owner = 'ATURMA100' AND sequence_name IN ('SQ_NR_TURMA');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Sequences                                                      */
/*==============================================================*/
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_sequences WHERE sequence_owner = 'ATURMA100' AND sequence_name = 'SQ_NR_TURMA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[create sequence ATURMA100.SQ_NR_TURMA
increment by 1
start with 1577
nocycle
cache 20]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: SEQUENCE ATURMA100.SQ_NR_TURMA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): SEQUENCE ATURMA100.SQ_NR_TURMA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em SEQUENCE ATURMA100.SQ_NR_TURMA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

grant SELECT on ATURMA100.SQ_NR_TURMA to ATURMAUSR;
create or replace synonym ATURMAUSR.SQ_NR_TURMA
   for ATURMA100.SQ_NR_TURMA;

/*==============================================================*/
/* Table: TB_SITUACAO_VERIFICACAO                               */
/*==============================================================*/
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tables WHERE owner = 'ATURMA100' AND table_name = 'TB_SITUACAO_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[CREATE TABLE "ATURMA100"."TB_SITUACAO_VERIFICACAO" 
   (	"ID_SITUACAO_VERIFICACAO" NUMBER(2,0) NOT NULL ENABLE, 
	"NO_SITUACAO_VERIFICACAO" VARCHAR2(60) NOT NULL ENABLE, 
	"ST_ATIVO" CHAR(1) DEFAULT 'S' NOT NULL ENABLE, 
	 CONSTRAINT "CC_SITUACAO_VERIFICACAO_ATIVO" CHECK (ST_ATIVO IN ('S', 'N')) ENABLE, 
	 CONSTRAINT "PK_SITUACAO_VERIFICACAO" PRIMARY KEY ("ID_SITUACAO_VERIFICACAO")
  USING INDEX  ENABLE
   )]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: TABLE ATURMA100.TB_SITUACAO_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): TABLE ATURMA100.TB_SITUACAO_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em TABLE ATURMA100.TB_SITUACAO_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

comment on table ATURMA100.TB_SITUACAO_VERIFICACAO is
'Tabela de referencia das situacoes de verificacao retornadas por sistemas externos (SERMIL, STI-MAR, TSE, SINPRO, SNIC).';
comment on column ATURMA100.TB_SITUACAO_VERIFICACAO.ID_SITUACAO_VERIFICACAO is
'Identificador unico sequencial da situacao de verificacao de sistema externo.';
comment on column ATURMA100.TB_SITUACAO_VERIFICACAO.NO_SITUACAO_VERIFICACAO is
'Descricao da situacao de verificacao retornada por sistema externo (ex.: SERMIL, STI-MAR, TSE, SINPRO, SNIC).';
comment on column ATURMA100.TB_SITUACAO_VERIFICACAO.ST_ATIVO is
'Indicador de registro ativo (S = ativo, N = inativo).';

grant DELETE,INSERT,SELECT,UPDATE on ATURMA100.TB_SITUACAO_VERIFICACAO to ATURMAUSR;

create or replace synonym ATURMAUSR.TB_SITUACAO_VERIFICACAO
   for ATURMA100.TB_SITUACAO_VERIFICACAO;

PROMPT DIAGNOSTICO - colunas a adicionar
SELECT table_name, column_name FROM dba_tab_columns
WHERE owner = 'ATURMA100' AND (table_name, column_name) IN (('TB_HISTORICO_SITUACAO_TURMA','DS_JUSTIFICATIVA'),('TB_NOTIFICACAO_TURMA','NR_CPF_USUARIO_CIENCIA'),('TB_PENDENCIA_ALUNO','DS_RETORNO_VERIFICACAO'),('TB_PENDENCIA_ALUNO','ID_SITUACAO_VERIFICACAO'),('TB_PENDENCIA_ALUNO','ST_FALHA_VERIFICACAO'),('TB_PESSOA_FISICA','ST_SITUACAO_CADASTRO'),('TB_TURMA','DT_PROCESSO_TURMA'));
-- Esperado: 0 linhas.

/*==============================================================*/
/* Colunas faltantes em tabela existente                          */
/*==============================================================*/
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_HISTORICO_SITUACAO_TURMA' AND column_name = 'DS_JUSTIFICATIVA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_HISTORICO_SITUACAO_TURMA ADD (DS_JUSTIFICATIVA VARCHAR2(4000))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA is
'Justificativa informada pelo usuario para a acao registrada no historico';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_NOTIFICACAO_TURMA' AND column_name = 'NR_CPF_USUARIO_CIENCIA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_NOTIFICACAO_TURMA ADD (NR_CPF_USUARIO_CIENCIA VARCHAR2(11))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA is
'CPF do usuario da Escola de Formacao que registrou a ciencia da notificacao';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_PENDENCIA_ALUNO' AND column_name = 'ST_FALHA_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_PENDENCIA_ALUNO ADD (ST_FALHA_VERIFICACAO CHAR(1) DEFAULT 'N' NOT NULL)]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO is
'S = a consulta ao sistema responsavel nao pode ser concluida (indisponibilidade, falha de comunicacao, erro ou ausencia de resposta) e a pesquisa deve ser feita manualmente pela DELESP; N = pendencia identificada pelo sistema responsavel (default)';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_PENDENCIA_ALUNO' AND column_name = 'ID_SITUACAO_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_PENDENCIA_ALUNO ADD (ID_SITUACAO_VERIFICACAO NUMBER(2))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO is
'Situacao retornada na verificacao do sistema externo (SituacaoSistemaEnum). Nulo em registros anteriores a HU056.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_PENDENCIA_ALUNO' AND column_name = 'DS_RETORNO_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_PENDENCIA_ALUNO ADD (DS_RETORNO_VERIFICACAO VARCHAR2(255))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO is
'Descricao retornada pelo sistema externo na verificacao.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_PESSOA_FISICA' AND column_name = 'ST_SITUACAO_CADASTRO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_PESSOA_FISICA ADD (ST_SITUACAO_CADASTRO CHAR(2) DEFAULT 'RA')]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO is
'Situacao do cadastro da pessoa fisica. Valores validos: RA - Rascunho (default), AP - Aprovado, PP - Possui Pendencia, JP - Justificada Pendencia.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_TURMA' AND column_name = 'DT_PROCESSO_TURMA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_TURMA ADD (DT_PROCESSO_TURMA DATE DEFAULT TRUNC(SYSDATE) NOT NULL)]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100.TB_TURMA.DT_PROCESSO_TURMA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100.TB_TURMA.DT_PROCESSO_TURMA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100.TB_TURMA.DT_PROCESSO_TURMA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100.TB_TURMA.DT_PROCESSO_TURMA is
'Data de criacao do processo da turma no GESP3 Internet. 
         Cada turma cadastrada pela escola gera um processo analisado e homologado pela DELESP no GESP3 Intranet. 
      Preenchida pelo sistema no cadastro da turma (nao digitada). Difere da data de inicio da turma, informada pela escola, que pode ser anterior em cadastro retroativo. Exibida na Intranet conforme HU069.';

PROMPT DIAGNOSTICO - constraints a criar
SELECT owner, table_name, constraint_name, status FROM dba_constraints
WHERE owner = 'ATURMA100' AND constraint_name IN ('CC_PEND_ALUNO_FALHA_VERIF','CC_PESSOA_FISICA_ST_CADASTRO','UK_TURMA_AN_NR_TURMA');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Constraints faltantes (PK / UK / CHECK)                        */
/*==============================================================*/
-- ATURMA100.TB_PENDENCIA_ALUNO.CC_PEND_ALUNO_FALHA_VERIF
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_constraints WHERE owner = 'ATURMA100' AND constraint_name = 'CC_PEND_ALUNO_FALHA_VERIF';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE "ATURMA100"."TB_PENDENCIA_ALUNO" ADD CONSTRAINT "CC_PEND_ALUNO_FALHA_VERIF" CHECK (ST_FALHA_VERIFICACAO IN ('S','N')) ENABLE]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: CONSTRAINT ATURMA100.CC_PEND_ALUNO_FALHA_VERIF');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): CONSTRAINT ATURMA100.CC_PEND_ALUNO_FALHA_VERIF');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em CONSTRAINT ATURMA100.CC_PEND_ALUNO_FALHA_VERIF: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

-- ATURMA100.TB_PESSOA_FISICA.CC_PESSOA_FISICA_ST_CADASTRO
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_constraints WHERE owner = 'ATURMA100' AND constraint_name = 'CC_PESSOA_FISICA_ST_CADASTRO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE "ATURMA100"."TB_PESSOA_FISICA" ADD CONSTRAINT "CC_PESSOA_FISICA_ST_CADASTRO" CHECK (ST_SITUACAO_CADASTRO IN ('RA', 'AP', 'PP', 'JP')) ENABLE]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: CONSTRAINT ATURMA100.CC_PESSOA_FISICA_ST_CADASTRO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): CONSTRAINT ATURMA100.CC_PESSOA_FISICA_ST_CADASTRO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em CONSTRAINT ATURMA100.CC_PESSOA_FISICA_ST_CADASTRO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

-- ATURMA100.TB_TURMA.UK_TURMA_AN_NR_TURMA
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_constraints WHERE owner = 'ATURMA100' AND constraint_name = 'UK_TURMA_AN_NR_TURMA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE "ATURMA100"."TB_TURMA" ADD CONSTRAINT "UK_TURMA_AN_NR_TURMA" UNIQUE ("AN_TURMA", "NR_TURMA")
  USING INDEX  ENABLE]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: CONSTRAINT ATURMA100.UK_TURMA_AN_NR_TURMA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): CONSTRAINT ATURMA100.UK_TURMA_AN_NR_TURMA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em CONSTRAINT ATURMA100.UK_TURMA_AN_NR_TURMA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

/*==============================================================*/
/* Constraints que existem SO NO DESTINO - decida (nada e gerado) */
/*==============================================================*/
-- ATURMA100.TB_ALUNO_TURMA.CC_ALUNO_ST_CADASTRO ("ST_SITUACAO_CADASTRO"='RA' OR "ST_SITUACAO_CADASTRO"='AP' OR "ST_SITUACAO_CADASTRO"='PP' OR "ST_SITUACAO_CADASTRO"='JP')
-- ALTER TABLE ATURMA100.TB_ALUNO_TURMA DROP CONSTRAINT CC_ALUNO_ST_CADASTRO;

/*==============================================================*/
/* Sinonimos que existem nos dois lados mas apontam para alvos    */
/* diferentes - COMENTADO: repontar muda o comportamento.         */
/*==============================================================*/
-- PMRA5012148.SQ_MUDANCA_PRAZO_NOTIFICACAO: destino=APROBAN100.SQ_MUDANCA_PRAZO_NOTIFICACAO | origem=ATURMA100.SQ_MUDANCA_PRAZO_NOTIFICACAO
-- create or replace synonym PMRA5012148.SQ_MUDANCA_PRAZO_NOTIFICACAO
--    for ATURMA100.SQ_MUDANCA_PRAZO_NOTIFICACAO;

-- PMRA5012148.TB_MUDANCA_PRAZO_NOTIFICACAO: destino=APROBAN100.TB_MUDANCA_PRAZO_NOTIFICACAO | origem=ATURMA100.TB_MUDANCA_PRAZO_NOTIFICACAO
-- create or replace synonym PMRA5012148.TB_MUDANCA_PRAZO_NOTIFICACAO
--    for ATURMA100.TB_MUDANCA_PRAZO_NOTIFICACAO;

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do configurado, ou aponta para objeto que      */
/* precisa ser confirmado antes de criar)                         */
/*==============================================================*/
-- ATURMAUSR.SEQ_CURSO_PRE_REQUISITO -> ATURMA100.SEQ_CURSO_PRE_REQUISITO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.SEQ_CURSO_PRE_REQUISITO existe de fato antes de criar)
-- ATURMAUSR.SQ_HISTORICO_SITUACAO_PF -> ATURMA100.SQ_HISTORICO_SITUACAO_PF (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.SQ_HISTORICO_SITUACAO_PF existe de fato antes de criar)
-- ATURMAUSR.TB_HISTORICO_SITUACAO_PF -> ATURMA100.TB_HISTORICO_SITUACAO_PF (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.TB_HISTORICO_SITUACAO_PF existe de fato antes de criar)
-- PUBLIC.SQ_LINK_MIDIA_TURMA -> ATURMA100.SQ_LINK_MIDIA_TURMA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.SQ_LINK_MIDIA_TURMA existe de fato antes de criar)
-- PUBLIC.TB_LINK_MIDIA_TURMA -> ATURMA100.TB_LINK_MIDIA_TURMA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100.TB_LINK_MIDIA_TURMA existe de fato antes de criar)

PROMPT DIAGNOSTICO - foreign keys a criar
SELECT owner, table_name, constraint_name, status FROM dba_constraints
WHERE owner = 'ATURMA100' AND constraint_name IN ('FK_PENDENCIA_ALUNO_SIT_VERIF');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Foreign keys - aplicar POR ULTIMO                              */
/* (depende das tabelas e das PKs referenciadas ja existirem;     */
/* se a tabela pai fica em outro schema, rode aquele script antes)*/
/*==============================================================*/
-- ATURMA100.TB_PENDENCIA_ALUNO.FK_PENDENCIA_ALUNO_SIT_VERIF -> ATURMA100.TB_SITUACAO_VERIFICACAO
-- confirme que ATURMA100.TB_SITUACAO_VERIFICACAO existe no destino antes de aplicar
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_constraints WHERE owner = 'ATURMA100' AND constraint_name = 'FK_PENDENCIA_ALUNO_SIT_VERIF';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE "ATURMA100"."TB_PENDENCIA_ALUNO" ADD CONSTRAINT "FK_PENDENCIA_ALUNO_SIT_VERIF" FOREIGN KEY ("ID_SITUACAO_VERIFICACAO")
	  REFERENCES "ATURMA100"."TB_SITUACAO_VERIFICACAO" ("ID_SITUACAO_VERIFICACAO") ENABLE]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: FK ATURMA100.FK_PENDENCIA_ALUNO_SIT_VERIF');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): FK ATURMA100.FK_PENDENCIA_ALUNO_SIT_VERIF');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em FK ATURMA100.FK_PENDENCIA_ALUNO_SIT_VERIF: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
