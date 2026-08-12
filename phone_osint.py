"""
GEONIV OSINT — Módulo de Inteligência Telefônica
Consulta de dados públicos a partir de número de telefone.
Tabela completa de DDDs brasileiros, identificação de operadora,
tipo de linha e geração de links OSINT para investigação externa.
"""

import re
import urllib.parse

# =============================================================================
# TABELA DE DDDs BRASILEIROS — Estado, Cidade Principal, Coordenadas
# =============================================================================
DDD_TABLE = {
    # São Paulo
    "11": {"uf": "SP", "city": "São Paulo", "lat": -23.5505, "lng": -46.6333, "tz": "America/Sao_Paulo"},
    "12": {"uf": "SP", "city": "São José dos Campos", "lat": -23.1896, "lng": -45.8841, "tz": "America/Sao_Paulo"},
    "13": {"uf": "SP", "city": "Santos", "lat": -23.9608, "lng": -46.3336, "tz": "America/Sao_Paulo"},
    "14": {"uf": "SP", "city": "Bauru", "lat": -22.3246, "lng": -49.0871, "tz": "America/Sao_Paulo"},
    "15": {"uf": "SP", "city": "Sorocaba", "lat": -23.5015, "lng": -47.4526, "tz": "America/Sao_Paulo"},
    "16": {"uf": "SP", "city": "Ribeirão Preto", "lat": -21.1704, "lng": -47.8103, "tz": "America/Sao_Paulo"},
    "17": {"uf": "SP", "city": "São José do Rio Preto", "lat": -20.8113, "lng": -49.3758, "tz": "America/Sao_Paulo"},
    "18": {"uf": "SP", "city": "Presidente Prudente", "lat": -22.1256, "lng": -51.3889, "tz": "America/Sao_Paulo"},
    "19": {"uf": "SP", "city": "Campinas", "lat": -22.9099, "lng": -47.0626, "tz": "America/Sao_Paulo"},
    # Rio de Janeiro
    "21": {"uf": "RJ", "city": "Rio de Janeiro", "lat": -22.9068, "lng": -43.1729, "tz": "America/Sao_Paulo"},
    "22": {"uf": "RJ", "city": "Campos dos Goytacazes", "lat": -21.7545, "lng": -41.3244, "tz": "America/Sao_Paulo"},
    "24": {"uf": "RJ", "city": "Volta Redonda / Petrópolis", "lat": -22.5231, "lng": -44.1039, "tz": "America/Sao_Paulo"},
    # Espírito Santo
    "27": {"uf": "ES", "city": "Vitória", "lat": -20.3155, "lng": -40.3128, "tz": "America/Sao_Paulo"},
    "28": {"uf": "ES", "city": "Cachoeiro de Itapemirim", "lat": -20.8489, "lng": -41.1128, "tz": "America/Sao_Paulo"},
    # Minas Gerais
    "31": {"uf": "MG", "city": "Belo Horizonte", "lat": -19.9191, "lng": -43.9386, "tz": "America/Sao_Paulo"},
    "32": {"uf": "MG", "city": "Juiz de Fora", "lat": -21.7642, "lng": -43.3503, "tz": "America/Sao_Paulo"},
    "33": {"uf": "MG", "city": "Governador Valadares", "lat": -18.8510, "lng": -41.9494, "tz": "America/Sao_Paulo"},
    "34": {"uf": "MG", "city": "Uberlândia", "lat": -18.9186, "lng": -48.2772, "tz": "America/Sao_Paulo"},
    "35": {"uf": "MG", "city": "Poços de Caldas", "lat": -21.7877, "lng": -46.5613, "tz": "America/Sao_Paulo"},
    "37": {"uf": "MG", "city": "Divinópolis", "lat": -20.1389, "lng": -44.8842, "tz": "America/Sao_Paulo"},
    "38": {"uf": "MG", "city": "Montes Claros", "lat": -16.7350, "lng": -43.8614, "tz": "America/Sao_Paulo"},
    # Paraná
    "41": {"uf": "PR", "city": "Curitiba", "lat": -25.4284, "lng": -49.2733, "tz": "America/Sao_Paulo"},
    "42": {"uf": "PR", "city": "Ponta Grossa", "lat": -25.0946, "lng": -50.1613, "tz": "America/Sao_Paulo"},
    "43": {"uf": "PR", "city": "Londrina", "lat": -23.3045, "lng": -51.1696, "tz": "America/Sao_Paulo"},
    "44": {"uf": "PR", "city": "Maringá", "lat": -23.4205, "lng": -51.9333, "tz": "America/Sao_Paulo"},
    "45": {"uf": "PR", "city": "Cascavel / Foz do Iguaçu", "lat": -25.5163, "lng": -54.5854, "tz": "America/Sao_Paulo"},
    "46": {"uf": "PR", "city": "Pato Branco / Francisco Beltrão", "lat": -26.2292, "lng": -52.6706, "tz": "America/Sao_Paulo"},
    # Santa Catarina
    "47": {"uf": "SC", "city": "Joinville", "lat": -26.3044, "lng": -48.8487, "tz": "America/Sao_Paulo"},
    "48": {"uf": "SC", "city": "Florianópolis", "lat": -27.5954, "lng": -48.5480, "tz": "America/Sao_Paulo"},
    "49": {"uf": "SC", "city": "Chapecó / Lages", "lat": -27.1006, "lng": -52.6158, "tz": "America/Sao_Paulo"},
    # Rio Grande do Sul
    "51": {"uf": "RS", "city": "Porto Alegre", "lat": -30.0346, "lng": -51.2177, "tz": "America/Sao_Paulo"},
    "53": {"uf": "RS", "city": "Pelotas / Rio Grande", "lat": -31.7654, "lng": -52.3376, "tz": "America/Sao_Paulo"},
    "54": {"uf": "RS", "city": "Caxias do Sul", "lat": -29.1681, "lng": -51.1794, "tz": "America/Sao_Paulo"},
    "55": {"uf": "RS", "city": "Santa Maria", "lat": -29.6842, "lng": -53.8069, "tz": "America/Sao_Paulo"},
    # Distrito Federal / Goiás
    "61": {"uf": "DF", "city": "Brasília", "lat": -15.7975, "lng": -47.8919, "tz": "America/Sao_Paulo"},
    "62": {"uf": "GO", "city": "Goiânia", "lat": -16.6869, "lng": -49.2648, "tz": "America/Sao_Paulo"},
    "64": {"uf": "GO", "city": "Rio Verde / Itumbiara", "lat": -17.7928, "lng": -50.9297, "tz": "America/Sao_Paulo"},
    # Tocantins
    "63": {"uf": "TO", "city": "Palmas", "lat": -10.1689, "lng": -48.3317, "tz": "America/Sao_Paulo"},
    # Mato Grosso do Sul
    "67": {"uf": "MS", "city": "Campo Grande", "lat": -20.4697, "lng": -54.6201, "tz": "America/Campo_Grande"},
    # Mato Grosso
    "65": {"uf": "MT", "city": "Cuiabá", "lat": -15.5989, "lng": -56.0949, "tz": "America/Cuiaba"},
    "66": {"uf": "MT", "city": "Rondonópolis", "lat": -16.4712, "lng": -54.6356, "tz": "America/Cuiaba"},
    # Acre
    "68": {"uf": "AC", "city": "Rio Branco", "lat": -9.9753, "lng": -67.8100, "tz": "America/Rio_Branco"},
    # Rondônia
    "69": {"uf": "RO", "city": "Porto Velho", "lat": -8.7612, "lng": -63.9004, "tz": "America/Porto_Velho"},
    # Bahia
    "71": {"uf": "BA", "city": "Salvador", "lat": -12.9714, "lng": -38.5124, "tz": "America/Bahia"},
    "73": {"uf": "BA", "city": "Ilhéus / Itabuna", "lat": -14.7928, "lng": -39.0404, "tz": "America/Bahia"},
    "74": {"uf": "BA", "city": "Juazeiro", "lat": -9.4310, "lng": -40.5033, "tz": "America/Bahia"},
    "75": {"uf": "BA", "city": "Feira de Santana", "lat": -12.2669, "lng": -38.9666, "tz": "America/Bahia"},
    "77": {"uf": "BA", "city": "Vitória da Conquista", "lat": -14.8619, "lng": -40.8444, "tz": "America/Bahia"},
    # Sergipe
    "79": {"uf": "SE", "city": "Aracaju", "lat": -10.9091, "lng": -37.0677, "tz": "America/Bahia"},
    # Pernambuco
    "81": {"uf": "PE", "city": "Recife", "lat": -8.0476, "lng": -34.8770, "tz": "America/Recife"},
    "87": {"uf": "PE", "city": "Petrolina / Garanhuns", "lat": -9.3891, "lng": -40.5028, "tz": "America/Recife"},
    # Alagoas
    "82": {"uf": "AL", "city": "Maceió", "lat": -9.6658, "lng": -35.7353, "tz": "America/Recife"},
    # Paraíba
    "83": {"uf": "PB", "city": "João Pessoa", "lat": -7.1195, "lng": -34.8450, "tz": "America/Recife"},
    # Rio Grande do Norte
    "84": {"uf": "RN", "city": "Natal", "lat": -5.7793, "lng": -35.2009, "tz": "America/Recife"},
    # Ceará
    "85": {"uf": "CE", "city": "Fortaleza", "lat": -3.7172, "lng": -38.5433, "tz": "America/Fortaleza"},
    "88": {"uf": "CE", "city": "Juazeiro do Norte / Sobral", "lat": -7.2132, "lng": -39.3157, "tz": "America/Fortaleza"},
    # Piauí
    "86": {"uf": "PI", "city": "Teresina", "lat": -5.0920, "lng": -42.8038, "tz": "America/Fortaleza"},
    "89": {"uf": "PI", "city": "Picos / Floriano", "lat": -7.0768, "lng": -41.4669, "tz": "America/Fortaleza"},
    # Maranhão
    "98": {"uf": "MA", "city": "São Luís", "lat": -2.5387, "lng": -44.2826, "tz": "America/Fortaleza"},
    "99": {"uf": "MA", "city": "Imperatriz", "lat": -5.5194, "lng": -47.4735, "tz": "America/Fortaleza"},
    # Pará
    "91": {"uf": "PA", "city": "Belém", "lat": -1.4558, "lng": -48.5024, "tz": "America/Belem"},
    "93": {"uf": "PA", "city": "Santarém", "lat": -2.4426, "lng": -54.7085, "tz": "America/Belem"},
    "94": {"uf": "PA", "city": "Marabá", "lat": -5.3687, "lng": -49.1178, "tz": "America/Belem"},
    # Amazonas
    "92": {"uf": "AM", "city": "Manaus", "lat": -3.1190, "lng": -60.0217, "tz": "America/Manaus"},
    "97": {"uf": "AM", "city": "Tefé / Parintins", "lat": -3.3687, "lng": -64.7108, "tz": "America/Manaus"},
    # Roraima
    "95": {"uf": "RR", "city": "Boa Vista", "lat": 2.8195, "lng": -60.6714, "tz": "America/Boa_Vista"},
    # Amapá
    "96": {"uf": "AP", "city": "Macapá", "lat": 0.0345, "lng": -51.0694, "tz": "America/Belem"},
}


