from lexer import tokenizar


def parseExpressao(linha, tokens):
    """
    Extrai tokens de uma linha de expressão RPN usando o analisador léxico.

    Parâmetros:
        linha: string com uma expressão RPN
        tokens: lista mutável a ser preenchida com os tokens extraídos

    Retorna:
        lista de tokens (mesma referência de `tokens`, também retornada).
        Em caso de erro léxico, retorna lista vazia.
    """
    try:
        resultado = tokenizar(linha)
    except Exception:
        tokens.clear()
        return tokens

    tem_parentese = False
    tem_operador_ou_comando = False

    for tok in resultado:
        tipo = tok["tipo"]
        if tipo in ("ABRE_PAREN", "FECHA_PAREN"):
            tem_parentese = True
        if tipo in ("OPERADOR", "OPERADOR_INT_DIV", "KEYWORD_RES", "MEM_ID"):
            tem_operador_ou_comando = True

    if not (tem_parentese and tem_operador_ou_comando):
        tokens.clear()
        return tokens

    tokens.clear()
    tokens.extend(resultado)
    return tokens
