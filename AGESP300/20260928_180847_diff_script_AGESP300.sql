/*==============================================================*/
/* DIFF: AGESP300 - aplicar em HOMOL_DPF06H                     */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

/*==============================================================*/
/* Indices faltantes                                              */
/*==============================================================*/
-- AGESP300.PK_TB_MARCA_MAQUINA_RECARGA em AGESP300.TB_MARCA_MAQUINA_RECARGA (ID_MARCA_MAQUINA_RECARGA)
CREATE UNIQUE INDEX "AGESP300"."PK_TB_MARCA_MAQUINA_RECARGA" ON "AGESP300"."TB_MARCA_MAQUINA_RECARGA" ("ID_MARCA_MAQUINA_RECARGA") 
  ;

-- AGESP300.SYS_IL0003011537C00003$$ em AGESP300.TB_DOC_NOTIFICACAO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003011537C00003$$" ON "AGESP300"."TB_DOC_NOTIFICACAO" (
  ;

-- AGESP300.SYS_IL0003011542C00004$$ em AGESP300.TB_DOC_TERMO_DECLARACAO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003011542C00004$$" ON "AGESP300"."TB_DOC_TERMO_DECLARACAO" (
  ;

-- AGESP300.SYS_IL0003011566C00005$$ em AGESP300.TB_ETAPA_PROCESSO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003011566C00005$$" ON "AGESP300"."TB_ETAPA_PROCESSO" (
  ;

-- AGESP300.SYS_IL0003011589C00003$$ em AGESP300.TB_PARECER_PROC_AUTORIZATIVO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003011589C00003$$" ON "AGESP300"."TB_PARECER_PROC_AUTORIZATIVO" (
  ;

-- AGESP300.SYS_IL0003226115C00010$$ em AGESP300.TB_ACEITE_TERMO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003226115C00010$$" ON "AGESP300"."TB_ACEITE_TERMO" (
  ;

-- AGESP300.SYS_IL0003226723C00007$$ em AGESP300.TB_AUTO_INFRACAO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003226723C00007$$" ON "AGESP300"."TB_AUTO_INFRACAO" (
  ;

-- AGESP300.SYS_IL0003226723C00017$$ em AGESP300.TB_AUTO_INFRACAO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003226723C00017$$" ON "AGESP300"."TB_AUTO_INFRACAO" (
  ;

-- AGESP300.SYS_IL0003226748C00005$$ em AGESP300.TB_AUTO_INFRACAO_HISTORICO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003226748C00005$$" ON "AGESP300"."TB_AUTO_INFRACAO_HISTORICO" (
  ;

-- AGESP300.SYS_IL0003229920C00003$$ em AGESP300.TB_DEFESA_ADMINISTRATIVA ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003229920C00003$$" ON "AGESP300"."TB_DEFESA_ADMINISTRATIVA" (
  ;

-- AGESP300.SYS_IL0003230241C00004$$ em AGESP300.TB_AUTO_INFRACAO_EMAIL ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003230241C00004$$" ON "AGESP300"."TB_AUTO_INFRACAO_EMAIL" (
  ;

-- AGESP300.SYS_IL0003239336C00004$$ em AGESP300.TB_PARECER_ANALISE ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003239336C00004$$" ON "AGESP300"."TB_PARECER_ANALISE" (
  ;

-- AGESP300.SYS_IL0003239336C00014$$ em AGESP300.TB_PARECER_ANALISE ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003239336C00014$$" ON "AGESP300"."TB_PARECER_ANALISE" (
  ;

