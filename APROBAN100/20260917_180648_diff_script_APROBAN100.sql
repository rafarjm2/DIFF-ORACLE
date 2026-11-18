/*==============================================================*/
/* DIFF: APROBAN100 - aplicar em HOMOL_DPF06H                   */
/* Origem: prehomol_gesp (conexao direta via DBMS_METADATA)     */
/* Gerado automaticamente por oracle_diff.py - revise antes de     */
/* aplicar, principalmente nomes de constraint auto-gerados e      */
/* grants que dependam de usuario que so existe num dos ambientes. */
/*==============================================================*/

PROMPT ==========================================================
PROMPT DIAGNOSTICO - confirmar ausencia antes de criar
PROMPT ==========================================================
SELECT owner, table_name, status FROM dba_tables
WHERE owner = 'APROBAN100' AND table_name IN ('TB_MOVIMENTACAO_PROCESSO');
-- Esperado: 0 linhas.

SELECT sequence_owner, sequence_name FROM dba_sequences
WHERE sequence_owner = 'APROBAN100' AND sequence_name IN ('SQ_MOVIMENTACAO_PROCESSO');
-- Esperado: 0 linhas.

/*==============================================================*/
/* Sequences                                                      */
/*==============================================================*/
create sequence APROBAN100.SQ_MOVIMENTACAO_PROCESSO
increment by 1
start with 8
nocycle
nocache;

grant SELECT on APROBAN100.SQ_MOVIMENTACAO_PROCESSO to APROBANUSR;
create or replace synonym APROBANUSR.SQ_MOVIMENTACAO_PROCESSO
   for APROBAN100.SQ_MOVIMENTACAO_PROCESSO;

/*==============================================================*/
/* Table: TB_MOVIMENTACAO_PROCESSO                              */
/*==============================================================*/
CREATE TABLE "APROBAN100"."TB_MOVIMENTACAO_PROCESSO" 
   (	"ID_MOVIMENTACAO_PROCESSO" NUMBER(19,0) NOT NULL ENABLE, 
	"ID_PROCESSO_BANCARIO" NUMBER(19,0) NOT NULL ENABLE, 
	"IC_TIPO_MOVIMENTACAO" VARCHAR2(3) NOT NULL ENABLE, 
	"ID_SITUACAO_ORIGEM" NUMBER(19,0), 
	"ID_SITUACAO_DESTINO" NUMBER(19,0), 
	"NR_CPF_USUARIO_OPERACAO" NUMBER(11,0) NOT NULL ENABLE, 
	"NR_CPF_RESPONSAVEL_ANTERIOR" NUMBER(11,0), 
	"NR_CPF_RESPONSAVEL_NOVO" NUMBER(11,0), 
	"ID_DOCUMENTO_PROCESSO" NUMBER(19,0), 
	"DS_JUSTIFICATIVA" VARCHAR2(500), 
	"DS_OBSERVACAO" VARCHAR2(1000), 
	"DH_MOVIMENTACAO" TIMESTAMP (6) NOT NULL ENABLE, 
	 CONSTRAINT "PK_MOVIMENTACAO_PROCESSO" PRIMARY KEY ("ID_MOVIMENTACAO_PROCESSO")
  USING INDEX  ENABLE, 
	 CONSTRAINT "FK_MOVPROC_PROCESSO_BANCARIO" FOREIGN KEY ("ID_PROCESSO_BANCARIO")
	  REFERENCES "APROBAN100"."TB_PROCESSO_BANCARIO" ("ID_PROCESSO_BANCARIO") ENABLE, 
	 CONSTRAINT "FK_MOVPROC_SITUACAO_ORIGEM" FOREIGN KEY ("ID_SITUACAO_ORIGEM")
	  REFERENCES "APROBAN100"."TB_SITUACAO_PROCESSO" ("ID_SITUACAO_PROCESSO") ENABLE, 
	 CONSTRAINT "FK_MOVPROC_SITUACAO_DESTINO" FOREIGN KEY ("ID_SITUACAO_DESTINO")
	  REFERENCES "APROBAN100"."TB_SITUACAO_PROCESSO" ("ID_SITUACAO_PROCESSO") ENABLE
   ) ;

