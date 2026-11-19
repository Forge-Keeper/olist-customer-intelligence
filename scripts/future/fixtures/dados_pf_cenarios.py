"""PFs adicionais reservadas a cenários de homologação.

APENAS OVERLAY DE TESTE: identificadores 281..299 já estão dentro da faixa
prevista de 100 PFs. Conciliar/repor estes IDs no cadastro sintético do
ambiente; não fazer append cego se já existirem documentos diferentes.
Cada documento é gerado antecipadamente e fixado como literal para repetição.
Tupla: (cclub_cli, ccpf_pssoa, nome).
"""

DADOS_PF_CENARIOS = [
    (281, "73002725765", "PESSOA FISICA SINTETICA 281"),
    (283, "73002745103", "PESSOA FISICA SINTETICA 283"),
    (285, "73002764582", "PESSOA FISICA SINTETICA 285"),
    (287, "73002783960", "PESSOA FISICA SINTETICA 287"),
    (289, "73002803316", "PESSOA FISICA SINTETICA 289"),
    (291, "73002822701", "PESSOA FISICA SINTETICA 291"),
    (293, "73002842133", "PESSOA FISICA SINTETICA 293"),
    (295, "73002861510", "PESSOA FISICA SINTETICA 295"),
    (297, "73002880906", "PESSOA FISICA SINTETICA 297"),
    (299, "73002900354", "PESSOA FISICA SINTETICA 299"),
]
