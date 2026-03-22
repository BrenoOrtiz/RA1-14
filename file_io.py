import sys

def lerArquivo(nome_arquivo: str, linhas: list) -> list[str]:
    """Abre o arquivo, lê todas as linhas, remove espaços e linhas vazias, preenche a lista e retorna"""
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