comment on table APROBAN100.TB_MOVIMENTACAO_PROCESSO is
'Trilha de movimentacoes de negocio do processo bancario. Cada linha representa uma operacao ocorrida no fluxo (distribuicao, parecer, notificacao, aprovacao) e e imutavel: nunca sofre UPDATE nem DELETE. Complementa a auditoria tecnica do Envers (H_TB_PROCESSO_BANCARIO), que registra alteracoes de campo sem semantica de negocio.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.ID_MOVIMENTACAO_PROCESSO is
'Identificador unico da movimentacao. Gerado pela sequencia SQ_MOVIMENTACAO_PROCESSO.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.ID_PROCESSO_BANCARIO is
'Processo bancario ao qual a movimentacao pertence. Referencia TB_PROCESSO_BANCARIO.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.IC_TIPO_MOVIMENTACAO is
'Codigo do tipo da operacao registrada, conforme TipoMovimentacaoProcessoEnum: DIS=Distribuicao, RED=Redistribuicao, AVI=Avaliacao de Item, RVF=Relatorio de Vistoria Finalizado, PDE=Parecer de Deferimento Encaminhado, PIE=Parecer de Indeferimento Encaminhado, NOT=Notificacao Encaminhada, ADL=Parecer Aprovado DELESP, RDL=Parecer Reprovado DELESP, ADX=Parecer Aprovado DREX, RDX=Parecer Reprovado DREX.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.ID_SITUACAO_ORIGEM is
'Situacao do processo imediatamente antes da operacao. Nulo quando a operacao nao altera nem depende de situacao.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.ID_SITUACAO_DESTINO is
'Situacao do processo resultante da operacao. Igual a situacao de origem quando a operacao nao promove transicao, como na redistribuicao.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.NR_CPF_USUARIO_OPERACAO is
'CPF, apenas digitos, do usuario logado que executou a operacao. Obtido do contexto de seguranca no momento do registro.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.NR_CPF_RESPONSAVEL_ANTERIOR is
'CPF do analista responsavel pelo processo antes da operacao. Preenchido em distribuicao e redistribuicao; nulo na primeira distribuicao e nos demais tipos de movimentacao.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.NR_CPF_RESPONSAVEL_NOVO is
'CPF do analista responsavel pelo processo apos a operacao. Preenchido em distribuicao e redistribuicao; nulo nos demais tipos de movimentacao.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.ID_DOCUMENTO_PROCESSO is
'Documento gerado ou avaliado pela operacao, como parecer ou notificacao. Referencia logicamente TB_DOCUMENTO_PROCESSO_BANCARIO, sem chave estrangeira fisica. Nulo nas operacoes que nao produzem documento.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.DS_JUSTIFICATIVA is
'Justificativa informada pelo usuario na operacao, quando exigida pela regra de negocio, como na reprovacao de parecer pela DELESP ou pela DREX. Preserva o texto do momento do registro, mesmo que o campo de origem no processo seja posteriormente sobrescrito.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.DS_OBSERVACAO is
'Informacao complementar da operacao, de uso livre por tipo de movimentacao. Nulo quando nao aplicavel.';
comment on column APROBAN100.TB_MOVIMENTACAO_PROCESSO.DH_MOVIMENTACAO is
'Data e hora em que a operacao foi registrada. Base da ordenacao cronologica da trilha.';

grant DELETE,INSERT,SELECT,UPDATE on APROBAN100.TB_MOVIMENTACAO_PROCESSO to APROBANUSR;

create or replace synonym APROBANUSR.TB_MOVIMENTACAO_PROCESSO
   for APROBAN100.TB_MOVIMENTACAO_PROCESSO;

