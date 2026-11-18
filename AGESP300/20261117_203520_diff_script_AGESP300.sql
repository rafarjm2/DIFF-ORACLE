/*==============================================================*/
/* DIFF: AGESP300 - aplicar em HOMOL_DPF06H                     */
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
WHERE owner = 'AGESP300' AND table_name IN ('TB_LOTACAO_TEMPORARIA');
-- Esperado: 0 linhas.

SELECT sequence_owner, sequence_name FROM dba_sequences
WHERE sequence_owner = 'AGESP300' AND sequence_name IN ('SQ_LOTACAO_TEMPORARIA');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Sequences                                                      */
/*==============================================================*/
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_sequences WHERE sequence_owner = 'AGESP300' AND sequence_name = 'SQ_LOTACAO_TEMPORARIA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[create sequence AGESP300.SQ_LOTACAO_TEMPORARIA
increment by 1
start with 22
nocycle
cache 20]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: SEQUENCE AGESP300.SQ_LOTACAO_TEMPORARIA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): SEQUENCE AGESP300.SQ_LOTACAO_TEMPORARIA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em SEQUENCE AGESP300.SQ_LOTACAO_TEMPORARIA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

grant SELECT on AGESP300.SQ_LOTACAO_TEMPORARIA to AGESPUSR;
create or replace synonym AGESPUSR.SQ_LOTACAO_TEMPORARIA
   for AGESP300.SQ_LOTACAO_TEMPORARIA;

/*==============================================================*/
/* Table: TB_LOTACAO_TEMPORARIA                                 */
/*==============================================================*/
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_tables WHERE owner = 'AGESP300' AND table_name = 'TB_LOTACAO_TEMPORARIA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[CREATE TABLE "AGESP300"."TB_LOTACAO_TEMPORARIA" 
   (	"ID_LOTACAO_TEMPORARIA" NUMBER(10,0) DEFAULT AGESP300.SQ_LOTACAO_TEMPORARIA.NEXTVAL NOT NULL ENABLE, 
	"CD_UUID" VARCHAR2(36) NOT NULL ENABLE, 
	"NR_CPF" VARCHAR2(11) NOT NULL ENABLE, 
	"CD_LOTACAO_ATUAL" NUMBER(10,0) NOT NULL ENABLE, 
	"CD_LOTACAO_MISSAO" NUMBER(10,0) NOT NULL ENABLE, 
	"DT_INICIO" DATE NOT NULL ENABLE, 
	"DT_FIM" DATE NOT NULL ENABLE, 
	"DH_CRIACAO_REGISTRO" DATE DEFAULT SYSDATE NOT NULL ENABLE, 
	"DH_ENCERRADO_MANUAL" DATE, 
	"IC_SITUACAO" VARCHAR2(1) DEFAULT 'A' NOT NULL ENABLE, 
	"NR_MATRICULA" NUMBER(10,0) NOT NULL ENABLE, 
	 CONSTRAINT "CC_LOTACAO_TEMP_NR_CPF" CHECK (REGEXP_LIKE(NR_CPF, '^[0-9]{11}$')) ENABLE, 
	 CONSTRAINT "CC_LOTACAO_TEMP_PERIODO" CHECK (DT_FIM >= DT_INICIO) ENABLE, 
	 CONSTRAINT "CC_LOTACAO_TEMP_IC_SITUACAO" CHECK (IC_SITUACAO IN ('A', 'E', 'C')) ENABLE, 
	 CONSTRAINT "PK_LOTACAO_TEMPORARIA" PRIMARY KEY ("ID_LOTACAO_TEMPORARIA")
  USING INDEX  ENABLE, 
	 CONSTRAINT "UK_LOTACAO_TEMPORARIA_UUID" UNIQUE ("CD_UUID")
  USING INDEX  ENABLE
   )]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: TABLE AGESP300.TB_LOTACAO_TEMPORARIA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): TABLE AGESP300.TB_LOTACAO_TEMPORARIA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em TABLE AGESP300.TB_LOTACAO_TEMPORARIA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

comment on table AGESP300.TB_LOTACAO_TEMPORARIA is
'Registra as lotacoes temporarias (missoes) de servidores em unidade administrativa diversa da lotacao de origem, por periodo determinado, sem alterar a lotacao de origem (HU052). As unidades sao obtidas da API de unidades administrativas do GESP3, por isso nao ha FK fisica para CD_LOTACAO_ATUAL e CD_LOTACAO_MISSAO.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.ID_LOTACAO_TEMPORARIA is
'Identificador artificial da lotacao temporaria. Gerado pela sequence SQ_LOTACAO_TEMPORARIA.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.CD_UUID is
'Identificador universal unico (UUID) da lotacao temporaria, gerado pela aplicacao no formato 8-4-4-4-12 (36 caracteres). Usado como referencia externa do registro.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.NR_CPF is
'Numero do CPF do servidor em missao, somente digitos (11 posicoes, com zeros a esquerda).';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.CD_LOTACAO_ATUAL is
'Codigo da unidade administrativa de lotacao de origem do servidor no momento da inclusao.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.CD_LOTACAO_MISSAO is
'Codigo da unidade administrativa da missao (lotacao temporaria), selecionada a partir da UF de missao.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.DT_INICIO is
'Data de inicio do periodo da missao.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.DT_FIM is
'Data de fim do periodo da missao. Nao pode ser anterior a DT_INICIO.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.DH_CRIACAO_REGISTRO is
'Data e hora de criacao do registro.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.DH_ENCERRADO_MANUAL is
'Data e hora do encerramento manual da missao antes de DT_FIM. Nulo quando a missao nao foi encerrada manualmente.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.IC_SITUACAO is
'Indicador da situacao da lotacao temporaria: A - Ativa; E - Encerrada; C - Cancelada.';
comment on column AGESP300.TB_LOTACAO_TEMPORARIA.NR_MATRICULA is
'Numero da matricula do servidor em missao.';

