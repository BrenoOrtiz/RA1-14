# Endereço do display HEX do CPUlator (ARMv7)
_HEX_DISPLAY_ADDR = 0xFF200020

class CodegenError(Exception):
    pass

def gerarAssembly(lista_tokens, codigo_assembly):
    """
    Traduz múltiplas expressões RPN para um único programa ARMv7 VFP (Double Precision).

    lista_tokens -- lista de listas de tokens (uma por linha/expressão)
    codigo_assembly -- lista mutável onde o bloco assembly final é adicionado
    """
    mem_labels = {}   # MEM_ID -> label na seção .data
    literais = {}     # valor float -> label na seção .data
    res_indices = set()  # índices RES usados
    reg_counter = [0]

    def prox_reg():
        """Retorna registradores D (64-bit) para operações .F64."""
        r = f"D{reg_counter[0]}"
        reg_counter[0] += 1
        return r

    def label_literal(val_str):
        if val_str not in literais:
            literais[val_str] = f"lit_{len(literais)}"
        return literais[val_str]

    def label_mem(nome):
        if nome not in mem_labels:
            mem_labels[nome] = f"mem_{nome.lower()}"
        return mem_labels[nome]

    instrucoes = []

    for num_linha, tokens in enumerate(lista_tokens, start=1):
        instrucoes.append(f"    @ ===== Linha {num_linha} =====")
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
                    instrucoes.append(f"    VCVT.S32.F64 S0, {reg_a}")
                    instrucoes.append(f"    VCVT.S32.F64 S1, {reg_b}")
                    instrucoes.append(f"    VMOV     R0, S0")
                    instrucoes.append(f"    VMOV     R1, S1")
                    instrucoes.append(f"    SDIV     R0, R0, R1")
                    instrucoes.append(f"    VMOV     S0, R0")
                    instrucoes.append(f"    VCVT.F64.S32 {reg_r}, S0")
                elif valor == '%':
                    instrucoes.append(f"    VCVT.S32.F64 S0, {reg_a}")
                    instrucoes.append(f"    VCVT.S32.F64 S1, {reg_b}")
                    instrucoes.append(f"    VMOV     R0, S0")
                    instrucoes.append(f"    VMOV     R1, S1")
                    instrucoes.append(f"    SDIV     R2, R0, R1")
                    instrucoes.append(f"    MLS      R0, R2, R1, R0")
                    instrucoes.append(f"    VMOV     S0, R0")
                    instrucoes.append(f"    VCVT.F64.S32 {reg_r}, S0")
                elif valor == '^':
                    lbl_loop = f"pow_loop_L{num_linha}_{reg_r}"
                    lbl_end = f"pow_end_L{num_linha}_{reg_r}"
                    reg_um = prox_reg()
                    instrucoes.append(f"    VCVT.S32.F64 S1, {reg_b}")
                    instrucoes.append(f"    VMOV     R2, S1")
                    instrucoes.append(f"    MOV      R3, #1")
                    instrucoes.append(f"    VMOV     S0, R3")
                    instrucoes.append(f"    VCVT.F64.S32 {reg_um}, S0")
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
                # O índice vem ANTES (já na pilha como registrador)
                if not pilha or pilha[-1] is None:
                    raise CodegenError("RES requer um número antes (ex: 1 RES)")
                reg_idx = pilha.pop()
                # Extrai o valor literal do registrador para saber qual res_hist carregar
                # Busca para trás o literal que foi carregado nesse registrador
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

        # Salva resultado no histórico RES e envia para display HEX
        if pilha and pilha[-1] is not None:
            reg_res = pilha[-1]
            res_indices.add(num_linha)
            instrucoes.append(f"    @ salva resultado em res_hist_{num_linha}")
            instrucoes.append(f"    LDR     R0, =res_hist_{num_linha}")
            instrucoes.append(f"    VSTR    {reg_res}, [R0]")
            instrucoes.append(f"    @ envia resultado para display HEX")
            instrucoes.append(f"    VCVT.S32.F64 S0, {reg_res}")
            instrucoes.append(f"    VMOV     R0, S0")
            instrucoes.append(f"    LDR      R1, =0x{_HEX_DISPLAY_ADDR:08X}")
            instrucoes.append(f"    STR      R0, [R1]")

    # --- Montagem do Bloco Final (único) ---
    secao_data = [".data", ".align 3"]
    for val_str, lbl in literais.items():
        secao_data.append(f"{lbl}:  .double {val_str}")
    for nome, lbl in mem_labels.items():
        secao_data.append(f"{lbl}:  .double 0.0")
    for idx in sorted(res_indices):
        secao_data.append(f"res_hist_{idx}:  .double 0.0")

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
    ]

    bloco = "\n".join(secao_data + [""] + secao_text)
    codigo_assembly.append(bloco)
    return bloco