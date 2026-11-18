/*==============================================================*/
/* DADOS: ATURMA100.TB_TIPO_DOCUMENTO_ANEXO                     */
/* Gerado em 28/09/2026 17:46:10 por oracle_data_web.py         */
/* Origem: 37 linhas | Destino: 37 linhas                       */
/* Chave: ID_TIPO_DOCUMENTO_ANEXO, NO_DOCUMENTO_ANEXO, ST_ATIVO */
/* Revise antes de aplicar. Commit fica no fim, uma unica vez.    */
/*==============================================================*/

/*--------------------------------------------------------------*/
/* Existem so no DESTINO - nenhum DELETE e gerado. Decida.       */
/*--------------------------------------------------------------*/
-- ID_TIPO_DOCUMENTO_ANEXO = 6 AND NO_DOCUMENTO_ANEXO = 'Atestado de saude fisica e mental' AND ST_ATIVO = 'S'
-- ID_TIPO_DOCUMENTO_ANEXO = 9 AND NO_DOCUMENTO_ANEXO = 'Atestado de aptidao psicologica' AND ST_ATIVO = 'S'

/*--------------------------------------------------------------*/
/* INSERT - 2 linha(s)                                          */
/*--------------------------------------------------------------*/
INSERT INTO ATURMA100.TB_TIPO_DOCUMENTO_ANEXO (ID_TIPO_DOCUMENTO_ANEXO, NO_DOCUMENTO_ANEXO, ST_ATIVO)
VALUES (6, 'Atestado de saúde física e mental', 'S');
INSERT INTO ATURMA100.TB_TIPO_DOCUMENTO_ANEXO (ID_TIPO_DOCUMENTO_ANEXO, NO_DOCUMENTO_ANEXO, ST_ATIVO)
VALUES (9, 'Atestado de aptidão psicológica', 'S');

-- Confira o resultado antes de confirmar:
-- SELECT COUNT(*) FROM ATURMA100.TB_TIPO_DOCUMENTO_ANEXO;
commit;