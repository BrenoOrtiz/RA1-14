
# Documentação do Projeto: Interpretador RPN → Assembly ARMv7

---

# Diagrama de Estados do AFD

[https://excalidraw.com/#json=30W3-zuSSFjBpbou5H_s7,Z0F_Bzyei0viubi6o_NYNA](Link para Diagrama)

## Estrutura de Pastas

```
rpn-to-assembly/
│
├── main.py                  # Ponto de entrada do programa
├── lexer.py                 # Analisador léxico (AFD)
├── parser.py                # parseExpressao — extrai tokens por linha
├── executor.py              # executarExpressao — avalia expressões RPN
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

##### `estado_inicial(char, pos, linha)`
- **Entrada:** caractere atual (`char`), posição (`pos`), linha completa (`linha`)
- **Saída:** tupla `(proximo_estado, token_parcial)` — próximo estado e buffer acumulado
- **Lógica:** Ponto de entrada do AFD. Roteia para o estado correto com base no primeiro caractere:
  - Dígito ou `-`/`+` seguido de dígito → `estado_numero`
  - Letra maiúscula → `estado_identificador`
  - `(` ou `)` → `estado_parentese`
  - Operador (`+`, `-`, `*`, `/`, `%`, `^`) → `estado_operador`
  - Espaço/tabulação → `estado_inicial` (ignora)
  - Qualquer outro → `estado_erro`

---

##### `estado_numero(char, buffer)`
- **Entrada:** caractere atual, buffer acumulado da leitura anterior
- **Saída:** `(proximo_estado, buffer_atualizado)`
- **Lógica:** Acumula dígitos e um único ponto decimal.
  - Dígito → permanece em `estado_numero`, acumula
  - `.` (primeiro) → transita para `estado_numero_decimal`
  - `.` (segundo) → transita para `estado_erro` (número malformado, ex.: `3.14.5`)
  - Espaço, `)` ou EOF → emite token do tipo `NUMERO`, retorna ao `estado_inicial`

---

##### `estado_numero_decimal(char, buffer)`
- **Entrada:** caractere atual, buffer com parte inteira + ponto
- **Saída:** `(proximo_estado, buffer_atualizado)`
- **Lógica:** Acumula a parte fracionária do número.
  - Dígito → permanece em `estado_numero_decimal`
  - Qualquer não-dígito → emite token `NUMERO`, transita ao estado adequado
  - Segundo `.` → `estado_erro`

---

##### `estado_identificador(char, buffer)`
- **Entrada:** caractere atual (letra maiúscula), buffer
- **Saída:** `(proximo_estado, buffer_atualizado)`
- **Lógica:** Acumula letras maiúsculas para formar identificadores (`MEM`, `RES`, `VAR`, etc.).
  - Letra maiúscula → permanece, acumula
  - Outro caractere → verifica se buffer é `RES` (keyword) ou identificador de memória
    - Se `RES` → emite token `KEYWORD_RES`
    - Caso contrário → emite token `MEM_ID`

---

##### `estado_operador(char, buffer)`
- **Entrada:** caractere atual (operador)
- **Saída:** `(estado_inicial, token)`
- **Lógica:** Reconhece operadores de um ou dois caracteres.
  - `+`, `-`, `*`, `%`, `^` → emite token `OPERADOR` imediatamente
  - `/` → verifica próximo caractere:
    - `//` → emite token `OPERADOR_INT_DIV`
    - `/` sozinho → emite token `OPERADOR`

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

### `executor.py` — Validação Estrutural de Expressões RPN

> **Importante:** nenhum cálculo aritmético é realizado por este módulo nem por qualquer outro código Python. Toda computação numérica ocorre exclusivamente na execução do código Assembly gerado (ex.: CPulator).

#### `executarExpressao(tokens: list[dict], memoria: dict, historico: list) -> None`
- **Entrada:**
  - `tokens` — lista de tokens produzida por `parseExpressao`
  - `memoria` — dicionário `{nome_mem: str}` com identificadores de memória declarados
  - `historico` — lista de rótulos/etiquetas de resultados anteriores para referência `RES`
- **Saída:** `None` — não retorna valor numérico; apenas valida a estrutura da expressão
- **Lógica:**
  1. Percorre os tokens para verificar a estrutura RPN sem avaliá-la numericamente:
     - `NUMERO` → registra presença de operando
     - `OPERADOR` / `OPERADOR_INT_DIV` → verifica se há operandos suficientes na pilha simbólica
     - `KEYWORD_RES` com N → verifica se N está dentro do histórico de etiquetas disponíveis
     - `MEM_ID` seguido de valor → registra declaração de variável de memória
     - `MEM_ID` sozinho → verifica se identificador foi declarado anteriormente
  2. Lança `ExecError` em caso de estrutura inválida (pilha simbólica mal formada, índice `RES` fora do intervalo ou identificador de memória não declarado)

