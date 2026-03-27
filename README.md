
# Interpretador RPN → Assembly ARMv7

GRUPO - **RA1 14**

Integrantes:

**Breno Ortiz David**, user: @BrenoOrtiz

**Vitor Coradin Ferreira**, user: @VitorCoradinFerreira

**Carlos Eduardo Ferreira Brandt**, user: @CaaduuuC

**João Ishikawa Onofrio**, user: @JoaoIshikawa

Projeto da disciplina de **Construcao de Interpretadores** (PUCPR) que implementa um pipeline completo de processamento de expressoes em **Notacao Polonesa Reversa (RPN)**:


1. **Analise Lexica** — Automato Finito Deterministico (AFD) implementado sem regex, reconhece numeros inteiros e decimais, operadores, identificadores de memoria e parenteses.
2. **Execucao** — Avaliador de expressoes RPN com pilha, suporte a 7 operacoes aritmeticas, variaveis de memoria e referencia a resultados anteriores (`RES`).
3. **Geracao de Codigo** — Traduz as expressoes para **Assembly ARMv7** com instrucoes **VFP .F64** (ponto flutuante de 64 bits, norma IEEE 754), compativel com a placa DE1-SoC no simulador CPUlator.


---

## Pre-requisitos

- **Python 3.10+** (utiliza apenas a biblioteca padrao; nao ha dependencias externas)

