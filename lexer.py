class LexerError(Exception):
    """Exceção para erros detectados durante a análise léxica."""
    pass


def estado_erro(char, buffer, pos):
    """Levanta erro léxico ao encontrar caractere inválido.

    Args:
        char: Caractere inválido encontrado.
        buffer: Conteúdo acumulado do token até o momento do erro.
        pos: Posição do caractere na linha.

    Raises:
        LexerError: Sempre levantada com mensagem detalhada.
    """
    raise LexerError(
        f"Caractere inválido '{char}' na posição {pos}. Buffer atual: '{buffer}'"
    )


def estado_parentese(char):
    """Reconhece parênteses e emite o token correspondente.

    Args:
        char: Caractere ``(`` ou ``)``.

    Returns:
        Tupla ``(proximo_estado, token, buffer)`` com o token
        ``ABRE_PAREN`` ou ``FECHA_PAREN``.
    """
    if char == '(':
        return "estado_inicial", {"tipo": "ABRE_PAREN", "valor": "("}, ""
    return "estado_inicial", {"tipo": "FECHA_PAREN", "valor": ")"}, ""


def estado_operador(char, buffer):
    """Reconhece operadores de um ou dois caracteres.

    Trata o caso especial de ``//`` (divisão inteira) que requer
    lookahead de um caractere.

    Args:
        char: Caractere atual sendo analisado.
        buffer: Buffer acumulado (contém ``/`` quando aguardando
            segundo caractere).

    Returns:
        Tupla ``(proximo_estado, token_ou_None, buffer)``.
    """
    if buffer == "/":
        # Segundo caractere após /
        if char == '/':
            return "estado_inicial", {"tipo": "OPERADOR_INT_DIV", "valor": "//"}, ""
        # Era só / — emite e reprocessa o char atual
        return "reprocessar", {"tipo": "OPERADOR", "valor": "/"}, ""
    # Primeiro caractere do operador
    if char == '/':
        # Precisa ver o próximo char para decidir / ou //
        return "estado_operador", None, "/"
    return "estado_inicial", {"tipo": "OPERADOR", "valor": char}, ""


def estado_numero(char, buffer):
    """Acumula dígitos da parte inteira de um número.

    Transita para ``estado_numero_decimal`` ao encontrar um ponto,
    ou emite o token ``NUMERO`` ao encontrar um delimitador.

    Args:
        char: Caractere atual sendo analisado.
        buffer: Dígitos acumulados até o momento.

    Returns:
        Tupla ``(proximo_estado, token_ou_None, buffer)``.

    Raises:
        LexerError: Se encontrar dois pontos decimais.
    """
    if char >= '0' and char <= '9':
        return "estado_numero", None, buffer + char
    if char == '.' and '.' not in buffer:
        return "estado_numero_decimal", None, buffer + char
    if char == '.':
        estado_erro(char, buffer, -1)
    # Delimitador — emite token e reprocessa o char atual
    return "reprocessar", {"tipo": "NUMERO", "valor": buffer}, ""


def estado_numero_decimal(char, buffer):
    """Acumula dígitos da parte fracionária após o ponto decimal.

    Emite o token ``NUMERO`` ao encontrar um delimitador.

    Args:
        char: Caractere atual sendo analisado.
        buffer: Parte inteira + ponto + dígitos fracionários acumulados.

    Returns:
        Tupla ``(proximo_estado, token_ou_None, buffer)``.

    Raises:
        LexerError: Se encontrar segundo ponto decimal.
    """
    if char >= '0' and char <= '9':
        return "estado_numero_decimal", None, buffer + char
    if char == '.':
        estado_erro(char, buffer, -1)
    # Delimitador — emite token e reprocessa o char atual
    return "reprocessar", {"tipo": "NUMERO", "valor": buffer}, ""


