"""
Cargas de entrada derivadas das heurísticas de teste (Elisabeth Hendrickson,
Test Heuristics Cheat Sheet — Test Obsessed).

Cada constante aponta a heurística que a originou, para o teste poder citá-la.
"""

# --- Testes de Strings -------------------------------------------------------

TEXTO_LONGO = lambda tamanho: 'A' * tamanho  # noqa: E731 - "strings longas"
ACENTUADO = 'Ãçêñtõs àéîôü — Remédio Nº1'  # "caracteres acentuados"
ASIATICO = '薬の時間です'  # "caracteres asiáticos"
DELIMITADORES = 'Nome com "aspas", \'apóstrofo\', <tag> & ponto-e-vírgula;'  # "caracteres especiais"
INJECAO_SQL = "Losartana'); DROP TABLE medications; --"  # "injeção de SQL"
EM_BRANCO = ''  # "em branco"
SO_ESPACOS = '   '  # "em branco"
ESPACOS_NAS_BORDAS = '  Losartana  '  # "espaços no início ou fim"

# --- Ataques de Tipos de Dados ----------------------------------------------

DATAS_INVALIDAS = [
    '30/02/2026',  # "dias inválidos"
    '31/09/2026',  # "dias inválidos"
    '32/01/2026',
    '00/01/2026',
]

FORMATOS_DE_DATA_RECUSADOS = [
    '5 de junho de 2001',  # "formatos de data"
    '2026-11-26',
    '06-05-01',
    '6/5/26',
]

HORARIOS_INVALIDOS = ['24:00', '07:60', '-1:00', '8h30', 'manhã', '08:30:00', '', '::']
HORARIOS_VALIDOS = ['00:00', '08:30', '23:59', '8:30']

INTERVALOS_INVALIDOS = ['0', '25', '-3', '1.5', 'três', '']
INTERVALOS_VALIDOS = ['1', '24', ' 3 ']

# --- Massa fictícia ----------------------------------------------------------

MEDICAMENTO_VALIDO = {
    'nome': 'Losartana Fictícia',
    'dosagem': '50mg',
    'quantidade': '1 comprimido',
}