def parse_phone_number(raw: str) -> dict:
    """
    Limpa, valida e extrai componentes de um número de telefone.
    Suporta formatos brasileiros: +55 11 98765-4321, (11) 98765-4321, 11987654321, etc.
    """
    # Remove tudo que não é dígito nem +
    cleaned = re.sub(r"[^\d+]", "", raw.strip())

    result = {
        "raw_input": raw.strip(),
        "cleaned": cleaned,
        "country_code": None,
        "ddd": None,
        "subscriber": None,
        "is_brazilian": False,
        "is_valid_format": False,
        "formatted": None,
    }

    # Detectar e remover código de país
    digits_only = re.sub(r"[^\d]", "", cleaned)

    if cleaned.startswith("+55") or (len(digits_only) >= 12 and digits_only.startswith("55")):
        result["country_code"] = "55"
        digits_only = digits_only[2:]  # Remove 55
        result["is_brazilian"] = True
    elif len(digits_only) >= 10 and len(digits_only) <= 11:
        # Provavelmente brasileiro sem código de país
        result["country_code"] = "55"
        result["is_brazilian"] = True
    elif cleaned.startswith("+"):
        # Número internacional
        result["country_code"] = digits_only[:2]
        result["is_brazilian"] = False

    if result["is_brazilian"]:
        # Número brasileiro: DDD (2 dígitos) + 8 ou 9 dígitos
        if len(digits_only) >= 10:
            result["ddd"] = digits_only[:2]
            result["subscriber"] = digits_only[2:]
            result["is_valid_format"] = len(digits_only) in (10, 11)

            if len(digits_only) == 11:
                result["formatted"] = f"+55 ({result['ddd']}) {result['subscriber'][:5]}-{result['subscriber'][5:]}"
            elif len(digits_only) == 10:
                result["formatted"] = f"+55 ({result['ddd']}) {result['subscriber'][:4]}-{result['subscriber'][4:]}"
        elif len(digits_only) >= 8:
            # Sem DDD
            result["subscriber"] = digits_only
            result["is_valid_format"] = False
    else:
        result["formatted"] = cleaned
        result["is_valid_format"] = len(digits_only) >= 7

    return result


