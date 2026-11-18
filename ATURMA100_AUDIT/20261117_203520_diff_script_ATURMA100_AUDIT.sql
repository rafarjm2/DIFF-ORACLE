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