/*==============================================================*/
/* Ajustes de coluna (NOT NULL / tipo) - REVISAR antes de aplicar */
/* Direcao assumida: destino se alinha a origem.                  */
/*==============================================================*/
-- APROBAN100.TB_DOCUMENTO_PROCESSO_BNCRO.NR_CPF_ANALISTA_RESPONSAVEL: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE APROBAN100.TB_DOCUMENTO_PROCESSO_BNCRO MODIFY (NR_CPF_ANALISTA_RESPONSAVEL NULL);

-- APROBAN100.TB_PLANO_SEGURANCA.IC_POSSUI_COFRE_DISP_TEMPORIZA: nullable diverge (homol_DPF06H=Y vs prehomol_gesp=N)
-- ATENCAO: checar dados com NULL antes de aplicar NOT NULL:
-- SELECT COUNT(*) FROM APROBAN100.TB_PLANO_SEGURANCA WHERE IC_POSSUI_COFRE_DISP_TEMPORIZA IS NULL;
ALTER TABLE APROBAN100.TB_PLANO_SEGURANCA MODIFY (IC_POSSUI_COFRE_DISP_TEMPORIZA NOT NULL);

-- APROBAN100.TB_PLANO_SEGURANCA.IC_POSSUI_COFRE_FECHA_REMOTO: nullable diverge (homol_DPF06H=Y vs prehomol_gesp=N)
-- ATENCAO: checar dados com NULL antes de aplicar NOT NULL:
-- SELECT COUNT(*) FROM APROBAN100.TB_PLANO_SEGURANCA WHERE IC_POSSUI_COFRE_FECHA_REMOTO IS NULL;
ALTER TABLE APROBAN100.TB_PLANO_SEGURANCA MODIFY (IC_POSSUI_COFRE_FECHA_REMOTO NOT NULL);

-- APROBAN100.TB_PLANO_SEGURANCA.IC_POSSUI_PRIVACIDADE_GUICHE: nullable diverge (homol_DPF06H=Y vs prehomol_gesp=N)
-- ATENCAO: checar dados com NULL antes de aplicar NOT NULL:
-- SELECT COUNT(*) FROM APROBAN100.TB_PLANO_SEGURANCA WHERE IC_POSSUI_PRIVACIDADE_GUICHE IS NULL;
ALTER TABLE APROBAN100.TB_PLANO_SEGURANCA MODIFY (IC_POSSUI_PRIVACIDADE_GUICHE NOT NULL);

-- APROBAN100.TB_PLANO_SEGURANCA.IC_PRIVACIDADE_DIVISORIA: nullable diverge (homol_DPF06H=Y vs prehomol_gesp=N)
-- ATENCAO: checar dados com NULL antes de aplicar NOT NULL:
-- SELECT COUNT(*) FROM APROBAN100.TB_PLANO_SEGURANCA WHERE IC_PRIVACIDADE_DIVISORIA IS NULL;
ALTER TABLE APROBAN100.TB_PLANO_SEGURANCA MODIFY (IC_PRIVACIDADE_DIVISORIA NOT NULL);

-- APROBAN100.TB_PLANO_SEGURANCA.IC_PRIVACIDADE_OUTRAS: nullable diverge (homol_DPF06H=Y vs prehomol_gesp=N)
-- ATENCAO: checar dados com NULL antes de aplicar NOT NULL:
-- SELECT COUNT(*) FROM APROBAN100.TB_PLANO_SEGURANCA WHERE IC_PRIVACIDADE_OUTRAS IS NULL;
ALTER TABLE APROBAN100.TB_PLANO_SEGURANCA MODIFY (IC_PRIVACIDADE_OUTRAS NOT NULL);

-- APROBAN100.TB_VIGILANCIA.TP_LOCAL_GUARDA: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE APROBAN100.TB_VIGILANCIA MODIFY (TP_LOCAL_GUARDA NULL);

-- APROBAN100.TB_VIGILANCIA.TP_RECIPIENTE_GUARDA: nullable diverge (homol_DPF06H=N vs prehomol_gesp=Y)
ALTER TABLE APROBAN100.TB_VIGILANCIA MODIFY (TP_RECIPIENTE_GUARDA NULL);
