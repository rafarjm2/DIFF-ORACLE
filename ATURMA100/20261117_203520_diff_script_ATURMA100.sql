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

/*==============================================================*/
/* Ajustes de coluna (DEFAULT / NOT NULL / tipo) - REVISAR       */
/* Direcao assumida: destino se alinha a origem.                  */
/*==============================================================*/
-- ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tab_columns WHERE owner = 'ATURMA100' AND table_name = 'TB_PESSOA_FISICA' AND column_name = 'ST_SITUACAO_CADASTRO' AND nullable = 'N';
  IF v_qtd > 0 THEN
    EXECUTE IMMEDIATE q'[ALTER TABLE ATURMA100.TB_PESSOA_FISICA MODIFY (ST_SITUACAO_CADASTRO NULL)]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: NULL ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): NULL ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em NULL ATURMA100.TB_PESSOA_FISICA.ST_SITUACAO_CADASTRO: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

/*==============================================================*/
/* Constraints com MESMO NOME e definicao diferente - COMENTADO.  */
/* Oracle nao tem ALTER da regra: e DROP + recriar. Confira antes */
/* se a tabela tem dado que viola a definicao da origem.          */
/*==============================================================*/
-- ATURMA100.TB_PENDENCIA_ALUNO.CC_PEND_ALUNO_FALHA_VERIF: destino=[ST_FALHA_VERIFICACAO IN ('S', 'N')] | origem=[ST_FALHA_VERIFICACAO IN ('S','N')]
-- ALTER TABLE ATURMA100.TB_PENDENCIA_ALUNO DROP CONSTRAINT CC_PEND_ALUNO_FALHA_VERIF;
-- ALTER TABLE "ATURMA100"."TB_PENDENCIA_ALUNO" ADD CONSTRAINT "CC_PEND_ALUNO_FALHA_VERIF" CHECK (ST_FALHA_VERIFICACAO IN ('S','N')) ENABLE;

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
