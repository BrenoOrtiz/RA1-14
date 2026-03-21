
def estado_erro(char, buffer, pos):
    """Estado de absorção de erros. Levanta LexerError com mensagem detalhada."""
    raise LexerError(
        f"Caractere inválido '{char}' na posição {pos}. Buffer atual: '{buffer}'"
    )


def estado_parentese(char):
    """Reconhece parênteses e emite o token correspondente."""
    if char == '(':
        return "estado_inicial", {"tipo": "ABRE_PAREN", "valor": "("}, ""
    return "estado_inicial", {"tipo": "FECHA_PAREN", "valor": ")"}, ""


def estado_operador(char, buffer):
    """Reconhece operadores de um ou dois caracteres."""
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
    """Acumula dígitos e no máximo um ponto decimal para formar um NUMERO."""
    if char >= '0' and char <= '9':
        return "estado_numero", None, buffer + char
    if char == '.' and '.' not in buffer:
        return "estado_numero_decimal", None, buffer + char
    if char == '.':
        estado_erro(char, buffer, -1)
    # Delimitador — emite token e reprocessa o char atual
    return "reprocessar", {"tipo": "NUMERO", "valor": buffer}, ""


def estado_numero_decimal(char, buffer):
    """Acumula a parte fracionária do número após o ponto decimal."""
    if char >= '0' and char <= '9':
        return "estado_numero_decimal", None, buffer + char
    if char == '.':
        estado_erro(char, buffer, -1)
    # Delimitador — emite token e reprocessa o char atual
    return "reprocessar", {"tipo": "NUMERO", "valor": buffer}, ""


def estado_identificador(char, buffer):
    """Acumula letras maiúsculas para formar identificadores (MEM, RES, etc.)."""
    if char >= 'A' and char <= 'Z':
        return "estado_identificador", None, buffer + char
    # Fim do identificador — classifica e reprocessa
    if buffer == "RES":
        return "reprocessar", {"tipo": "KEYWORD_RES", "valor": "RES"}, ""
    return "reprocessar", {"tipo": "MEM_ID", "valor": buffer}, ""


def estado_inicial(char, buffer):
    """
    Ponto de entrada do AFD. Roteia para o estado correto com base no caractere.
    Retorna (proximo_estado, token_ou_None, buffer).
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