def identify_line_type(parsed: dict) -> str:
    """
    Identifica tipo de linha baseado no formato do número brasileiro.
    Celulares brasileiros têm 9 dígitos (começando com 9).
    Fixos têm 8 dígitos (começando com 2-5).
    """
    subscriber = parsed.get("subscriber", "")
    if not subscriber or not parsed.get("is_brazilian"):
        return "Desconhecido"

    if len(subscriber) == 9 and subscriber.startswith("9"):
        return "Celular / Móvel"
    elif len(subscriber) == 8:
        first_digit = subscriber[0]
        if first_digit in ("2", "3", "4", "5"):
            return "Telefone Fixo"
        elif first_digit in ("7", "8", "9"):
            return "Celular / Móvel (formato antigo)"
        else:
            return "Fixo / Especial"
    elif len(subscriber) >= 3 and subscriber.startswith("0800"):
        return "Linha Gratuita (0800)"
    else:
        return "Formato não identificado"


def identify_carrier_hint(parsed: dict) -> str:
    """
    Tentativa de identificação de operadora pelo prefixo do número.
    Nota: Desde a portabilidade numérica, o prefixo original pode não
    refletir a operadora atual. Isso é apenas uma indicação do chip original.
    """
    subscriber = parsed.get("subscriber", "")
    if not subscriber or not parsed.get("is_brazilian"):
        return "Não identificada (número internacional)"

    # Prefixos comuns (chip original, antes de portabilidade)
    # Os 4 primeiros dígitos do subscriber (sem o 9 inicial em celulares)
    if len(subscriber) == 9:
        prefix_4 = subscriber[1:5]  # Remove o 9 inicial
    elif len(subscriber) == 8:
        prefix_4 = subscriber[:4]
    else:
        return "Não identificada"

    prefix_2 = prefix_4[:2] if len(prefix_4) >= 2 else ""

    # Faixas aproximadas (podem variar por região)
    vivo_ranges = ("96", "97", "98", "99")
    claro_ranges = ("91", "92", "93", "94", "95", "73", "74", "75")
    tim_ranges = ("80", "81", "82", "83", "84", "85")
    oi_ranges = ("86", "87", "88", "89")

    if prefix_2 in vivo_ranges:
        return "Vivo (Telefônica) — indicação pelo prefixo original"
    elif prefix_2 in claro_ranges:
        return "Claro (América Móvil) — indicação pelo prefixo original"
    elif prefix_2 in tim_ranges:
        return "TIM (Telecom Italia) — indicação pelo prefixo original"
    elif prefix_2 in oi_ranges:
        return "Oi (Telemar) — indicação pelo prefixo original"
    else:
        return "Operadora não determinada pelo prefixo"