Para executar o assembly gerado:
- [CPUlator ARMv7 DE1-SoC](https://cpulator.01xz.net/?sys=arm-de1soc) (simulador online)

---

## Como Rodar

### Executar o interpretador

```bash
python main.py tests/teste1.txt
```

Arquivos de saida gerados em `output/`:
- `tokens_last_run.json` — tokens reconhecidos pelo analisador lexico
- `assembly_last_run.asm` — codigo Assembly ARMv7

### Executar os testes unitarios

```bash
# Todos os testes de uma vez
python -m unittest discover -s tests -p "test_*.py" -v

# Testes individuais
python -m unittest tests.test_lexer -v
python -m unittest tests.test_executor -v
python -m unittest tests.test_codegen -v
```

### Executar o assembly no CPUlator

1. Abra o CPUlator (ARMv7 DE1-SoC)
2. Cole o conteudo de `output/assembly_last_run.asm`
3. Compile e execute — os resultados serao impressos no terminal JTAG UART

---

## Diagrama de Estados do AFD

[Link para Diagrama](https://excalidraw.com/#json=30W3-zuSSFjBpbou5H_s7,Z0F_Bzyei0viubi6o_NYNA)

---

## Estrutura de Pastas

```
rpn-to-assembly/
│
├── main.py                  # Ponto de entrada do programa
├── lexer.py                 # Analisador léxico (AFD)
├── parser.py                # parseExpressao — extrai tokens por linha
├── executor.py              # executarExpressao — avalia expressões RPN com pilha
├── codegen.py               # gerarAssembly — traduz tokens para ARMv7
├── file_io.py               # lerArquivo — leitura do arquivo de entrada
├── display.py               # exibirResultados — formatação da saída
│
├── tests/
│   ├── test_lexer.py        # Testes unitários do analisador léxico (AFD)
│   ├── test_executor.py     # Testes da execução de expressões e memória
│   ├── test_codegen.py      # Testes da geração de Assembly
│   ├── test_display.py      # Testes da saída e integração do main
│   ├── teste1.txt           # Arquivo de teste 1 (≥10 expressões)
│   ├── teste2.txt           # Arquivo de teste 2 (≥10 expressões)
│   └── teste3.txt           # Arquivo de teste 3 (≥10 expressões)
│
├── output/
│   └── tokens_last_run.json # Tokens gerados na última execução do lexer
│   └── assembly_last_run.asm# Código Assembly da última execução
│
└── README.md                # Instruções de uso, equipe e disciplina
```

---

## Módulos e Funções

---

### `lexer.py` — Analisador Léxico com AFD

Implementa um Autômato Finito Determinístico (AFD) onde **cada estado é uma função Python**. Não utiliza expressões regulares. Reconhece os tokens válidos da linguagem RPN definida.

#### Estados do AFD (funções de estado)

---

##### `estado_inicial(char, buffer)`
- **Entrada:** caractere atual (`char`), buffer acumulado (`buffer`, sempre vazio neste estado)
- **Saída:** tupla `(proximo_estado, token_ou_None, buffer)` — próximo estado, token emitido (ou `None`) e buffer atualizado
- **Lógica:** Ponto de entrada do AFD. Roteia para o estado correto com base no primeiro caractere:
  - Dígito → `estado_numero`
  - Letra maiúscula → `estado_identificador`
  - `(` ou `)` → `estado_parentese` (emite token imediatamente)
  - Operador (`+`, `-`, `*`, `/`, `%`, `^`) → `estado_operador`
  - Espaço/tabulação → `estado_inicial` (ignora)
  - Qualquer outro → `estado_erro`

---

##### `estado_numero(char, buffer)`
- **Entrada:** caractere atual, buffer acumulado da leitura anterior
- **Saída:** `(proximo_estado, token_ou_None, buffer)`
- **Lógica:** Acumula dígitos e um único ponto decimal.
  - Dígito → permanece em `estado_numero`, acumula
  - `.` (primeiro) → transita para `estado_numero_decimal`
  - `.` (segundo) → levanta `LexerError` (número malformado, ex.: `3.14.5`)
  - Qualquer outro caractere (delimitador) → emite token `NUMERO` e reprocessa o caractere atual via estado `reprocessar`

---

##### `estado_numero_decimal(char, buffer)`
- **Entrada:** caractere atual, buffer com parte inteira + ponto + dígitos fracionários
- **Saída:** `(proximo_estado, token_ou_None, buffer)`
- **Lógica:** Acumula a parte fracionária do número.
  - Dígito → permanece em `estado_numero_decimal`
  - Segundo `.` → levanta `LexerError`
  - Qualquer outro caractere (delimitador) → emite token `NUMERO` e reprocessa o caractere atual via estado `reprocessar`

---

##### `estado_identificador(char, buffer)`
- **Entrada:** caractere atual, buffer de letras maiúsculas acumuladas
- **Saída:** `(proximo_estado, token_ou_None, buffer)`
- **Lógica:** Acumula letras maiúsculas para formar identificadores (`MEM`, `RES`, `VAR`, etc.).
  - Letra maiúscula → permanece, acumula
  - Outro caractere → classifica o buffer e reprocessa o caractere atual:
    - Se `RES` → emite token `KEYWORD_RES`
    - Caso contrário → emite token `MEM_ID`

---

##### `estado_operador(char, buffer)`
- **Entrada:** caractere atual, buffer (contém `/` quando aguardando segundo caractere)
- **Saída:** `(proximo_estado, token_ou_None, buffer)`
- **Lógica:** Reconhece operadores de um ou dois caracteres.
  - `+`, `-`, `*`, `%`, `^` → emite token `OPERADOR` imediatamente
  - `/` (primeiro) → permanece em `estado_operador` com buffer `/`, aguardando próximo caractere
  - Segundo caractere após `/`:
    - `/` → emite token `OPERADOR_INT_DIV` (valor `//`)
    - Outro → emite token `OPERADOR` (valor `/`) e reprocessa o caractere atual

---

##### `estado_parentese(char)`
- **Entrada:** `(` ou `)`
- **Saída:** token `ABRE_PAREN` ou `FECHA_PAREN`
- **Lógica:** Estado terminal simples; emite o token correspondente.

---

##### `estado_erro(char, buffer, pos)`
- **Entrada:** caractere inválido, buffer atual, posição na linha
- **Saída:** levanta `LexerError` com mensagem detalhada
- **Lógica:** Estado de absorção de erros. Registra posição e conteúdo do token malformado para diagnóstico.

---

#### `tokenizar(linha: str) -> list[dict]`
- **Entrada:** string com uma linha de expressão RPN
- **Saída:** lista de dicionários `[{"tipo": str, "valor": str}, ...]`
- **Lógica:** Percorre caractere por caractere, delegando ao estado atual do AFD. Ao fim, valida balanceamento de parênteses. Retorna lista de tokens ou levanta `LexerError`.

**Tipos de token emitidos:**

| Tipo            | Exemplo de valor |
|-----------------|-----------------|
| `ABRE_PAREN`    | `(`             |
| `FECHA_PAREN`   | `)`             |
| `NUMERO`        | `3.14`, `42`    |
| `OPERADOR`      | `+`, `-`, `*`, `/`, `%`, `^` |
| `OPERADOR_INT_DIV` | `//`         |
| `KEYWORD_RES`   | `RES`           |
| `MEM_ID`        | `MEM`, `VAR`, `X` |

---

### `parser.py` — Extração de Tokens por Linha

#### `parseExpressao(linha: str, tokens: list) -> list[dict]`
- **Entrada:** `linha` — string com uma expressão RPN; `tokens` — lista mutável a ser preenchida
- **Saída:** lista de tokens (mesma referência de `tokens`, também retornada)
- **Lógica:**
  1. Chama `tokenizar(linha)` do módulo `lexer.py`
  2. Valida estrutura mínima (pelo menos um par de parênteses e um operador ou comando)
  3. Preenche `tokens` in-place e retorna a lista
  4. Em caso de erro léxico, registra a linha como inválida e retorna lista vazia

---

### `executor.py` — Avaliação de Expressões RPN

#### `executarExpressao(tokens: list[dict], memoria: dict, historico: dict) -> float | None`
- **Entrada:**
  - `tokens` — lista de tokens produzida por `parseExpressao`
  - `memoria` — dicionário `{nome_mem: float}` com variáveis de memória e seus valores
  - `historico` — dicionário `{num_linha: float}` com resultados de linhas anteriores para referência `RES`
- **Saída:** `float` com o resultado da expressão, ou `None` para comandos de armazenamento em memória
- **Lógica:**
  1. Utiliza uma pilha para avaliar a expressão RPN, tratando parênteses como delimitadores de subexpressões:
     - `ABRE_PAREN` → empilha um marcador de início de subexpressão
     - `FECHA_PAREN` → finaliza a subexpressão atual; o resultado parcial da subexpressão é empilhado de volta como operando
     - `NUMERO` → converte para `float` e empilha como operando
     - `OPERADOR` / `OPERADOR_INT_DIV` → desempilha dois operandos, aplica a operação e empilha o resultado
     - `KEYWORD_RES` → desempilha o número anterior como índice (chave) no `historico`; empilha o valor correspondente
     - `MEM_ID` seguido de valor → armazena o valor em `memoria` sob o identificador; retorna `None`
     - `MEM_ID` sozinho → busca o valor em `memoria` e empilha (retorna `0.0` se não inicializado)
  2. Ao final, o topo da pilha contém o resultado da expressão
  3. Lança `ExecError` em caso de erro (divisão por zero, índice `RES` fora do intervalo, pilha mal formada, etc.)

| Operador | Operação                   |
|----------|----------------------------|
| `+`      | Adição                     |
| `-`      | Subtração                  |
| `*`      | Multiplicação              |
| `/`      | Divisão real               |
| `//`     | Divisão inteira (trunca)   |
| `%`      | Resto da divisão inteira   |
| `^`      | Potenciação (B inteiro ≥ 0)|

---

### `file_io.py` — Leitura do Arquivo de Entrada

#### `lerArquivo(nome_arquivo: str, linhas: list) -> list[str]`
- **Entrada:** `nome_arquivo` — caminho do arquivo `.txt`; `linhas` — lista mutável a ser preenchida
- **Saída:** lista de strings, uma por linha do arquivo (sem `\n`)
- **Lógica:**
  1. Tenta abrir o arquivo com `open(nome_arquivo, 'r', encoding='utf-8')`
  2. Lê todas as linhas, remove espaços e linhas em branco
  3. Preenche `linhas` in-place e retorna
  4. Em caso de `FileNotFoundError` ou `PermissionError`, exibe mensagem de erro clara e encerra com `sys.exit(1)`

---

### `codegen.py` — Geração de Código Assembly ARMv7

#### `gerarAssembly(lista_tokens: list, codigo_assembly: list) -> str`
- **Entrada:**
  - `lista_tokens` — lista onde cada elemento é uma lista de tokens (dicts `{"tipo": str, "valor": str}`) ou a string `"ERRO_LEXICO"` para linhas com erro léxico
  - `codigo_assembly` — lista mutável onde o bloco assembly final será adicionado como string única
- **Saída:** string com o programa Assembly completo (seções `.data` e `.text`)
- **Lógica:**
  1. Percorre todas as expressões e traduz cada operação RPN para instruções ARMv7:
     - Números são carregados via `VLDR` para registradores VFP de 64 bits (`D0`, `D1`, etc.)
     - Operações usam instruções VFP (`VADD.F64`, `VSUB.F64`, `VMUL.F64`, `VDIV.F64`) para float64
     - Divisão inteira e resto usam `VDIV.F64` + `VCVT.S32.F64` / `VCVT.F64.S32` (truncamento via VFP)
     - Potenciação gera loop com `VMUL.F64`
     - Comandos `MEM` mapeiam para endereços de memória definidos na seção `.data`
     - Resultados são impressos via JTAG UART (`0xFF201000`) com sub-rotinas `uart_char`, `uart_int` e `uart_float`
  2. Inclui cabeçalho `.global _start`, inicialização da FPU, seção `.data` e seção `.text`
  3. Gera um único bloco Assembly com todas as expressões, sub-rotinas de impressão e dados

---

### `display.py` — Exibição de Resultados

#### `exibirResultados(resultados: list) -> None`
- **Entrada:** lista de valores retornados por `executarExpressao` (`float` ou `None`), um por linha do arquivo de entrada
- **Saída:** nenhum valor de retorno; imprime no `stdout`
- **Lógica:**
  1. Percorre `resultados` com índice
  2. Para cada resultado:
     - `float` → exibe o valor numérico (ex.: `3.1`)
     - `None` → exibe `"(sem retorno)"` para comandos de armazenamento em memória
     - Exceção capturada → exibe `"ERRO"` na linha correspondente
  3. Formato de saída: `Linha N: <resultado>`

---

### `main.py` — Ponto de Entrada

#### `main()`
- **Entrada:** argumento de linha de comando `sys.argv[1]` (nome do arquivo de teste)
- **Saída:** código Assembly gerado em `output/assembly_last_run.asm` + tokens em `output/tokens_last_run.json` + resultados no `stdout`
- **Lógica (fluxo completo):**

```
1. Valida sys.argv (exige exatamente 1 argumento)
2. lerArquivo(arquivo, linhas)
3. Para cada linha em linhas:
   a. parseExpressao(linha, tokens)        → extrai tokens via AFD
      - Se LexerError: registra "Erro lexico", acumula "ERRO_LEXICO" e pula para próxima linha
      - Se tokens vazio (expressão sem parênteses/operador): registra None e pula
   b. executarExpressao(tokens, mem, hist) → avalia expressão RPN, retorna float|None
      - Se resultado não-None: salva em historico[num_linha]
   c. Acumula tokens em todas_tokens
4. gerarAssembly(todas_tokens, asm_buffer) → gera bloco Assembly único com todas as expressões
5. Salva tokens em output/tokens_last_run.json
6. Salva Assembly em output/assembly_last_run.asm
7. exibirResultados(resultados)

```

---

## Fluxo de Dados

```
arquivo.txt
    │
    ▼
lerArquivo()
    │  lista de linhas (str)
    ▼
┌─ Para cada linha: ──────────────────────┐
│  parseExpressao()  ←→  tokenizar() [AFD]│
│      │  lista de tokens (dict)          │
│      ▼                                  │
│  executarExpressao()                    │
│    (avalia com pilha,                   │
│     trata parênteses)                   │
│      │  float | None | str              │
│      ▼                                  │
│  acumula tokens em todas_tokens         │
│  acumula resultado em resultados        │
└─────────────────────────────────────────┘
    │
    ├── todas_tokens ──► gerarAssembly()
    │                        │  str (ARMv7)
    │                        ▼
    │                   assembly_last_run.asm
    │
    ├── resultados ───► exibirResultados()
    │                        │
    │                     stdout
    │
    └── tokens_json ──► tokens_last_run.json
```

---

## Formato do Arquivo de Tokens (`tokens_last_run.json`)

```json
[
  {
    "linha": 1,
    "expressao": "(3.14 2.0 +)",
    "tokens": [
      {"tipo": "ABRE_PAREN", "valor": "("},
      {"tipo": "NUMERO",     "valor": "3.14"},
      {"tipo": "NUMERO",     "valor": "2.0"},
      {"tipo": "OPERADOR",   "valor": "+"},
      {"tipo": "FECHA_PAREN","valor": ")"}
    ]
  }
]
```

---

## Tratamento de Erros

| Situação                            | Módulo responsável | Comportamento                                        |
|-------------------------------------|--------------------|------------------------------------------------------|
| Número malformado (`3.14.5`)        | `lexer.py`         | `LexerError` com posição; linha marcada como inválida |
| Operador inválido (`&`, `@`)        | `lexer.py`         | `LexerError`; linha ignorada                         |
| Parênteses desbalanceados           | `lexer.py`         | `LexerError` ao fim da tokenização                   |
| Divisão por zero                    | `executor.py`      | `ExecError`; resultado `None`, aviso impresso        |
| `(N RES)` com N fora do histórico   | `executor.py`      | `ExecError`; resultado `None`                        |
| `(MEM)` não inicializada            | `executor.py`      | Retorna `0.0` conforme especificação                 |
| Arquivo não encontrado              | `file_io.py`       | Mensagem de erro + `sys.exit(1)`                     |

---

## Execução

```bash
python main.py tests/teste1.txt
```