**Nota:** os valores reais das operações abaixo são computados integralmente pelo Assembly ARMv7 gerado:

| Operador | Operação                   | Tipo Assembly |
|----------|----------------------------|---------------|
| `+`      | Adição                     | `VADD.F64`    |
| `-`      | Subtração                  | `VSUB.F64`    |
| `*`      | Multiplicação              | `VMUL.F64`    |
| `/`      | Divisão real               | `VDIV.F64`    |
| `//`     | Divisão inteira            | `SDIV`        |
| `%`      | Resto da divisão inteira   | `SDIV` + `MLS`|
| `^`      | Potenciação (B inteiro ≥ 0)| loop `VMUL.F64`|

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

#### `gerarAssembly(tokens: list[dict], codigo_assembly: list) -> str`
- **Entrada:**
  - `tokens` — lista de tokens de uma expressão
  - `codigo_assembly` — lista acumuladora de linhas Assembly (modificada in-place)
- **Saída:** string com o bloco de código Assembly gerado para aquela expressão
- **Lógica:**
  1. Percorre os tokens e traduz cada operação RPN para instruções ARMv7:
     - Números são carregados via `VLDR` / `MOV` para registradores de ponto flutuante (`S0`, `S1`, etc.) ou inteiros (`R0`, `R1`)
     - Operações usam instruções VFP (`VADD.F64`, `VSUB.F64`, `VMUL.F64`, `VDIV.F64`) para float64
     - Divisão inteira e resto usam `SDIV` e sequência `MLS`
     - Potenciação gera loop com `VMUL.F64`
     - Comandos `MEM` mapeiam para endereços de memória definidos na seção `.data`
     - Resultados são enviados para o display HEX do Cpulator via endereço mapeado de I/O (`0xFF200020`)
  2. Inclui cabeçalho `.global _start`, seção `.data` e seção `.text`
  3. Acumula todo o Assembly gerado no arquivo `output/assembly_last_run.asm`

---

### `display.py` — Exibição de Resultados

#### `exibirResultados(resultados: list) -> None`
- **Entrada:** lista de strings com os resultados lidos da saída da execução Assembly, um por linha do arquivo de entrada
- **Saída:** nenhum valor de retorno; imprime no `stdout`
- **Lógica:**
  1. Percorre `resultados` com índice
  2. Para cada resultado obtido da execução do Assembly:
     - Valor numérico → exibe o resultado conforme retornado pelo Assembly (ex.: `3.1`)
     - `None` / ausente → exibe `"(sem retorno)"` para comandos de armazenamento em memória
     - Exceção capturada → exibe `"ERRO"` na linha correspondente
  3. Formato de saída: `Linha N: <resultado>`
- **Nota:** nenhum cálculo é realizado neste módulo; os valores exibidos são exclusivamente os resultados produzidos pela execução do código Assembly gerado

---

### `main.py` — Ponto de Entrada

#### `main()`
- **Entrada:** argumento de linha de comando `sys.argv[1]` (nome do arquivo de teste)
- **Saída:** código Assembly gerado em `output/assembly_last_run.asm` + tokens em `output/tokens_last_run.json`; os resultados numéricos são obtidos executando o Assembly gerado (ex.: CPulator)
- **Lógica (fluxo completo):**

```
1. Valida sys.argv (exige exatamente 1 argumento)
2. lerArquivo(arquivo, linhas)
3. Para cada linha em linhas:
   a. parseExpressao(linha, tokens)        → extrai tokens via AFD
   b. executarExpressao(tokens, mem, hist) → valida estrutura RPN (sem cálculo)
   c. gerarAssembly(tokens, asm_buffer)    → acumula código Assembly ARMv7
4. Salva tokens em output/tokens_last_run.json
5. Salva Assembly em output/assembly_last_run.asm
6. [Fora do Python] Executa o Assembly gerado no CPulator → obtém resultados
7. exibirResultados(resultados_do_assembly)

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
parseExpressao()  ←→  tokenizar() [AFD]
    │  lista de tokens (dict)
    ├──────────────────────────────────────────────┐
    ▼                                              ▼
executarExpressao()                         gerarAssembly()
  (valida estrutura,                               │  str (ARMv7)
   SEM cálculo)                                    ▼
                                      assembly_last_run.asm
                                                   │
                                     [execução no CPulator]
                                                   │  resultados numéricos
                                                   ▼
                                        exibirResultados()
                                                   │
                                                stdout

NOTA: nenhum valor numérico é calculado pelo Python.
      O cálculo ocorre exclusivamente na execução do Assembly.
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

Saída esperada no terminal:
```
Linha 1: 5.1
Linha 2: 12.0
Linha 3: (sem retorno)
...
```