-- AGESP300.SYS_IL0003239346C00004$$ em AGESP300.TB_ANOTACAO_AUTO_INFRACAO ()
CREATE UNIQUE INDEX "AGESP300"."SYS_IL0003239346C00004$$" ON "AGESP300"."TB_ANOTACAO_AUTO_INFRACAO" (
  ;

/*==============================================================*/
/* Constraints faltantes (PK / UK / CHECK)                        */
/*==============================================================*/
-- AGESP300.TB_VINCULO_EMPSA_MQNA_RECARGA.PK_VNCLA_EMPSA_MAQUINA_RECA
ALTER TABLE "AGESP300"."TB_VINCULO_EMPSA_MQNA_RECARGA" ADD CONSTRAINT "PK_VNCLA_EMPSA_MAQUINA_RECA" PRIMARY KEY ("ID_MAQUINA_RECARGA", "ID_PESSOA_GESP", "DT_INICIO_VINCULO")
  USING INDEX  ENABLE;

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do usuario de servico configurado, ou aponta   */
/* para objeto que precisa ser confirmado antes de criar)         */
/*==============================================================*/
-- PMRA5012148.SQ_ARTIGO -> AGESP300.SQ_ARTIGO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_ARTIGO existe de fato antes de criar)
-- PMRA5012148.SQ_CONTATO_EMPRESA -> AGESP300.SQ_CONTATO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_CONTATO_EMPRESA existe de fato antes de criar)
-- PMRA5012148.SQ_PROCESSO_AUTORIZATIVO -> AGESP300.SQ_PROCESSO_AUTORIZATIVO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_PROCESSO_AUTORIZATIVO existe de fato antes de criar)
-- PMRA5012148.SQ_PROCESSO_PUNITIVO -> AGESP300.SQ_PROCESSO_PUNITIVO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_PROCESSO_PUNITIVO existe de fato antes de criar)
-- PMRA5012148.TB_ARTIGO -> AGESP300.TB_ARTIGO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_ARTIGO existe de fato antes de criar)
-- PMRA5012148.TB_COLETE -> AGESP300.TB_COLETE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_COLETE existe de fato antes de criar)
-- PMRA5012148.TB_DOC_TERMO_DECLARACAO -> AGESP300.TB_DOC_TERMO_DECLARACAO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_DOC_TERMO_DECLARACAO existe de fato antes de criar)
-- PMRA5012148.TB_EMPRESA_TIPO_ATIVIDADE -> AGESP300.TB_EMPRESA_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_EMPRESA_TIPO_ATIVIDADE existe de fato antes de criar)
-- PMRA5012148.TB_FUNCIONALIDADE -> AGESP300.TB_FUNCIONALIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_FUNCIONALIDADE existe de fato antes de criar)
-- PMRA5012148.TB_PROCESSO -> AGESP300.TB_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_PROCESSO existe de fato antes de criar)
-- PMRA5012148.TB_PROCESSO_AUTORIZATIVO -> AGESP300.TB_PROCESSO_AUTORIZATIVO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_PROCESSO_AUTORIZATIVO existe de fato antes de criar)
-- PMRA5012148.TB_SOCIO_PESSOA_JURIDICA -> AGESP300.TB_SOCIO_PESSOA_JURIDICA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_SOCIO_PESSOA_JURIDICA existe de fato antes de criar)
-- PMRA5012148.TB_TIPO_ATIVIDADE -> AGESP300.TB_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_TIPO_ATIVIDADE existe de fato antes de criar)
-- PMRA5012148.TB_TIPO_PROCESSO -> AGESP300.TB_TIPO_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_TIPO_PROCESSO existe de fato antes de criar)
-- PMRA5012148.TB_VEICULO -> AGESP300.TB_VEICULO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_VEICULO existe de fato antes de criar)
-- PWDA11874.SQ_ANEXO_EMPRESA_PROCESSO -> AGESP300.SQ_ANEXO_EMPRESA_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_ANEXO_EMPRESA_PROCESSO existe de fato antes de criar)
-- PWDA11874.SQ_ANEXO_PROCURADOR -> AGESP300.SQ_ANEXO_PROCURADOR (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_ANEXO_PROCURADOR existe de fato antes de criar)
-- PWDA11874.SQ_CONTATO_EMPRESA -> AGESP300.SQ_CONTATO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_CONTATO_EMPRESA existe de fato antes de criar)
-- PWDA11874.SQ_ESTOQUE_ARMA_EMPRESA -> AGESP300.SQ_ESTOQUE_ARMA_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_ESTOQUE_ARMA_EMPRESA existe de fato antes de criar)
-- PWDA11874.SQ_ESTOQUE_MUNICAO_EMPRESA -> AGESP300.SQ_ESTOQUE_MUNICAO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_ESTOQUE_MUNICAO_EMPRESA existe de fato antes de criar)
-- PWDA11874.SQ_PERFIL_PESSOA_GESP -> AGESP300.SQ_PERFIL_PESSOA_GESP (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_PERFIL_PESSOA_GESP existe de fato antes de criar)
-- PWDA11874.SQ_PROCESSO_AUTORIZATIVO -> AGESP300.SQ_PROCESSO_AUTORIZATIVO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_PROCESSO_AUTORIZATIVO existe de fato antes de criar)
-- PWDA11874.SQ_RECEITA_SIAR -> AGESP300.SQ_RECEITA_SIAR (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_RECEITA_SIAR existe de fato antes de criar)
-- PWDA11874.SQ_RESPONSAVEL_EMPRESA_PROC -> AGESP300.SQ_RESPONSAVEL_EMPRESA_PROC (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_RESPONSAVEL_EMPRESA_PROC existe de fato antes de criar)
-- PWDA11874.SQ_RESPONSAVEL_PROCESSO -> AGESP300.SQ_RESPONSAVEL_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_RESPONSAVEL_PROCESSO existe de fato antes de criar)
-- PWDA11874.TB_ANEXO_EMPRESA_PROCESSO -> AGESP300.TB_ANEXO_EMPRESA_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_ANEXO_EMPRESA_PROCESSO existe de fato antes de criar)
-- PWDA11874.TB_ANEXO_PROCURADOR -> AGESP300.TB_ANEXO_PROCURADOR (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_ANEXO_PROCURADOR existe de fato antes de criar)
-- PWDA11874.TB_CALIBRE_TIPO_ATIVIDADE -> AGESP300.TB_CALIBRE_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_CALIBRE_TIPO_ATIVIDADE existe de fato antes de criar)
-- PWDA11874.TB_COLETE -> AGESP300.TB_COLETE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_COLETE existe de fato antes de criar)
-- PWDA11874.TB_CONTROLE_MIGRACAO -> AGESP300.TB_CONTROLE_MIGRACAO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_CONTROLE_MIGRACAO existe de fato antes de criar)
-- PWDA11874.TB_DOC_TERMO_DECLARACAO -> AGESP300.TB_DOC_TERMO_DECLARACAO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_DOC_TERMO_DECLARACAO existe de fato antes de criar)
-- PWDA11874.TB_EMPRESA_TIPO_ATIVIDADE -> AGESP300.TB_EMPRESA_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_EMPRESA_TIPO_ATIVIDADE existe de fato antes de criar)
-- PWDA11874.TB_ESPECIE_ARMA_TIPO_ATIVIDADE -> AGESP300.TB_ESPECIE_ARMA_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_ESPECIE_ARMA_TIPO_ATIVIDADE existe de fato antes de criar)
-- PWDA11874.TB_ESTOQUE_ARMA_EMPRESA -> AGESP300.TB_ESTOQUE_ARMA_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_ESTOQUE_ARMA_EMPRESA existe de fato antes de criar)
-- PWDA11874.TB_ESTOQUE_MUNICAO_EMPRESA -> AGESP300.TB_ESTOQUE_MUNICAO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_ESTOQUE_MUNICAO_EMPRESA existe de fato antes de criar)
-- PWDA11874.TB_PERFIL_PESSOA_GESP -> AGESP300.TB_PERFIL_PESSOA_GESP (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_PERFIL_PESSOA_GESP existe de fato antes de criar)
-- PWDA11874.TB_PROCESSO -> AGESP300.TB_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_PROCESSO existe de fato antes de criar)
-- PWDA11874.TB_PROCESSO_AUTORIZATIVO -> AGESP300.TB_PROCESSO_AUTORIZATIVO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_PROCESSO_AUTORIZATIVO existe de fato antes de criar)
-- PWDA11874.TB_RESPONSAVEL_EMPRESA_PROC -> AGESP300.TB_RESPONSAVEL_EMPRESA_PROC (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_RESPONSAVEL_EMPRESA_PROC existe de fato antes de criar)
-- PWDA11874.TB_RESPONSAVEL_PROCESSO -> AGESP300.TB_RESPONSAVEL_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_RESPONSAVEL_PROCESSO existe de fato antes de criar)
-- PWDA11874.TB_SOCIO_PESSOA_JURIDICA -> AGESP300.TB_SOCIO_PESSOA_JURIDICA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_SOCIO_PESSOA_JURIDICA existe de fato antes de criar)
-- PWDA11874.TB_TIPO_ATIVIDADE -> AGESP300.TB_TIPO_ATIVIDADE (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_TIPO_ATIVIDADE existe de fato antes de criar)
-- PWDA11874.TB_TIPO_PROCESSO -> AGESP300.TB_TIPO_PROCESSO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_TIPO_PROCESSO existe de fato antes de criar)
-- PWDA11874.TB_VEICULO -> AGESP300.TB_VEICULO (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_VEICULO existe de fato antes de criar)
