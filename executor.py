class ExecError(Exception):
    pass


def _aplicar_operador(op, b, a):
    """Aplica operador binário: a op b (a foi empilhado antes de b)."""
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
    """
    Avalia uma expressão RPN representada como lista de tokens.

    Parâmetros:
        tokens   -- lista de dicts {"tipo": str, "valor": str} produzida por parseExpressao
        memoria  -- dict {nome_mem: float} com variáveis de memória (modificado in-place)
        historico -- lista de floats com resultados anteriores (para KEYWORD_RES)

    Retorna:
        float com o resultado da expressão, ou
        None  para comandos de armazenamento em memória (MEM_ID seguido de valor)

    Lança ExecError em caso de erro semântico.
    """
    # Pilha principal; cada entrada é um float ou o marcador de subexpressão
    _MARCA = object()  # sentinela de ABRE_PAREN

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
            # Não permite operar sobre marcadores
            if a is _MARCA or b is _MARCA:
                raise ExecError(f"Operação '{valor}' sobre marcador de parêntese")
            pilha.append(_aplicar_operador(valor, b, a))

        elif tipo == "KEYWORD_RES":
            # O índice da linha vem ANTES (já na pilha)
            if not pilha or pilha[-1] is _MARCA:
                raise ExecError("RES requer um número antes (ex: 1 RES)")
            indice = int(pilha.pop())
            if indice not in historico:
                raise ExecError(
                    f"RES {indice}: linha {indice} não possui resultado no histórico"
                )
            pilha.append(historico[indice])

        elif tipo == "MEM_ID":
            # Store: valor já na pilha + próximo token é FECHA_PAREN ou fim
            tem_valor = pilha and pilha[-1] is not _MARCA
            proximo_fecha = (i + 1 < n and tokens[i + 1]["tipo"] == "FECHA_PAREN") or (i + 1 >= n)
            if tem_valor and proximo_fecha:
                valor_mem = pilha.pop()
                memoria[valor] = valor_mem
                return None
            else:
                # Load: empilha valor da memória
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
