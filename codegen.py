# Endereço do JTAG UART do CPUlator (DE1-SoC)
_JTAG_UART_ADDR = 0xFF201000

class CodegenError(Exception):
    """Exceção para erros durante a geração de código assembly."""
    pass


def gerarAssembly(lista_tokens, codigo_assembly):
    """Traduz expressões RPN para um programa ARMv7 VFP assembly.

    Gera um único bloco assembly com seções ``.data`` e ``.text``,
    incluindo inicialização da FPU, instruções de cada expressão,
    saída via JTAG UART e sub-rotinas de impressão.

    Args:
        lista_tokens: Lista onde cada elemento é uma lista de tokens
            (dicts ``{"tipo": str, "valor": str}``) ou a string
            ``"ERRO_LEXICO"`` para linhas com erro léxico.
        codigo_assembly: Lista mutável onde o bloco assembly final
            será adicionado como string única.

    Returns:
        String com o programa assembly completo.

    Raises:
        CodegenError: Se houver operandos insuficientes, índice RES
            indeterminado ou outros erros de geração.
    """
    mem_labels = {}   # MEM_ID -> label na seção .data
    literais = {}     # valor float -> label na seção .data
    res_indices = set()  # índices RES usados
    reg_counter = [0]

    def prox_reg():
        """Aloca e retorna o próximo registrador D (64-bit).

        Returns:
            String no formato ``D<n>`` para uso em instruções VFP ``.F64``.
        """
        r = f"D{reg_counter[0]}"
        reg_counter[0] += 1
        return r

    def label_literal(val_str):
        """Obtém ou cria o label ``.data`` para um literal numérico.

        Args:
            val_str: Valor numérico como string (ex: ``"3.14"``).

        Returns:
            Nome do label no formato ``lit_<n>``.
        """
        if val_str not in literais:
            literais[val_str] = f"lit_{len(literais)}"
        return literais[val_str]

    def label_mem(nome):
        """Obtém ou cria o label ``.data`` para uma variável de memória.

        Args:
            nome: Nome da variável em maiúsculas (ex: ``"MA"``).

        Returns:
            Nome do label no formato ``mem_<nome_lower>``.
        """
        if nome not in mem_labels:
            mem_labels[nome] = f"mem_{nome.lower()}"
        return mem_labels[nome]

    instrucoes = []

    for num_linha, tokens in enumerate(lista_tokens, start=1):
        instrucoes.append(f"    @ ===== Linha {num_linha} =====")

        if tokens == "ERRO_LEXICO":
            instrucoes.append(f"    @ Erro lexico - imprime mensagem")
            instrucoes.append(f"    MOV      R0, #76")
            instrucoes.append(f"    BL       uart_char")
            instrucoes.append(f"    MOV      R0, #{num_linha}")
            instrucoes.append(f"    BL       uart_int")
            instrucoes.append(f"    MOV      R0, #61")
            instrucoes.append(f"    BL       uart_char")
            instrucoes.append(f"    MOV      R0, #32")
            instrucoes.append(f"    BL       uart_char")
            for ch in "Erro lexico":
                instrucoes.append(f"    MOV      R0, #{ord(ch)}")
                instrucoes.append(f"    BL       uart_char")
            instrucoes.append(f"    MOV      R0, #10")
            instrucoes.append(f"    BL       uart_char")
            continue

        pilha = []
        reg_counter[0] = 0

        i = 0
        while i < len(tokens):
            token = tokens[i]
            tipo = token["tipo"]
            valor = token["valor"]

            if tipo == "ABRE_PAREN":
                pilha.append(None)
                i += 1

            elif tipo == "FECHA_PAREN":
                if None in pilha:
                    idx = len(pilha) - 1 - pilha[::-1].index(None)
                    pilha.pop(idx)
                i += 1

            elif tipo == "NUMERO":
                lbl = label_literal(valor)
                reg = prox_reg()
                instrucoes.append(f"    @ carrega {valor} em {reg}")
                instrucoes.append(f"    LDR     R0, ={lbl}")
                instrucoes.append(f"    VLDR    {reg}, [R0]")
                pilha.append(reg)
                i += 1

            elif tipo in ("OPERADOR", "OPERADOR_INT_DIV"):
                if len([r for r in pilha if r is not None]) < 2:
                    raise CodegenError(f"Operandos insuficientes para '{valor}'")

                reg_b = pilha.pop()
                reg_a = pilha.pop()
                reg_r = prox_reg()

                instrucoes.append(f"    @ {reg_a} {valor} {reg_b} -> {reg_r}")

                if valor == '+':
                    instrucoes.append(f"    VADD.F64 {reg_r}, {reg_a}, {reg_b}")
                elif valor == '-':
                    instrucoes.append(f"    VSUB.F64 {reg_r}, {reg_a}, {reg_b}")
                elif valor == '*':
                    instrucoes.append(f"    VMUL.F64 {reg_r}, {reg_a}, {reg_b}")
                elif valor == '/':
                    instrucoes.append(f"    VDIV.F64 {reg_r}, {reg_a}, {reg_b}")
                elif valor == '//':
                    # Divisão inteira via VFP: divide como float, trunca para int
                    reg_div = prox_reg()
                    reg_scratch = prox_reg()
                    s_scratch = f"S{int(reg_scratch[1:]) * 2}"
                    instrucoes.append(f"    VDIV.F64 {reg_div}, {reg_a}, {reg_b}")
                    instrucoes.append(f"    VCVT.S32.F64 {s_scratch}, {reg_div}")
                    instrucoes.append(f"    VCVT.F64.S32 {reg_r}, {s_scratch}")
                elif valor == '%':
                    # Resto: a - (a // b) * b, tudo via VFP
                    reg_div = prox_reg()
                    reg_trunc = prox_reg()
                    reg_mul = prox_reg()
                    reg_scratch = prox_reg()
                    s_scratch = f"S{int(reg_scratch[1:]) * 2}"
                    instrucoes.append(f"    VDIV.F64 {reg_div}, {reg_a}, {reg_b}")
                    instrucoes.append(f"    VCVT.S32.F64 {s_scratch}, {reg_div}")
                    instrucoes.append(f"    VCVT.F64.S32 {reg_trunc}, {s_scratch}")
                    instrucoes.append(f"    VMUL.F64 {reg_mul}, {reg_trunc}, {reg_b}")
                    instrucoes.append(f"    VSUB.F64 {reg_r}, {reg_a}, {reg_mul}")
                elif valor == '^':
                    lbl_loop = f"pow_loop_L{num_linha}_{reg_r}"
                    lbl_end = f"pow_end_L{num_linha}_{reg_r}"
                    reg_um = prox_reg()
                    reg_scratch = prox_reg()
                    s_scratch = f"S{int(reg_scratch[1:]) * 2}"
                    instrucoes.append(f"    VCVT.S32.F64 {s_scratch}, {reg_b}")
                    instrucoes.append(f"    VMOV     R2, {s_scratch}")
                    instrucoes.append(f"    MOV      R3, #1")
                    instrucoes.append(f"    VMOV     {s_scratch}, R3")
                    instrucoes.append(f"    VCVT.F64.S32 {reg_um}, {s_scratch}")
                    instrucoes.append(f"{lbl_loop}:")
                    instrucoes.append(f"    CMP      R2, #0")
                    instrucoes.append(f"    BLE      {lbl_end}")
                    instrucoes.append(f"    VMUL.F64 {reg_um}, {reg_um}, {reg_a}")
                    instrucoes.append(f"    SUB      R2, R2, #1")
                    instrucoes.append(f"    B        {lbl_loop}")
                    instrucoes.append(f"{lbl_end}:")
                    instrucoes.append(f"    VMOV.F64 {reg_r}, {reg_um}")

                pilha.append(reg_r)
                i += 1

            elif tipo == "KEYWORD_RES":
                if not pilha or pilha[-1] is None:
                    raise CodegenError("RES requer um número antes (ex: 1 RES)")
                reg_idx = pilha.pop()
                idx = None
                for t in reversed(tokens[:i]):
                    if t["tipo"] == "NUMERO":
                        idx = int(float(t["valor"]))
                        break
                if idx is None:
                    raise CodegenError("Não foi possível determinar o índice de RES")
                res_indices.add(idx)
                reg = prox_reg()
                instrucoes.append(f"    @ carrega RES[{idx}] em {reg}")
                instrucoes.append(f"    LDR     R0, =res_hist_{idx}")
                instrucoes.append(f"    VLDR    {reg}, [R0]")
                pilha.append(reg)
                i += 1

            elif tipo == "MEM_ID":
                tem_valor = pilha and pilha[-1] is not None
                proximo_fecha = (i + 1 < len(tokens) and tokens[i+1]["tipo"] == "FECHA_PAREN") or (i + 1 >= len(tokens))
                if tem_valor and proximo_fecha:
                    reg_src = pilha.pop()
                    lbl = label_mem(valor)
                    instrucoes.append(f"    @ armazena {reg_src} em {valor}")
                    instrucoes.append(f"    LDR     R0, ={lbl}")
                    instrucoes.append(f"    VSTR    {reg_src}, [R0]")
                    i += 1
                else:
                    lbl = label_mem(valor)
                    reg = prox_reg()
                    instrucoes.append(f"    @ lê {valor} -> {reg}")
                    instrucoes.append(f"    LDR     R0, ={lbl}")
                    instrucoes.append(f"    VLDR    {reg}, [R0]")
                    pilha.append(reg)
                    i += 1
            else:
                i += 1

        # Salva resultado no histórico RES e imprime no terminal JTAG UART
        if pilha and pilha[-1] is not None:
            reg_res = pilha[-1]
            res_indices.add(num_linha)
            instrucoes.append(f"    @ salva resultado em res_hist_{num_linha}")
            instrucoes.append(f"    LDR     R0, =res_hist_{num_linha}")
            instrucoes.append(f"    VSTR    {reg_res}, [R0]")
            instrucoes.append(f"    @ imprime 'L<num>= ' no terminal")
            instrucoes.append(f"    MOV      R0, #76")
            instrucoes.append(f"    BL       uart_char")
            instrucoes.append(f"    MOV      R0, #{num_linha}")
            instrucoes.append(f"    BL       uart_int")
            instrucoes.append(f"    MOV      R0, #61")
            instrucoes.append(f"    BL       uart_char")
            instrucoes.append(f"    MOV      R0, #32")
            instrucoes.append(f"    BL       uart_char")
            instrucoes.append(f"    @ imprime resultado como float")
            instrucoes.append(f"    VMOV.F64 D0, {reg_res}")
            instrucoes.append(f"    BL       uart_float")
            instrucoes.append(f"    MOV      R0, #10")
            instrucoes.append(f"    BL       uart_char")

    # --- Montagem do Bloco Final (único) ---
    secao_data = [".data", ".align 3"]
    for val_str, lbl in literais.items():
        secao_data.append(f"{lbl}:  .double {val_str}")
    for nome, lbl in mem_labels.items():
        secao_data.append(f"{lbl}:  .double 0.0")
    for idx in sorted(res_indices):
        secao_data.append(f"res_hist_{idx}:  .double 0.0")

    subrotinas = [
        "",
        "@ ========== Sub-rotinas JTAG UART ==========",
        "",
        "@ uart_char: imprime caractere em R0",
        "uart_char:",
        "    PUSH    {R1, R2, LR}",
        f"    LDR     R1, =0x{_JTAG_UART_ADDR:08X}",
        "uart_char_wait:",
        "    LDR     R2, [R1, #4]",
        "    LSR     R2, R2, #16",
        "    CMP     R2, #0",
        "    BEQ     uart_char_wait",
        "    STR     R0, [R1]",
        "    POP     {R1, R2, PC}",
        "",
        "@ uart_int: imprime inteiro em R0 (com sinal)",
        "uart_int:",
        "    PUSH    {R0-R5, LR}",
        "    MOV     R4, R0",
        "    CMP     R4, #0",
        "    BGE     ui_pos",
        "    MOV     R0, #45",
        "    BL      uart_char",
        "    RSB     R4, R4, #0",
        "ui_pos:",
        "    MOV     R5, #0",
        "    CMP     R4, #0",
        "    BNE     ui_push",
        "    MOV     R0, #48",
        "    BL      uart_char",
        "    B       ui_done",
        "ui_push:",
        "    CMP     R4, #0",
        "    BEQ     ui_print",
        "    MOV     R1, #10",
        "    MOV     R2, #0",
        "ui_div:",
        "    CMP     R4, R1",
        "    BLT     ui_div_end",
        "    SUB     R4, R4, R1",
        "    ADD     R2, R2, #1",
        "    B       ui_div",
        "ui_div_end:",
        "    ADD     R4, R4, #48",
        "    PUSH    {R4}",
        "    ADD     R5, R5, #1",
        "    MOV     R4, R2",
        "    B       ui_push",
        "ui_print:",
        "    CMP     R5, #0",
        "    BEQ     ui_done",
        "    POP     {R0}",
        "    BL      uart_char",
        "    SUB     R5, R5, #1",
        "    B       ui_print",
        "ui_done:",
        "    POP     {R0-R5, PC}",
        "",
        "@ uart_float: imprime D0 com 2 casas decimais",
        "uart_float:",
        "    PUSH    {R0-R3, LR}",
        "    VPUSH   {D1-D3}",
        "    @ checa negativo",
        "    VMOV    R0, R1, D0",
        "    CMP     R1, #0",
        "    BGE     uf_pos",
        "    MOV     R0, #45",
        "    BL      uart_char",
        "    VNEG.F64 D0, D0",
        "uf_pos:",
        "    @ parte inteira",
        "    VCVT.S32.F64 S4, D0",
        "    VMOV    R0, S4",
        "    PUSH    {R0}",
        "    BL      uart_int",
        "    @ ponto decimal",
        "    MOV     R0, #46",
        "    BL      uart_char",
        "    @ parte fracionaria: (D0 - int) * 100",
        "    POP     {R0}",
        "    VMOV    S4, R0",
        "    VCVT.F64.S32 D1, S4",
        "    VSUB.F64 D2, D0, D1",
        "    MOV     R0, #100",
        "    VMOV    S4, R0",
        "    VCVT.F64.S32 D3, S4",
        "    VMUL.F64 D2, D2, D3",
        "    VCVT.S32.F64 S4, D2",
        "    VMOV    R0, S4",
        "    @ valor absoluto da parte fracionaria",
        "    CMP     R0, #0",
        "    RSBLT   R0, R0, #0",
        "    @ leading zero se < 10",
        "    CMP     R0, #10",
        "    BGE     uf_two",
        "    PUSH    {R0}",
        "    MOV     R0, #48",
        "    BL      uart_char",
        "    POP     {R0}",
        "uf_two:",
        "    BL      uart_int",
        "    VPOP    {D1-D3}",
        "    POP     {R0-R3, PC}",
    ]

    secao_text = [
        ".global _start",
        ".text",
        "_start:",
        "    @ --- Inicialização da FPU ---",
        "    LDR     R0, =(0xF << 20)",
        "    MCR     P15, 0, R0, C1, C0, 2",
        "    ISB",
        "    MOV     R0, #0x40000000",
        "    VMSR    FPEXC, R0",
        "    @ ---------------------------",
    ] + instrucoes + [
        "    MOV     R7, #1",
        "    SWI     0",
    ] + subrotinas

    bloco = "\n".join(secao_data + [""] + secao_text)
    codigo_assembly.append(bloco)
    return bloco