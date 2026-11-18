/*==============================================================*/
/* DIFF: AGESP300_AUDIT - aplicar em HOMOL_DPF06H               */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

/*==============================================================*/
/* Sinonimos que existem nos dois lados mas apontam para alvos    */
/* diferentes - COMENTADO: repontar muda o comportamento.         */
/*==============================================================*/
-- PMRA5012148.SQ_CONTROLE_AUDITORIA: destino=APROBAN100_AUDIT.SQ_CONTROLE_AUDITORIA | origem=AGESP300_AUDIT.SQ_CONTROLE_AUDITORIA
-- create or replace synonym PMRA5012148.SQ_CONTROLE_AUDITORIA
--    for AGESP300_AUDIT.SQ_CONTROLE_AUDITORIA;

-- PMRA5012148.TB_CONTROLE_AUDITORIA: destino=APROBAN100_AUDIT.TB_CONTROLE_AUDITORIA | origem=AGESP300_AUDIT.TB_CONTROLE_AUDITORIA
-- create or replace synonym PMRA5012148.TB_CONTROLE_AUDITORIA
--    for AGESP300_AUDIT.TB_CONTROLE_AUDITORIA;

-- PWDA11874.H_TB_ANEXO: destino=ATURMA100_AUDIT.H_TB_ANEXO | origem=AGESP300_AUDIT.H_TB_ANEXO
-- create or replace synonym PWDA11874.H_TB_ANEXO
--    for AGESP300_AUDIT.H_TB_ANEXO;

-- PWDA11874.H_TB_CONTATO: destino=ATURMA100_AUDIT.H_TB_CONTATO | origem=AGESP300_AUDIT.H_TB_CONTATO
-- create or replace synonym PWDA11874.H_TB_CONTATO
--    for AGESP300_AUDIT.H_TB_CONTATO;

-- PWDA11874.H_TB_GRU: destino=ATURMA100_AUDIT.H_TB_GRU | origem=AGESP300_AUDIT.H_TB_GRU
-- create or replace synonym PWDA11874.H_TB_GRU
--    for AGESP300_AUDIT.H_TB_GRU;

-- PWDA11874.H_TB_PESSOA_FISICA: destino=ATURMA100_AUDIT.H_TB_PESSOA_FISICA | origem=AGESP300_AUDIT.H_TB_PESSOA_FISICA
-- create or replace synonym PWDA11874.H_TB_PESSOA_FISICA
--    for AGESP300_AUDIT.H_TB_PESSOA_FISICA;

-- PWDA11874.SQ_CONTROLE_AUDITORIA: destino=ATURMA100_AUDIT.SQ_CONTROLE_AUDITORIA | origem=AGESP300_AUDIT.SQ_CONTROLE_AUDITORIA
-- create or replace synonym PWDA11874.SQ_CONTROLE_AUDITORIA
--    for AGESP300_AUDIT.SQ_CONTROLE_AUDITORIA;

-- PWDA11874.TB_CONTROLE_AUDITORIA: destino=ATURMA100_AUDIT.TB_CONTROLE_AUDITORIA | origem=AGESP300_AUDIT.TB_CONTROLE_AUDITORIA
-- create or replace synonym PWDA11874.TB_CONTROLE_AUDITORIA
--    for AGESP300_AUDIT.TB_CONTROLE_AUDITORIA;

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do configurado, ou aponta para objeto que      */
/* precisa ser confirmado antes de criar)                         */
/*==============================================================*/
-- AGESPUSR.H_TB_CONTATO_PESSOA -> AGESP300_AUDIT.H_TB_CONTATO_PESSOA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_CONTATO_PESSOA existe de fato antes de criar)
-- PMRA5012148.H_TB_TIPO_SITUACAO_EMPRESA -> AGESP300_AUDIT.H_TB_TIPO_SITUACAO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_TIPO_SITUACAO_EMPRESA existe de fato antes de criar)
-- PWDA11874.H_TB_ANEXO_EMPRESA_PROCESSO -> AGESP300_AUDIT.H_TB_ANEXO_EMPRESA_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_ANEXO_EMPRESA_PROCESSO existe de fato antes de criar)
-- PWDA11874.H_TB_ANEXO_PROCURADOR -> AGESP300_AUDIT.H_TB_ANEXO_PROCURADOR (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_ANEXO_PROCURADOR existe de fato antes de criar)
-- PWDA11874.H_TB_ESTOQUE_ARMA_EMPRESA -> AGESP300_AUDIT.H_TB_ESTOQUE_ARMA_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_ESTOQUE_ARMA_EMPRESA existe de fato antes de criar)
-- PWDA11874.H_TB_ESTOQUE_MUNICAO_EMPRESA -> AGESP300_AUDIT.H_TB_ESTOQUE_MUNICAO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_ESTOQUE_MUNICAO_EMPRESA existe de fato antes de criar)
-- PWDA11874.H_TB_PERFIL_PESSOA_GESP -> AGESP300_AUDIT.H_TB_PERFIL_PESSOA_GESP (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_PERFIL_PESSOA_GESP existe de fato antes de criar)
-- PWDA11874.H_TB_RESPONSAVEL_EMPRESA_PROC -> AGESP300_AUDIT.H_TB_RESPONSAVEL_EMPRESA_PROC (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_RESPONSAVEL_EMPRESA_PROC existe de fato antes de criar)
-- PWDA11874.H_TB_RESPONSAVEL_PROCESSO -> AGESP300_AUDIT.H_TB_RESPONSAVEL_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_RESPONSAVEL_PROCESSO existe de fato antes de criar)
-- PWDA11874.H_TB_TIPO_ATIVIDADE -> AGESP300_AUDIT.H_TB_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_TIPO_ATIVIDADE existe de fato antes de criar)
-- PWDA11874.H_TB_TIPO_SITUACAO_EMPRESA -> AGESP300_AUDIT.H_TB_TIPO_SITUACAO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300_AUDIT.H_TB_TIPO_SITUACAO_EMPRESA existe de fato antes de criar)
