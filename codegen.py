# Endereço do display HEX do CPUlator (ARMv7)
_HEX_DISPLAY_ADDR = 0xFF200020

class CodegenError(Exception):
    pass

def gerarAssembly(tokens, codigo_assembly):
    """
    Traduz tokens de uma expressão RPN para instruções ARMv7 VFP (Double Precision).
    """
    linhas = []
    mem_labels = {}   # MEM_ID -> label na seção .data
    literais = {}     # valor float -> label na seção .data
    reg_counter = [0]

    def prox_reg():
        """Retorna registradores D (64-bit) para operações .F64."""
        r = f"D{reg_counter[0]}"
        reg_counter[0] += 1
        return r

    def label_literal(val_str):
        key = val_str
        if key not in literais:
            label = f"lit_{len(literais)}"
            literais[key] = label
        return literais[key]

    def label_mem(nome):
        if nome not in mem_labels:
            mem_labels[nome] = f"mem_{nome.lower()}"
        return mem_labels[nome]

    # --- Primeira passagem: Geração de instruções ---
    instrucoes = []
    pilha = [] # Pilha de registradores (strings "Dx")

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
                # Divisão inteira usando S0 como ponte para conversão
                instrucoes.append(f"    VCVT.S32.F64 S0, {reg_a}")
                instrucoes.append(f"    VCVT.S32.F64 S1, {reg_b}")
                instrucoes.append(f"    VMOV     R0, S0")
                instrucoes.append(f"    VMOV     R1, S1")
                instrucoes.append(f"    SDIV     R0, R0, R1")
                instrucoes.append(f"    VMOV     S0, R0")
                instrucoes.append(f"    VCVT.F64.S32 {reg_r}, S0")
            elif valor == '%':
                # Resto: R0 - (R2 * R1)
                instrucoes.append(f"    VCVT.S32.F64 S0, {reg_a}")
                instrucoes.append(f"    VCVT.S32.F64 S1, {reg_b}")
                instrucoes.append(f"    VMOV     R0, S0")
                instrucoes.append(f"    VMOV     R1, S1")
                instrucoes.append(f"    SDIV     R2, R0, R1")
                instrucoes.append(f"    MLS      R0, R2, R1, R0")
                instrucoes.append(f"    VMOV     S0, R0")
                instrucoes.append(f"    VCVT.F64.S32 {reg_r}, S0")
            elif valor == '^':
                # Loop de potenciação
                reg_um = prox_reg()
                instrucoes.append(f"    VCVT.S32.F64 S1, {reg_b}")
                instrucoes.append(f"    VMOV     R2, S1")       # R2 = expoente
                instrucoes.append(f"    MOV      R3, #1")
                instrucoes.append(f"    VMOV     S0, R3")
                instrucoes.append(f"    VCVT.F64.S32 {reg_um}, S0") # reg_um = 1.0
                instrucoes.append(f"pow_loop_{reg_r}:")
                instrucoes.append(f"    CMP      R2, #0")
                instrucoes.append(f"    BLE      pow_end_{reg_r}")
                instrucoes.append(f"    VMUL.F64 {reg_um}, {reg_um}, {reg_a}")
                instrucoes.append(f"    SUB      R2, R2, #1")
                instrucoes.append(f"    B        pow_loop_{reg_r}")
                instrucoes.append(f"pow_end_{reg_r}:")
                instrucoes.append(f"    VMOV.F64 {reg_r}, {reg_um}")

            pilha.append(reg_r)
            i += 1

        elif tipo == "KEYWORD_RES":
            idx = int(float(tokens[i + 1]["valor"]))
            reg = prox_reg()
            instrucoes.append(f"    @ carrega RES[{idx}] em {reg}")
            instrucoes.append(f"    LDR     R0, =res_hist_{idx}")
            instrucoes.append(f"    VLDR    {reg}, [R0]")
            pilha.append(reg)
            i += 2

        elif tipo == "MEM_ID":
            # Lógica de Store/Load simplificada
            tem_valor = any(r is not None for r in pilha) and pilha[-1] is not None
            if i + 1 < len(tokens) and tokens[i+1]["tipo"] == "FECHA_PAREN" and tem_valor:
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

    # Envia resultado final para o display HEX
    if pilha and pilha[-1] is not None:
        reg_res = pilha[-1]
        instrucoes.append(f"    @ envia resultado para display HEX")
        instrucoes.append(f"    VCVT.S32.F64 S0, {reg_res}")
        instrucoes.append(f"    VMOV     R0, S0")
        instrucoes.append(f"    LDR      R1, =0x{_HEX_DISPLAY_ADDR:08X}")
        instrucoes.append(f"    STR      R0, [R1]")

    # --- Montagem do Bloco Final ---
    secao_data = [".data", ".align 3"]
    for val_str, lbl in literais.items():
        secao_data.append(f"{lbl}:  .double {val_str}")
    for nome, lbl in mem_labels.items():
        secao_data.append(f"{lbl}:  .double 0.0")

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