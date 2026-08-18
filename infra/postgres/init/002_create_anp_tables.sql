CREATE TABLE IF NOT EXISTS anp.combustiveis_precos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    regiao_sigla TEXT,
    estado_sigla TEXT,
    municipio TEXT,
    revenda TEXT,
    cnpj_revenda TEXT,
    nome_rua TEXT,
    numero_rua TEXT,
    complemento TEXT,
    bairro TEXT,
    cep TEXT,
    produto TEXT,
    data_coleta DATE NOT NULL,
    valor_venda NUMERIC NOT NULL,
    valor_compra NUMERIC,
    unidade_medida TEXT,
    bandeira TEXT
);
