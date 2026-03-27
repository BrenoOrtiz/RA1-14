import sys

def lerArquivo(nome_arquivo: str, linhas: list) -> list[str]:
    """Lê um arquivo texto e extrai suas linhas não vazias.

    Abre o arquivo, remove espaços em branco das extremidades de cada
    linha e descarta linhas vazias. Encerra o programa com mensagem
    de erro se o arquivo não for encontrado ou não houver permissão.

    Args:
        nome_arquivo: Caminho do arquivo a ser lido.
        linhas: Lista mutável que será preenchida com as linhas
            processadas.

    Returns:
        Mesma referência de ``linhas``, preenchida com as linhas
        não vazias do arquivo.
    """
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.readlines()

        for linha in conteudo:
            linha_limpa = linha.strip()
            if linha_limpa:
                linhas.append(linha_limpa)

        return linhas

    except FileNotFoundError:
        print(f"Erro: arquivo '{nome_arquivo}' não encontrado.")
        sys.exit(1)

    except PermissionError:
        print(f"Erro: sem permissão para ler o arquivo '{nome_arquivo}'.")
        sys.exit(1)