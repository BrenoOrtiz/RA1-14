class ExecError(Exception):
    """Exceção para erros semânticos durante a execução de expressões RPN."""
    pass


def _aplicar_operador(op, b, a):
    """Aplica um operador binário sobre dois operandos.

    Em notação RPN o operando ``a`` é empilhado antes de ``b``, portanto
    a operação realizada é ``a op b``.

    Args:
        op: String do operador (``+``, ``-``, ``*``, ``/``, ``//``, ``%``, ``^``).
        b: Operando do topo da pilha (float).
        a: Operando abaixo do topo da pilha (float).

    Returns:
        Resultado da operação como float.

    Raises:
        ExecError: Se houver divisão por zero, expoente negativo ou operador desconhecido.
    """
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            raise ExecError("Divisão por zero")
        return a / b
    elif op == '//':
        if b == 0:
            raise ExecError("Divisão inteira por zero")
        return float(int(a) // int(b))
    elif op == '%':
        if b == 0:
            raise ExecError("Resto por zero")
        return float(int(a) % int(b))
    elif op == '^':
        exp = int(b)
        if exp < 0:
            raise ExecError(f"Expoente deve ser inteiro >= 0, recebido: {exp}")
        return float(a ** exp)
    else:
        raise ExecError(f"Operador desconhecido: {op}")


def executarExpressao(tokens, memoria, historico):
    """Avalia uma expressão RPN representada como lista de tokens.

    Percorre a lista de tokens usando uma pilha para acumular operandos
    e aplicar operadores. Suporta parênteses aninhados, variáveis de
    memória (store/load) e referências a resultados anteriores (RES).

    Args:
        tokens: Lista de dicts ``{"tipo": str, "valor": str}`` produzida
            por ``parseExpressao``.
        memoria: Dict ``{nome_var: float}`` com variáveis de memória.
            Modificado in-place quando há operação de store.
        historico: Dict ``{num_linha: float}`` com resultados de linhas
            anteriores, usado pelo comando ``RES``.

    Returns:
        Float com o resultado da expressão, ou ``None`` quando a
        expressão é um comando de armazenamento em memória.

    Raises:
        ExecError: Se houver erro semântico (operandos insuficientes,
            parênteses desbalanceados, índice RES inválido, etc.).
    """
    _MARCA = object()  # sentinela de ABRE_PAREN para controle de subexpressões

    pilha = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        tipo = tok["tipo"]
        valor = tok["valor"]

        if tipo == "ABRE_PAREN":
            pilha.append(_MARCA)

        elif tipo == "FECHA_PAREN":
            # O topo deve ser o resultado da subexpressão; marca logo abaixo
            if len(pilha) < 2:
                raise ExecError("Pilha malformada ao fechar parêntese")
            resultado_sub = pilha.pop()
            marca = pilha.pop()
            if marca is not _MARCA:
                raise ExecError("Parênteses desbalanceados na pilha")
            if not isinstance(resultado_sub, float):
                raise ExecError("Subexpressão sem resultado numérico")
            pilha.append(resultado_sub)

        elif tipo == "NUMERO":
            pilha.append(float(valor))

        elif tipo in ("OPERADOR", "OPERADOR_INT_DIV"):
            if len(pilha) < 2:
                raise ExecError(f"Operandos insuficientes para '{valor}'")
            b = pilha.pop()
            a = pilha.pop()
            if a is _MARCA or b is _MARCA:
                raise ExecError(f"Operação '{valor}' sobre marcador de parêntese")
            pilha.append(_aplicar_operador(valor, b, a))

        elif tipo == "KEYWORD_RES":
            if not pilha or pilha[-1] is _MARCA:
                raise ExecError("RES requer um número antes (ex: 1 RES)")
            indice = int(pilha.pop())
            if indice not in historico:
                raise ExecError(
                    f"RES {indice}: linha {indice} não possui resultado no histórico"
                )
            pilha.append(historico[indice])

        elif tipo == "MEM_ID":
            tem_valor = pilha and pilha[-1] is not _MARCA
            proximo_fecha = (i + 1 < n and tokens[i + 1]["tipo"] == "FECHA_PAREN") or (i + 1 >= n)
            if tem_valor and proximo_fecha:
                valor_mem = pilha.pop()
                memoria[valor] = valor_mem
                return None
            else:
                pilha.append(memoria.get(valor, 0.0))

        else:
            raise ExecError(f"Token desconhecido: {tipo} '{valor}'")

        i += 1

    if not pilha:
        raise ExecError("Pilha vazia ao fim da expressão")

    resultado = pilha[-1]
    if resultado is _MARCA:
        raise ExecError("Pilha malformada: marcador no topo ao fim")

    return resultado
