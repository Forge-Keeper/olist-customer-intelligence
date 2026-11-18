"""18 GEs FIXOS: seis normais (1), seis isolados (5), seis gerenciais (6).
Colunas: cgrp_econm, ctpo_grp_econm, igrp_econm, itpo_grp_econm,
dincl_reg, dult_atulz_reg, hprocm_dia.
"""
from datetime import date, datetime

DADOS_GRUPOS_ATIVOS = [
    (910101, 1, "GRUPO TESTE NORMAL 01", "NORMAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910102, 1, "GRUPO TESTE NORMAL 02", "NORMAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910103, 1, "GRUPO TESTE NORMAL 03", "NORMAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910104, 1, "GRUPO TESTE NORMAL 04", "NORMAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910105, 1, "GRUPO TESTE NORMAL 05", "NORMAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910106, 1, "GRUPO TESTE NORMAL 06", "NORMAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910501, 5, "GRUPO TESTE ISOLADO 01", "ISOLADO", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910502, 5, "GRUPO TESTE ISOLADO 02", "ISOLADO", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910503, 5, "GRUPO TESTE ISOLADO 03", "ISOLADO", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910504, 5, "GRUPO TESTE ISOLADO 04", "ISOLADO", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910505, 5, "GRUPO TESTE ISOLADO 05", "ISOLADO", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910506, 5, "GRUPO TESTE ISOLADO 06", "ISOLADO", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910601, 6, "GRUPO TESTE GERENCIAL 01", "GERENCIAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910602, 6, "GRUPO TESTE GERENCIAL 02", "GERENCIAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910603, 6, "GRUPO TESTE GERENCIAL 03", "GERENCIAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910604, 6, "GRUPO TESTE GERENCIAL 04", "GERENCIAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910605, 6, "GRUPO TESTE GERENCIAL 05", "GERENCIAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
    (910606, 6, "GRUPO TESTE GERENCIAL 06", "GERENCIAL", date(2026, 5, 5), date(2026, 5, 5), datetime(2026, 5, 5, 9, 0, 0)),
]