def estado_identificador(char, buffer):
    """Acumula letras maiúsculas para formar identificadores.

    Classifica o identificador como ``KEYWORD_RES`` (se for ``RES``)
    ou ``MEM_ID`` (qualquer outra sequência de maiúsculas).

    Args:
        char: Caractere atual sendo analisado.
        buffer: Letras maiúsculas acumuladas até o momento.

    Returns:
        Tupla ``(proximo_estado, token_ou_None, buffer)``.
    """
    if char >= 'A' and char <= 'Z':
        return "estado_identificador", None, buffer + char
    # Fim do identificador — classifica e reprocessa
    if buffer == "RES":
        return "reprocessar", {"tipo": "KEYWORD_RES", "valor": "RES"}, ""
    return "reprocessar", {"tipo": "MEM_ID", "valor": buffer}, ""


def estado_inicial(char, buffer):
    """Ponto de entrada do AFD, roteia para o estado correto.

    Analisa o caractere atual e determina a transição para o
    estado apropriado (número, identificador, operador, parêntese)
    ou levanta erro para caracteres inválidos.

    Args:
        char: Caractere atual sendo analisado.
        buffer: Buffer acumulado (não utilizado, sempre vazio).

    Returns:
        Tupla ``(proximo_estado, token_ou_None, buffer)``.

    Raises:
        LexerError: Se o caractere não for reconhecido pelo AFD.
    """
    if char == ' ' or char == '\t':
        return "estado_inicial", None, ""

    if char >= '0' and char <= '9':
        return "estado_numero", None, char

    if char >= 'A' and char <= 'Z':
        return "estado_identificador", None, char

    if char == '(' or char == ')':
        return estado_parentese(char)

    if char in ('+', '-', '*', '/', '%', '^'):
        return estado_operador(char, "")

    estado_erro(char, "", -1)


ESTADOS = {
    "estado_inicial": estado_inicial,
    "estado_numero": estado_numero,
    "estado_numero_decimal": estado_numero_decimal,
    "estado_identificador": estado_identificador,
    "estado_operador": estado_operador,
}


def tokenizar(linha):
    """Executa a análise léxica de uma linha usando o AFD.

    Percorre a linha caractere por caractere, delegando ao estado
    atual do autômato finito determinístico. Ao final, valida o
    balanceamento de parênteses.

    Args:
        linha: String com uma linha de expressão RPN.

    Returns:
        Lista de dicts ``{"tipo": str, "valor": str}`` com os
        tokens reconhecidos.

    Raises:
        LexerError: Se encontrar caractere inválido ou parênteses
            desbalanceados.
    """
    tokens = []
    pos = 0
    estado_atual = "estado_inicial"
    buffer = ""

    while pos < len(linha):
        char = linha[pos]

        estado_atual, token, buffer = ESTADOS[estado_atual](char, buffer)

        if token is not None:
            tokens.append(token)

        if estado_atual == "reprocessar":
            estado_atual = "estado_inicial"
        else:
            pos += 1

    if estado_atual == "estado_numero" or estado_atual == "estado_numero_decimal":
        tokens.append({"tipo": "NUMERO", "valor": buffer})
    elif estado_atual == "estado_identificador":
        if buffer == "RES":
            tokens.append({"tipo": "KEYWORD_RES", "valor": "RES"})
        else:
            tokens.append({"tipo": "MEM_ID", "valor": buffer})
    elif estado_atual == "estado_operador":
        tokens.append({"tipo": "OPERADOR", "valor": buffer})

    
    contador_paren = 0
    for token in tokens:
        if token["tipo"] == "ABRE_PAREN":
            contador_paren += 1
        elif token["tipo"] == "FECHA_PAREN":
            contador_paren -= 1
        if contador_paren < 0:
            raise LexerError("Parêntese de fechamento sem correspondente de abertura")

    if contador_paren != 0:
        raise LexerError("Parênteses desbalanceados: faltam parênteses de fechamento")

    return tokens