def get_ddd_info(ddd: str) -> dict | None:
    """Retorna informações geográficas do DDD brasileiro."""
    return DDD_TABLE.get(ddd)


def generate_osint_links(phone_raw: str, parsed: dict) -> list:
    """
    Gera links para plataformas de OSINT externas onde o usuário pode
    pesquisar informações públicas sobre o número.
    """
    # Número limpo para busca
    cleaned = re.sub(r"[^\d]", "", phone_raw.strip())
    if parsed.get("is_brazilian") and not cleaned.startswith("55"):
        cleaned = "55" + cleaned

    formatted_search = parsed.get("formatted") or phone_raw.strip()
    encoded_raw = urllib.parse.quote_plus(formatted_search)
    encoded_clean = urllib.parse.quote_plus(cleaned)
    encoded_plus = urllib.parse.quote_plus(f"+{cleaned}")

    links = [
        {
            "name": "Google Search",
            "url": f"https://www.google.com/search?q=%22{encoded_clean}%22",
            "icon": "fa-brands fa-google",
            "color": "#4285f4",
            "description": "Pesquisa aberta por menções públicas do número"
        },
        {
            "name": "Truecaller",
            "url": f"https://www.truecaller.com/search/br/{cleaned}",
            "icon": "fa-solid fa-phone-volume",
            "color": "#1fb6ff",
            "description": "Identificação do proprietário e reputação"
        },
        {
            "name": "Sync.me",
            "url": f"https://sync.me/search/?number={encoded_plus}",
            "icon": "fa-solid fa-address-book",
            "color": "#6366f1",
            "description": "Identificação social e nome do proprietário"
        },
        {
            "name": "Quem Me Ligou?",
            "url": f"https://www.tellows.com.br/num/{cleaned[-10:] if len(cleaned) > 10 else cleaned}",
            "icon": "fa-solid fa-shield-halved",
            "color": "#ef4444",
            "description": "Reputação do número: spam, golpe ou legítimo"
        },
        {
            "name": "NumLookup",
            "url": f"https://www.numlookup.com/br/{cleaned}",
            "icon": "fa-solid fa-magnifying-glass",
            "color": "#10b981",
            "description": "Validação e identificação de operadora"
        },
        {
            "name": "Facebook",
            "url": f"https://www.facebook.com/search/top/?q={encoded_clean}",
            "icon": "fa-brands fa-facebook",
            "color": "#1877f2",
            "description": "Pesquisar perfis vinculados ao número"
        },
        {
            "name": "WhatsApp Check",
            "url": f"https://wa.me/{cleaned}",
            "icon": "fa-brands fa-whatsapp",
            "color": "#25d366",
            "description": "Verificar se o número possui WhatsApp ativo"
        },
        {
            "name": "Telegram",
            "url": f"https://t.me/+{cleaned}",
            "icon": "fa-brands fa-telegram",
            "color": "#0088cc",
            "description": "Verificar perfil no Telegram"
        },
    ]

    return links


