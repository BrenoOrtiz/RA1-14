def exibirResultados(resultados: list) -> None:
    """Exibe os resultados das expressões RPN no console.

    Percorre a lista de resultados e imprime cada um formatado
    com o número da linha. Trata os diferentes tipos de resultado:
    valores numéricos, erros léxicos, erros de execução e linhas
    sem retorno (store em memória).

    Args:
        resultados: Lista de valores retornados pelo pipeline de
            execução. Cada elemento pode ser ``float`` (resultado
            numérico), ``str`` (mensagem de erro léxico), ``None``
            (operação de store) ou ``Exception`` (erro de execução).
    """
    for i, resultado in enumerate(resultados, start=1):
        if isinstance(resultado, Exception):
            print(f"Linha {i}: ERRO")
        elif resultado is None:
            print(f"Linha {i}: (sem retorno)")
        else:
            print(f"Linha {i}: {resultado}")