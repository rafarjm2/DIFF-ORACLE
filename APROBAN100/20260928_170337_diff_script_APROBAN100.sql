/*==============================================================*/
/* DIFF: APROBAN100 - aplicar em HOMOL_DPF06H                   */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

/*==============================================================*/
/* Colunas faltantes em tabela existente                          */
/*==============================================================*/
ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (IC_ORIGEM_RELATORIO NUMBER(1) DEFAULT 3 NOT NULL);
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.IC_ORIGEM_RELATORIO is
'Origem do Relatorio de Vistoria: 1 = gerado automaticamente pelo GESP3 (1o Ano de Vigencia - Renovacao ou Primeiro Plano); 2 = gerado automaticamente pelo GESP3 (2o Ano de Vigencia - Renovacao ou Primeiro Plano); 3 = relatorio criado pelo analista ou anexado externamente (default)';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (IC_AVALIACAO VARCHAR2(1));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.IC_AVALIACAO is
'Avaliacao do Relatorio de Vistoria finalizado: S=Aprovado, N=Reprovado';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (DS_JUSTIFICATIVA_AVALIACAO VARCHAR2(4000));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.DS_JUSTIFICATIVA_AVALIACAO is
'Justificativa obrigatoria quando IC_AVALIACAO = N (Reprovado)';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (NR_CPF_USUARIO_AVALIACAO VARCHAR2(11));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.NR_CPF_USUARIO_AVALIACAO is
'CPF do analista que registrou a avaliacao do relatorio';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (DH_AVALIACAO TIMESTAMP(6));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.DH_AVALIACAO is
'Data/hora do registro da avaliacao do relatorio';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (NO_USUARIO_FINALIZACAO VARCHAR2(200));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.NO_USUARIO_FINALIZACAO is
'Nome do analista que finalizou o Relatorio de Vistoria, registrado no momento da finalizacao';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (NR_MATRICULA_USUARIO_FINALIZACAO VARCHAR2(20));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.NR_MATRICULA_USUARIO_FINALIZACAO is
'Matricula do analista que finalizou o Relatorio de Vistoria, registrada no momento da finalizacao';

ALTER TABLE APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO ADD (SG_UNIDADE_USUARIO_FINALIZACAO VARCHAR2(100));
comment on column APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.SG_UNIDADE_USUARIO_FINALIZACAO is
'Sigla da unidade (lotacao ou exercicio) do analista que finalizou o Relatorio de Vistoria, registrada no momento da finalizacao';

/*==============================================================*/
/* Ajustes de coluna (DEFAULT / NOT NULL / tipo) - REVISAR       */
/* Direcao assumida: destino se alinha a origem.                  */
/*==============================================================*/
-- APROBAN100.TB_ALARME.DS_TP_ACIONA_ALARME_REDUNDANTE: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE APROBAN100.TB_ALARME MODIFY (DS_TP_ACIONA_ALARME_REDUNDANTE NULL);

/*==============================================================*/
/* Constraints faltantes (PK / UK / CHECK)                        */
/*==============================================================*/
-- APROBAN100.TB_CAIXA_ELETRONICO.CK_IC_SUBSTANCIA_PIROTECNIA
ALTER TABLE "APROBAN100"."TB_CAIXA_ELETRONICO" ADD CONSTRAINT "CK_IC_SUBSTANCIA_PIROTECNIA" CHECK (IC_SUBSTANCIA_PIROTECNIA IS NULL OR (IC_SUBSTANCIA_PIROTECNIA IN ('S','N'))) ENABLE;

-- APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.CC_RVP_IC_AVALIACAO
ALTER TABLE "APROBAN100"."TB_RELATORIO_VISTORIA_PROCESSO" ADD CONSTRAINT "CC_RVP_IC_AVALIACAO" CHECK (IC_AVALIACAO IN ('S','N')) ENABLE;

-- APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.CC_RVP_IC_ORIGEM_RELATORIO
ALTER TABLE "APROBAN100"."TB_RELATORIO_VISTORIA_PROCESSO" ADD CONSTRAINT "CC_RVP_IC_ORIGEM_RELATORIO" CHECK (IC_ORIGEM_RELATORIO IN (1,2,3)) ENABLE;

-- APROBAN100.TB_RELATORIO_VISTORIA_PROCESSO.CC_RVP_JSTVA_QDO_REPROVADO
ALTER TABLE "APROBAN100"."TB_RELATORIO_VISTORIA_PROCESSO" ADD CONSTRAINT "CC_RVP_JSTVA_QDO_REPROVADO" CHECK (IC_AVALIACAO != 'N' OR DS_JUSTIFICATIVA_AVALIACAO IS NOT NULL) ENABLE;

/*==============================================================*/
/* Ordem fisica das colunas diverge - NAO ha ALTER que reordene.  */
/* Impacto: INSERT sem lista de colunas e SELECT *. Corrigir      */
/* exige recriar a tabela (CTAS + rename) em janela controlada.   */
/*==============================================================*/
-- APROBAN100.TB_CAIXA_ELETRONICO: conferir ordem no relatorio de diferencas
