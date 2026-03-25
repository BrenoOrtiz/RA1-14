import sys
import json
import os
 
from file_io import lerArquivo
from parser import parseExpressao
from executor import executarExpressao
from codegen import gerarAssembly
from display import exibirResultados
 
 
def main():
    """
    Ponto de entrada do programa. Valida os argumentos de linha de comando,
    coordena a leitura do arquivo, tokenização, execução, geração de Assembly
    e exibição dos resultados. Salva os tokens em JSON e o Assembly em .asm
    na pasta output/.
    """
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo_de_entrada.txt>")
        sys.exit(1)
 
    nome_arquivo = sys.argv[1]
 
    linhas = []
    resultados = []
    memoria = {}
    historico = []
    asm_buffer = []
    tokens_json = []
 
    lerArquivo(nome_arquivo, linhas)
 
    for i, linha in enumerate(linhas, start=1):
        tokens = []
 
        parseExpressao(linha, tokens)
 
        if not tokens:
            resultados.append(None)
            tokens_json.append({
                "linha": i,
                "expressao": linha,
                "tokens": []
            })
            continue
 
        tokens_json.append({
            "linha": i,
            "expressao": linha,
            "tokens": tokens
        })
        
        continue
    
    tokens_json.append({
        "linha": i,
        "expressao": linha,
        "tokens": tokens
    })

    try:
        resultado = executarExpressao(tokens, memoria, historico)
        resultados.append(resultado)

        if resultado is not None:
            historico.append(resultado)

    except Exception as e:
        print(f"[ERRO executor] Linha {i}: {e}", file=sys.stderr)
        resultados.append(Exception(str(e)))

    try:
        gerarAssembly(tokens, asm_buffer)
    except Exception as e:
        print(f"[ERRO codegen] Linha {i}: {e}", file=sys.stderr)        