def phone_lookup(raw_phone: str) -> dict:
    """
    Função principal: analisa um número de telefone e retorna todos os
    dados OSINT disponíveis offline + links para investigação externa.
    """
    parsed = parse_phone_number(raw_phone)

    result = {
        "input": raw_phone.strip(),
        "formatted": parsed.get("formatted"),
        "country_code": parsed.get("country_code"),
        "ddd": parsed.get("ddd"),
        "subscriber": parsed.get("subscriber"),
        "is_brazilian": parsed.get("is_brazilian", False),
        "is_valid_format": parsed.get("is_valid_format", False),
        "line_type": identify_line_type(parsed),
        "carrier_hint": identify_carrier_hint(parsed),
        "ddd_info": None,
        "osint_links": generate_osint_links(raw_phone, parsed),
        "warnings": [],
    }

    # Dados geográficos do DDD
    if parsed.get("ddd"):
        ddd_info = get_ddd_info(parsed["ddd"])
        if ddd_info:
            result["ddd_info"] = ddd_info
        else:
            result["warnings"].append(f"DDD {parsed['ddd']} não encontrado na tabela brasileira.")

    # Avisos úteis
    if not parsed.get("is_valid_format"):
        result["warnings"].append("O formato do número pode estar incompleto ou incorreto.")

    result["warnings"].append(
        "A operadora indicada é baseada no prefixo original do chip. "
        "Devido à portabilidade numérica, o número pode ter sido transferido para outra operadora."
    )

    return result
