from lexer import tokenizar, LexerError


def parseExpressao(linha, tokens):
    """Extrai e valida tokens de uma linha de expressão RPN.

    Utiliza o analisador léxico para tokenizar a linha e verifica
    se a expressão contém tanto parênteses quanto operadores ou
    comandos. Expressões que não atendem esse critério são descartadas.

    Args:
        linha: String com uma linha de expressão RPN.
        tokens: Lista mutável a ser preenchida com os tokens extraídos.

    Returns:
        Mesma referência de ``tokens``, preenchida com os tokens
        válidos ou vazia se a expressão for inválida.

    Raises:
        LexerError: Se o analisador léxico detectar caractere inválido
            ou parênteses desbalanceados.
    """
    try:
        resultado = tokenizar(linha)
    except LexerError:
        tokens.clear()
        raise

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
