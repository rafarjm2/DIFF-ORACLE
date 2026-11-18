/*==============================================================*/
/* DIFF: ATURMA100_AUDIT - aplicar em HOMOL_DPF06H              */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

SET DEFINE OFF
SET SERVEROUTPUT ON
SET SQLBLANKLINES ON

PROMPT DIAGNOSTICO - colunas a adicionar
SELECT table_name, column_name FROM dba_tab_columns
WHERE owner = 'ATURMA100_AUDIT' AND (table_name, column_name) IN (('H_TB_HISTORICO_SITUACAO_TURMA','DS_JUSTIFICATIVA'),('H_TB_NOTIFICACAO_TURMA','NR_CPF_USUARIO_CIENCIA'),('H_TB_PENDENCIA_ALUNO','DS_RETORNO_VERIFICACAO'),('H_TB_PENDENCIA_ALUNO','ID_SITUACAO_VERIFICACAO'),('H_TB_PENDENCIA_ALUNO','ST_FALHA_VERIFICACAO'),('H_TB_PESSOA_FISICA','ST_SITUACAO_CADASTRO'),('H_TB_TURMA','DT_PROCESSO_TURMA'));
-- Esperado: 0 linhas.

/*==============================================================*/
/* Colunas faltantes em tabela existente                          */
/*==============================================================*/
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_HISTORICO_SITUACAO_TURMA' AND column_name = 'DS_JUSTIFICATIVA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_TURMA ADD (DS_JUSTIFICATIVA VARCHAR2(4000))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_TURMA.DS_JUSTIFICATIVA is
'Justificativa informada pelo usuario para a acao registrada no historico';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_NOTIFICACAO_TURMA' AND column_name = 'NR_CPF_USUARIO_CIENCIA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_NOTIFICACAO_TURMA ADD (NR_CPF_USUARIO_CIENCIA VARCHAR2(11))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_NOTIFICACAO_TURMA.NR_CPF_USUARIO_CIENCIA is
'CPF do usuario da Escola de Formacao que registrou a ciencia da notificacao';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_PENDENCIA_ALUNO' AND column_name = 'ST_FALHA_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO ADD (ST_FALHA_VERIFICACAO CHAR(1))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ST_FALHA_VERIFICACAO is
'S = a consulta ao sistema responsavel nao pode ser concluida (indisponibilidade, falha de comunicacao, erro ou ausencia de resposta) e a pesquisa deve ser feita manualmente pela DELESP; N = pendencia identificada pelo sistema responsavel. Reflete o valor da coluna correspondente em TB_PENDENCIA_ALUNO no momento da operacao de auditoria.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_PENDENCIA_ALUNO' AND column_name = 'ID_SITUACAO_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO ADD (ID_SITUACAO_VERIFICACAO NUMBER(2))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.ID_SITUACAO_VERIFICACAO is
'Situacao retornada na verificacao do sistema externo (SituacaoSistemaEnum). Nulo em registros anteriores a HU056.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_PENDENCIA_ALUNO' AND column_name = 'DS_RETORNO_VERIFICACAO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO ADD (DS_RETORNO_VERIFICACAO VARCHAR2(255))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_PENDENCIA_ALUNO.DS_RETORNO_VERIFICACAO is
'Descricao retornada pelo sistema externo na verificacao.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_PESSOA_FISICA' AND column_name = 'ST_SITUACAO_CADASTRO';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_PESSOA_FISICA ADD (ST_SITUACAO_CADASTRO CHAR(2))]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO is
'Situacao do cadastro da pessoa fisica. Valores validos: RA - Rascunho (default), AP - Aprovado, PP - Possui Pendencia, JP - Justificada Pendencia.';

DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100_AUDIT' AND table_name = 'H_TB_TURMA' AND column_name = 'DT_PROCESSO_TURMA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100_AUDIT.H_TB_TURMA ADD (DT_PROCESSO_TURMA DATE)]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: ADD COLUMN ATURMA100_AUDIT.H_TB_TURMA.DT_PROCESSO_TURMA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): ADD COLUMN ATURMA100_AUDIT.H_TB_TURMA.DT_PROCESSO_TURMA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em ADD COLUMN ATURMA100_AUDIT.H_TB_TURMA.DT_PROCESSO_TURMA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/
comment on column ATURMA100_AUDIT.H_TB_TURMA.DT_PROCESSO_TURMA is
'Data de criacao do processo da turma no GESP3 Internet. 
      Cada turma cadastrada pela escola gera um processo analisado e homologado pela DELESP no GESP3 Intranet. 
      Preenchida pelo sistema no cadastro da turma (nao digitada). Difere da data de inicio da turma, informada pela escola, que pode ser anterior em cadastro retroativo. Exibida na Intranet conforme HU069.';

/*==============================================================*/
/* Constraints que existem SO NO DESTINO - decida (nada e gerado) */
/*==============================================================*/
-- ATURMA100_AUDIT.H_TB_ALUNO_TURMA.CC_ALUNO_ST_CADASTRO ("ST_SITUACAO_CADASTRO" IS NULL OR "ST_SITUACAO_CADASTRO"='RA' OR "ST_SITUACAO_CADASTRO"='AP' OR "ST_SITUACAO_CADASTRO"='PP' OR "ST_SITUACAO_CADASTRO"='JP')
-- ALTER TABLE ATURMA100_AUDIT.H_TB_ALUNO_TURMA DROP CONSTRAINT CC_ALUNO_ST_CADASTRO;

/*==============================================================*/
/* Sinonimos que existem nos dois lados mas apontam para alvos    */
/* diferentes - COMENTADO: repontar muda o comportamento.         */
/*==============================================================*/
-- PMRA5012148.H_TB_MUDANCA_PRAZO_NOTIFICACAO: destino=APROBAN100_AUDIT.H_TB_MUDANCA_PRAZO_NOTIFICACAO | origem=ATURMA100_AUDIT.H_TB_MUDANCA_PRAZO_NOTIFICACAO
-- create or replace synonym PMRA5012148.H_TB_MUDANCA_PRAZO_NOTIFICACAO
--    for ATURMA100_AUDIT.H_TB_MUDANCA_PRAZO_NOTIFICACAO;

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do configurado, ou aponta para objeto que      */
/* precisa ser confirmado antes de criar)                         */
/*==============================================================*/
-- ATURMAUSR.H_TB_HISTORICO_SITUACAO_PF -> ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_PF (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100_AUDIT.H_TB_HISTORICO_SITUACAO_PF existe de fato antes de criar)
-- PUBLIC.H_TB_LINK_MIDIA_TURMA -> ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se ATURMA100_AUDIT.H_TB_LINK_MIDIA_TURMA existe de fato antes de criar)
