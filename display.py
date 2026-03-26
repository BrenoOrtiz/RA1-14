def exibirResultados(resultados: list) -> None:
    """
    Exibe os resultados das expressões RPN avaliadas.

    Parâmetros:
        resultados: lista de valores retornados por executarExpressao
                    (float, None ou Exception por linha)
    """
    for i, resultado in enumerate(resultados, start=1):
        if isinstance(resultado, Exception):
            print(f"Linha {i}: ERRO")
        elif resultado is None:
            print(f"Linha {i}: (sem retorno)")
        else:
            print(f"Linha {i}: {resultado}")