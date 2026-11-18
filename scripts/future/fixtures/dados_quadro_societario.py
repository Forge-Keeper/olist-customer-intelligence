"""Quadro societário sintético FIXO para PJs NÃO MEI.
    
Os titulares dos MEIs já têm QSA criado pelo usuário e NÃO são
duplicados aqui. A lista abaixo reproduz os 19 cenários de QSA
já definidos e inclui mais 8 PJs usadas nos grupos ativos.

ORDENAMENTO DA TUPLA (igual ao notebook):
    ccnpj_empr, pprtcp_soctr, cindcd_quadr_soctr, ipartc_empr,
    dfim_prtcp_soctr, cclub_cli, ccpf_cnpj_pssoa_soctr, dptcao_orige

cclub_cli sempre identifica o SÓCIO (PF ímpar; PJ par), NÃO
a empresa titular do quadro societário.

Nenhum valor é sorteado, obtido de outro arquivo ou calculado em
tempo de execução. Os registros são literais e repetíveis em DV/HO.

Atenção: três CNPJs titulares (cclub_cli 112, 118, 120) vieram
da lista de QSA preparada na conversa e devem ser reconciliados
com o cadastro PJ do notebook antes da persistência.
"""
from datetime import date
from decimal import Decimal

DADOS_QSA_OUTROS_PJ = [
    # Empresa cclub_cli=66 | Borracharia Pneu Sem Drama LTDA | CNPJ 35650844000162
    ("35650844000162", Decimal("34.00"), 1, "EPHRAM TDM DIER_KO", date(1001, 10, 1), 105, "52831220009", date(2026, 5, 5)),
    ("35650844000162", Decimal("33.00"), 1, "MONGO TDM TEMPLAR", date(1001, 10, 1), 107, "70474442462", date(2026, 5, 5)),
    ("35650844000162", Decimal("33.00"), 1, "TAMERA TDM LAGRANGE", date(1001, 10, 1), 111, "77449952602", date(2026, 5, 5)),

    # Empresa cclub_cli=72 | Funilaria Martelo Diplomático LTDA | CNPJ 08730759000131
    ("08730759000131", Decimal("60.00"), 1, "DABEET TDM CHACKO", date(1001, 10, 1), 113, "63124847504", date(2026, 5, 5)),
    ("08730759000131", Decimal("40.00"), 1, "KALA TDM FALL", date(1001, 10, 1), 115, "66609568910", date(2026, 5, 5)),

    # Empresa cclub_cli=82 | Farmácia Doutor Coruja LTDA | CNPJ 66400340000118
    ("66400340000118", Decimal("60.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("66400340000118", Decimal("40.00"), 1, "EPHRAM TDM DIER_KO", date(1001, 10, 1), 105, "52831220009", date(2026, 5, 5)),

    # Empresa cclub_cli=84 | Clínica Sorriso de Jacaré LTDA | CNPJ 31929392000100
    ("31929392000100", Decimal("70.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),
    ("31929392000100", Decimal("30.00"), 1, "MONGO TDM TEMPLAR", date(1001, 10, 1), 107, "70474442462", date(2026, 5, 5)),

    # Empresa cclub_cli=88 | Pet Shop Latido Elegante LTDA | CNPJ 49043284000192
    ("49043284000192", Decimal("100.00"), 1, "Lavação Carro de Domingo MEI", date(1001, 10, 1), 68, "93773779000169", date(2026, 5, 5)),

    # Empresa cclub_cli=90 | Veterinária Pata de Ouro LTDA | CNPJ 18247047000110
    ("18247047000110", Decimal("50.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("18247047000110", Decimal("50.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),

    # Empresa cclub_cli=92 | Academia Bíceps de Algodão LTDA | CNPJ 16412297000132
    ("16412297000132", Decimal("60.00"), 1, "Lavação Carro de Domingo MEI", date(1001, 10, 1), 68, "93773779000169", date(2026, 5, 5)),
    ("16412297000132", Decimal("40.00"), 1, "TAMERA TDM LAGRANGE", date(1001, 10, 1), 111, "77449952602", date(2026, 5, 5)),

    # Empresa cclub_cli=94 | Fisioterapia Coluna Feliz LTDA | CNPJ 23211382000106
    ("23211382000106", Decimal("60.00"), 1, "DABEET TDM CHACKO", date(1001, 10, 1), 113, "63124847504", date(2026, 5, 5)),
    ("23211382000106", Decimal("40.00"), 1, "KALA TDM FALL", date(1001, 10, 1), 115, "66609568910", date(2026, 5, 5)),

    # Empresa cclub_cli=96 | Barbearia Bigode Atômico LTDA | CNPJ 55458690000119
    ("55458690000119", Decimal("60.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("55458690000119", Decimal("25.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),
    ("55458690000119", Decimal("15.00"), 1, "EPHRAM TDM DIER_KO", date(1001, 10, 1), 105, "52831220009", date(2026, 5, 5)),

    # Empresa cclub_cli=102 | Papelaria Lápis Encantado LTDA | CNPJ 91586998000103
    ("91586998000103", Decimal("51.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),
    ("91586998000103", Decimal("49.00"), 1, "MONGO TDM TEMPLAR", date(1001, 10, 1), 107, "70474442462", date(2026, 5, 5)),

    # Empresa cclub_cli=104 | Gráfica Letra Torta LTDA | CNPJ 99944451000144
    ("99944451000144", Decimal("50.00"), 1, "EPHRAM TDM DIER_KO", date(1001, 10, 1), 105, "52831220009", date(2026, 5, 5)),
    ("99944451000144", Decimal("50.00"), 1, "TAMERA TDM LAGRANGE", date(1001, 10, 1), 111, "77449952602", date(2026, 5, 5)),

    # Empresa cclub_cli=106 | Livraria Virada de Página LTDA | CNPJ 19271940000143
    ("19271940000143", Decimal("49.99"), 1, "Lavação Carro de Domingo MEI", date(1001, 10, 1), 68, "93773779000169", date(2026, 5, 5)),
    ("19271940000143", Decimal("50.01"), 1, "DABEET TDM CHACKO", date(1001, 10, 1), 113, "63124847504", date(2026, 5, 5)),

    # Empresa cclub_cli=108 | Armarinho Linha do Horizonte LTDA | CNPJ 74254453000180
    ("74254453000180", Decimal("34.00"), 1, "KALA TDM FALL", date(1001, 10, 1), 115, "66609568910", date(2026, 5, 5)),
    ("74254453000180", Decimal("33.00"), 1, "EPHRAM TDM DIER_KO", date(1001, 10, 1), 105, "52831220009", date(2026, 5, 5)),
    ("74254453000180", Decimal("33.00"), 1, "MONGO TDM TEMPLAR", date(1001, 10, 1), 107, "70474442462", date(2026, 5, 5)),

    # Empresa cclub_cli=110 | Loja de Presentes Surpresa do Zé LTDA | CNPJ 05772590000194
    ("05772590000194", Decimal("70.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("05772590000194", Decimal("30.00"), 1, "Lavação Carro de Domingo MEI", date(1001, 10, 1), 68, "93773779000169", date(2026, 5, 5)),

    # Empresa cclub_cli=112 | Bazar Tem de Tudo Mesmo LTDA | CNPJ 20010176000131
    ("20010176000131", Decimal("100.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),

    # Empresa cclub_cli=114 | Brechó Elegância Recuperada LTDA | CNPJ 48383213000176
    ("48383213000176", Decimal("100.00"), 1, "TAMERA TDM LAGRANGE", date(1001, 10, 1), 111, "77449952602", date(2026, 5, 5)),

    # Empresa cclub_cli=116 | Ateliê Agulha Voadora LTDA | CNPJ 09245260000100
    ("09245260000100", Decimal("60.00"), 1, "Lavação Carro de Domingo MEI", date(1001, 10, 1), 68, "93773779000169", date(2026, 5, 5)),
    ("09245260000100", Decimal("40.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),

    # Empresa cclub_cli=118 | Costureira Ponto e Vírgula LTDA | CNPJ 52592529000145
    ("52592529000145", Decimal("60.00"), 1, "KALA TDM FALL", date(1001, 10, 1), 115, "66609568910", date(2026, 5, 5)),
    ("52592529000145", Decimal("40.00"), 1, "DABEET TDM CHACKO", date(1001, 10, 1), 113, "63124847504", date(2026, 5, 5)),

    # Empresa cclub_cli=120 | Sapataria Passo de Gigante LTDA | CNPJ 45639543000191
    ("45639543000191", Decimal("50.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("45639543000191", Decimal("25.00"), 1, "EPHRAM TDM DIER_KO", date(1001, 10, 1), 105, "52831220009", date(2026, 5, 5)),
    ("45639543000191", Decimal("25.00"), 1, "DABEET TDM CHACKO", date(1001, 10, 1), 113, "63124847504", date(2026, 5, 5)),

    # Empresa cclub_cli=74 | Peças do Fusca Veloz LTDA | CNPJ 75538340000108
    ("75538340000108", Decimal("60.00"), 1, "RISHIKESH TDM BLUNDEN", date(1001, 10, 1), 117, "01860259391", date(2026, 5, 5)),
    ("75538340000108", Decimal("40.00"), 1, "TEJESHWAR TDM POND", date(1001, 10, 1), 119, "43809353370", date(2026, 5, 5)),

    # Empresa cclub_cli=98 | Salão Cachos Rebeldes LTDA | CNPJ 08619104000190
    ("08619104000190", Decimal("60.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("08619104000190", Decimal("40.00"), 1, "ATIQA TDM LOGAN", date(1001, 10, 1), 121, "49796617692", date(2026, 5, 5)),

    # Empresa cclub_cli=122 | Material de Construção Tijolo Ninja LTDA | CNPJ 17122868000167
    ("17122868000167", Decimal("100.00"), 1, "SHAUNAK TDM JAKUBIK", date(1001, 10, 1), 123, "43919225767", date(2026, 5, 5)),

    # Empresa cclub_cli=124 | Ferragens Pregão do Bode LTDA | CNPJ 30902347000190
    ("30902347000190", Decimal("34.00"), 1, "RISHIKESH TDM BLUNDEN", date(1001, 10, 1), 117, "01860259391", date(2026, 5, 5)),
    ("30902347000190", Decimal("33.00"), 1, "TEJESHWAR TDM POND", date(1001, 10, 1), 119, "43809353370", date(2026, 5, 5)),
    ("30902347000190", Decimal("33.00"), 1, "ATIQA TDM LOGAN", date(1001, 10, 1), 121, "49796617692", date(2026, 5, 5)),

    # Empresa cclub_cli=126 | Eletrônica Curto Circuito Feliz LTDA | CNPJ 55067144000157
    ("55067144000157", Decimal("55.00"), 1, "Lavação Carro de Domingo MEI", date(1001, 10, 1), 68, "93773779000169", date(2026, 5, 5)),
    ("55067144000157", Decimal("45.00"), 1, "SHAUNAK TDM JAKUBIK", date(1001, 10, 1), 123, "43919225767", date(2026, 5, 5)),

    # Empresa cclub_cli=128 | Assistência Celular Tela Triste LTDA | CNPJ 67486384000175
    ("67486384000175", Decimal("50.00"), 1, "Oficina Parafuso Filosófico MEI", date(1001, 10, 1), 62, "39070293000119", date(2026, 5, 5)),
    ("67486384000175", Decimal("50.00"), 1, "Auto Elétrica Vagalume Noturno MEI", date(1001, 10, 1), 64, "47911744000121", date(2026, 5, 5)),

    # Empresa cclub_cli=130 | Informática Byte do Interior LTDA | CNPJ 71192259000120
    ("71192259000120", Decimal("100.00"), 1, "TEJESHWAR TDM POND", date(1001, 10, 1), 119, "43809353370", date(2026, 5, 5)),

    # Empresa cclub_cli=132 | Internet Fibra do Saci LTDA | CNPJ 46646545000170
    ("46646545000170", Decimal("60.00"), 1, "RISHIKESH TDM BLUNDEN", date(1001, 10, 1), 117, "01860259391", date(2026, 5, 5)),
    ("46646545000170", Decimal("40.00"), 1, "ATIQA TDM LOGAN", date(1001, 10, 1), 121, "49796617692", date(2026, 5, 5)),

]