grant DELETE,INSERT,SELECT,UPDATE on AGESP300.TB_LOTACAO_TEMPORARIA to AGESPUSR;

create or replace synonym AGESPUSR.TB_LOTACAO_TEMPORARIA
   for AGESP300.TB_LOTACAO_TEMPORARIA;

/*==============================================================*/
/* PK / UK / CHECK / INDICE equivalentes com NOME DIFERENTE       */
/* Nada foi criado (duplicaria o objeto). Renomeacao COMENTADA -  */
/* descomente so se o nome da origem tambem for o desejado.       */
/*==============================================================*/
-- PK AGESP300.TB_VINCULO_EMPSA_MQNA_RECARGA (ID_MAQUINA_RECARGA, ID_PESSOA_GESP, DT_INICIO_VINCULO): destino=PK_VINCULO_EMPSA_MQNA_RECARGA | origem=PK_VNCLA_EMPSA_MAQUINA_RECA
-- ALTER TABLE AGESP300.TB_VINCULO_EMPSA_MQNA_RECARGA RENAME CONSTRAINT PK_VINCULO_EMPSA_MQNA_RECARGA TO PK_VNCLA_EMPSA_MAQUINA_RECA;
-- conferir o indice de suporte apos o rename: SELECT index_name FROM dba_constraints WHERE owner = 'AGESP300' AND constraint_name = 'PK_VNCLA_EMPSA_MAQUINA_RECA';

PROMPT DIAGNOSTICO - indices a criar
SELECT owner, index_name FROM dba_indexes
WHERE owner = 'AGESP300' AND index_name IN ('IX_LOTACAO_TEMP_NR_CPF','PK_TB_MARCA_MAQUINA_RECARGA');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Indices faltantes                                              */
/*==============================================================*/
-- AGESP300.IX_LOTACAO_TEMP_NR_CPF em AGESP300.TB_LOTACAO_TEMPORARIA (NR_CPF, DT_INICIO)
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_indexes WHERE owner = 'AGESP300' AND index_name = 'IX_LOTACAO_TEMP_NR_CPF';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[CREATE INDEX "AGESP300"."IX_LOTACAO_TEMP_NR_CPF" ON "AGESP300"."TB_LOTACAO_TEMPORARIA" ("NR_CPF", "DT_INICIO")]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: INDEX AGESP300.IX_LOTACAO_TEMP_NR_CPF');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): INDEX AGESP300.IX_LOTACAO_TEMP_NR_CPF');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em INDEX AGESP300.IX_LOTACAO_TEMP_NR_CPF: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

-- AGESP300.PK_TB_MARCA_MAQUINA_RECARGA em AGESP300.TB_MARCA_MAQUINA_RECARGA (ID_MARCA_MAQUINA_RECARGA)
DECLARE
  v_qtd NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_qtd FROM dba_indexes WHERE owner = 'AGESP300' AND index_name = 'PK_TB_MARCA_MAQUINA_RECARGA';
  IF v_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[CREATE UNIQUE INDEX "AGESP300"."PK_TB_MARCA_MAQUINA_RECARGA" ON "AGESP300"."TB_MARCA_MAQUINA_RECARGA" ("ID_MARCA_MAQUINA_RECARGA")]';
    DBMS_OUTPUT.PUT_LINE('APLICADO: INDEX AGESP300.PK_TB_MARCA_MAQUINA_RECARGA');
  ELSE
    DBMS_OUTPUT.PUT_LINE('NADA A FAZER (ja esta assim): INDEX AGESP300.PK_TB_MARCA_MAQUINA_RECARGA');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ERRO em INDEX AGESP300.PK_TB_MARCA_MAQUINA_RECARGA: ' || SQLCODE || ' - ' || SQLERRM);
    RAISE;
END;
/

/*==============================================================*/
/* Sinonimos que existem nos dois lados mas apontam para alvos    */
/* diferentes - COMENTADO: repontar muda o comportamento.         */
/*==============================================================*/
-- PMRA5012148.SQ_ANEXO: destino=APROBAN100.SQ_ANEXO | origem=AGESP300.SQ_ANEXO
-- create or replace synonym PMRA5012148.SQ_ANEXO
--    for AGESP300.SQ_ANEXO;

