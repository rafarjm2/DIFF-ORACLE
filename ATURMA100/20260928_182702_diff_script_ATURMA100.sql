/*==============================================================*/
/* DIFF: ATURMA100 - aplicar em HOMOL_DPF06H                    */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

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