-- PMRA5012148.SQ_CONTATO: destino=APROBAN100.SQ_CONTATO | origem=AGESP300.SQ_CONTATO
-- create or replace synonym PMRA5012148.SQ_CONTATO
--    for AGESP300.SQ_CONTATO;

-- PMRA5012148.SQ_ENDERECO: destino=APROBAN100.SQ_ENDERECO | origem=AGESP300.SQ_ENDERECO
-- create or replace synonym PMRA5012148.SQ_ENDERECO
--    for AGESP300.SQ_ENDERECO;

-- PMRA5012148.SQ_GRU: destino=APROBAN100.SQ_GRU | origem=AGESP300.SQ_GRU
-- create or replace synonym PMRA5012148.SQ_GRU
--    for AGESP300.SQ_GRU;

-- PMRA5012148.SQ_RELATORIO_VISTORIA: destino=APROBAN100.SQ_RELATORIO_VISTORIA | origem=AGESP300.SQ_RELATORIO_VISTORIA
-- create or replace synonym PMRA5012148.SQ_RELATORIO_VISTORIA
--    for AGESP300.SQ_RELATORIO_VISTORIA;

-- PMRA5012148.TB_SITUACAO_PROCESSO: destino=APROBAN100.TB_SITUACAO_PROCESSO | origem=AGESP300.TB_SITUACAO_PROCESSO
-- create or replace synonym PMRA5012148.TB_SITUACAO_PROCESSO
--    for AGESP300.TB_SITUACAO_PROCESSO;

-- PWDA11874.SQ_ANEXO: destino=ATURMA100.SQ_ANEXO | origem=AGESP300.SQ_ANEXO
-- create or replace synonym PWDA11874.SQ_ANEXO
--    for AGESP300.SQ_ANEXO;

-- PWDA11874.SQ_CONTATO: destino=ATURMA100.SQ_CONTATO | origem=AGESP300.SQ_CONTATO
-- create or replace synonym PWDA11874.SQ_CONTATO
--    for AGESP300.SQ_CONTATO;

-- PWDA11874.SQ_ENDERECO: destino=ATURMA100.SQ_ENDERECO | origem=AGESP300.SQ_ENDERECO
-- create or replace synonym PWDA11874.SQ_ENDERECO
--    for AGESP300.SQ_ENDERECO;

-- PWDA11874.SQ_GRU: destino=ATURMA100.SQ_GRU | origem=AGESP300.SQ_GRU
-- create or replace synonym PWDA11874.SQ_GRU
--    for AGESP300.SQ_GRU;

-- PWDA11874.TB_ANEXO: destino=ATURMA100.TB_ANEXO | origem=AGESP300.TB_ANEXO
-- create or replace synonym PWDA11874.TB_ANEXO
--    for AGESP300.TB_ANEXO;

-- PWDA11874.TB_CONTATO: destino=ATURMA100.TB_CONTATO | origem=AGESP300.TB_CONTATO
-- create or replace synonym PWDA11874.TB_CONTATO
--    for AGESP300.TB_CONTATO;

-- PWDA11874.TB_ETAPA: destino=ATURMA100.TB_ETAPA | origem=AGESP300.TB_ETAPA
-- create or replace synonym PWDA11874.TB_ETAPA
--    for AGESP300.TB_ETAPA;

-- PWDA11874.TB_GRU: destino=ATURMA100.TB_GRU | origem=AGESP300.TB_GRU
-- create or replace synonym PWDA11874.TB_GRU
--    for AGESP300.TB_GRU;

-- PWDA11874.TB_PENDENCIA: destino=ATURMA100.TB_PENDENCIA | origem=AGESP300.TB_PENDENCIA
-- create or replace synonym PWDA11874.TB_PENDENCIA
--    for AGESP300.TB_PENDENCIA;

-- PWDA11874.TB_PESSOA_FISICA: destino=ATURMA100.TB_PESSOA_FISICA | origem=AGESP300.TB_PESSOA_FISICA
-- create or replace synonym PWDA11874.TB_PESSOA_FISICA
--    for AGESP300.TB_PESSOA_FISICA;

-- PWDA11874.TB_TIPO_DOCUMENTO_ANEXO: destino=ATURMA100.TB_TIPO_DOCUMENTO_ANEXO | origem=AGESP300.TB_TIPO_DOCUMENTO_ANEXO
-- create or replace synonym PWDA11874.TB_TIPO_DOCUMENTO_ANEXO
--    for AGESP300.TB_TIPO_DOCUMENTO_ANEXO;

/*==============================================================*/
/* Sinonimos faltantes NAO tratados automaticamente - revisar     */
/* (dono diferente do configurado, ou aponta para objeto que      */
/* precisa ser confirmado antes de criar)                         */
/*==============================================================*/
-- AGESPUSR.SQ_CONTATO_EMPRESA -> AGESP300.SQ_CONTATO_EMPRESA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.SQ_CONTATO_EMPRESA existe de fato antes de criar)
-- AGESPUSR.TB_CONTATO_PESSOA -> AGESP300.TB_CONTATO_PESSOA (existe em prehomol_gesp, ausente em homol_DPF06H - confirme se AGESP300.TB_CONTATO_PESSOA existe de fato antes de criar)
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
