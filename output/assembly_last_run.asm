.data
.align 3
lit_0:  .double 10
lit_1:  .double 5
lit_2:  .double 20
lit_3:  .double 4.3
lit_4:  .double 3.14
lit_5:  .double 7
lit_6:  .double 15.75
lit_7:  .double 3
lit_8:  .double 100.8
lit_9:  .double 4
lit_10:  .double 17
lit_11:  .double 2.5
lit_12:  .double 8
lit_13:  .double 2
lit_14:  .double 10.25
lit_15:  .double 5.1
mem_ma:  .double 0.0
mem_total:  .double 0.0
res_hist_1:  .double 0.0
res_hist_2:  .double 0.0
res_hist_3:  .double 0.0
res_hist_5:  .double 0.0
res_hist_6:  .double 0.0
res_hist_7:  .double 0.0
res_hist_8:  .double 0.0
res_hist_9:  .double 0.0
res_hist_11:  .double 0.0
res_hist_13:  .double 0.0
res_hist_14:  .double 0.0

.global _start
.text
_start:
    @ --- Inicialização da FPU ---
    LDR     R0, =(0xF << 20)
    MCR     P15, 0, R0, C1, C0, 2
    ISB
    MOV     R0, #0x40000000
    VMSR    FPEXC, R0
    @ ---------------------------
    @ ===== Linha 1 =====
    @ carrega 10 em D0
    LDR     R0, =lit_0
    VLDR    D0, [R0]
    @ carrega 5 em D1
    LDR     R0, =lit_1
    VLDR    D1, [R0]
    @ D0 + D1 -> D2
    VADD.F64 D2, D0, D1
    @ salva resultado em res_hist_1
    LDR     R0, =res_hist_1
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #1
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 2 =====
    @ carrega 20 em D0
    LDR     R0, =lit_2
    VLDR    D0, [R0]
    @ carrega 4.3 em D1
    LDR     R0, =lit_3
    VLDR    D1, [R0]
    @ D0 - D1 -> D2
    VSUB.F64 D2, D0, D1
    @ salva resultado em res_hist_2
    LDR     R0, =res_hist_2
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #2
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 3 =====
    @ carrega 3.14 em D0
    LDR     R0, =lit_4
    VLDR    D0, [R0]
    @ carrega 7 em D1
    LDR     R0, =lit_5
    VLDR    D1, [R0]
    @ D0 * D1 -> D2
    VMUL.F64 D2, D0, D1
    @ salva resultado em res_hist_3
    LDR     R0, =res_hist_3
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #3
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 4 =====
    @ carrega 15.75 em D0
    LDR     R0, =lit_6
    VLDR    D0, [R0]
    @ armazena D0 em MA
    LDR     R0, =mem_ma
    VSTR    D0, [R0]
    @ ===== Linha 5 =====
    @ lê MA -> D0
    LDR     R0, =mem_ma
    VLDR    D0, [R0]
    @ carrega 3 em D1
    LDR     R0, =lit_7
    VLDR    D1, [R0]
    @ D0 * D1 -> D2
    VMUL.F64 D2, D0, D1
    @ salva resultado em res_hist_5
    LDR     R0, =res_hist_5
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #5
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 6 =====
    @ carrega 100.8 em D0
    LDR     R0, =lit_8
    VLDR    D0, [R0]
    @ carrega 4 em D1
    LDR     R0, =lit_9
    VLDR    D1, [R0]
    @ D0 / D1 -> D2
    VDIV.F64 D2, D0, D1
    @ salva resultado em res_hist_6
    LDR     R0, =res_hist_6
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #6
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 7 =====
    @ carrega 17 em D0
    LDR     R0, =lit_10
    VLDR    D0, [R0]
    @ carrega 5 em D1
    LDR     R0, =lit_1
    VLDR    D1, [R0]
    @ D0 // D1 -> D2
    VDIV.F64 D3, D0, D1
    VCVT.S32.F64 S8, D3
    VCVT.F64.S32 D2, S8
    @ salva resultado em res_hist_7
    LDR     R0, =res_hist_7
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #7
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 8 =====
    @ carrega 17 em D0
    LDR     R0, =lit_10
    VLDR    D0, [R0]
    @ carrega 5 em D1
    LDR     R0, =lit_1
    VLDR    D1, [R0]
    @ D0 % D1 -> D2
    VDIV.F64 D3, D0, D1
    VCVT.S32.F64 S12, D3
    VCVT.F64.S32 D4, S12
    VMUL.F64 D5, D4, D1
    VSUB.F64 D2, D0, D5
    @ salva resultado em res_hist_8
    LDR     R0, =res_hist_8
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #8
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 9 =====
    @ carrega 2.5 em D0
    LDR     R0, =lit_11
    VLDR    D0, [R0]
    @ carrega 8 em D1
    LDR     R0, =lit_12
    VLDR    D1, [R0]
    @ D0 ^ D1 -> D2
    VCVT.S32.F64 S8, D1
    VMOV     R2, S8
    MOV      R3, #1
    VMOV     S8, R3
    VCVT.F64.S32 D3, S8
pow_loop_L9_D2:
    CMP      R2, #0
    BLE      pow_end_L9_D2
    VMUL.F64 D3, D3, D0
    SUB      R2, R2, #1
    B        pow_loop_L9_D2
pow_end_L9_D2:
    VMOV.F64 D2, D3
    @ salva resultado em res_hist_9
    LDR     R0, =res_hist_9
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #9
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 10 =====
    @ Erro lexico - imprime mensagem
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #10
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    MOV      R0, #69
    BL       uart_char
    MOV      R0, #114
    BL       uart_char
    MOV      R0, #114
    BL       uart_char
    MOV      R0, #111
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    MOV      R0, #108
    BL       uart_char
    MOV      R0, #101
    BL       uart_char
    MOV      R0, #120
    BL       uart_char
    MOV      R0, #105
    BL       uart_char
    MOV      R0, #99
    BL       uart_char
    MOV      R0, #111
    BL       uart_char
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 11 =====
    @ carrega 3 em D0
    LDR     R0, =lit_7
    VLDR    D0, [R0]
    @ carrega 4 em D1
    LDR     R0, =lit_9
    VLDR    D1, [R0]
    @ D0 + D1 -> D2
    VADD.F64 D2, D0, D1
    @ carrega 2 em D3
    LDR     R0, =lit_13
    VLDR    D3, [R0]
    @ carrega 5 em D4
    LDR     R0, =lit_1
    VLDR    D4, [R0]
    @ D3 * D4 -> D5
    VMUL.F64 D5, D3, D4
    @ D2 - D5 -> D6
    VSUB.F64 D6, D2, D5
    @ salva resultado em res_hist_11
    LDR     R0, =res_hist_11
    VSTR    D6, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #11
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D6
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 12 =====
    @ lê MA -> D0
    LDR     R0, =mem_ma
    VLDR    D0, [R0]
    @ carrega 10.25 em D1
    LDR     R0, =lit_14
    VLDR    D1, [R0]
    @ D0 + D1 -> D2
    VADD.F64 D2, D0, D1
    @ armazena D2 em TOTAL
    LDR     R0, =mem_total
    VSTR    D2, [R0]
    @ ===== Linha 13 =====
    @ lê TOTAL -> D0
    LDR     R0, =mem_total
    VLDR    D0, [R0]
    @ carrega 5.1 em D1
    LDR     R0, =lit_15
    VLDR    D1, [R0]
    @ D0 - D1 -> D2
    VSUB.F64 D2, D0, D1
    @ salva resultado em res_hist_13
    LDR     R0, =res_hist_13
    VSTR    D2, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #13
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D2
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    @ ===== Linha 14 =====
    @ lê MA -> D0
    LDR     R0, =mem_ma
    VLDR    D0, [R0]
    @ carrega 2 em D1
    LDR     R0, =lit_13
    VLDR    D1, [R0]
    @ D0 / D1 -> D2
    VDIV.F64 D2, D0, D1
    @ lê TOTAL -> D3
    LDR     R0, =mem_total
    VLDR    D3, [R0]
    @ carrega 3 em D4
    LDR     R0, =lit_7
    VLDR    D4, [R0]
    @ D3 + D4 -> D5
    VADD.F64 D5, D3, D4
    @ D2 * D5 -> D6
    VMUL.F64 D6, D2, D5
    @ salva resultado em res_hist_14
    LDR     R0, =res_hist_14
    VSTR    D6, [R0]
    @ imprime 'L<num>= ' no terminal
    MOV      R0, #76
    BL       uart_char
    MOV      R0, #14
    BL       uart_int
    MOV      R0, #61
    BL       uart_char
    MOV      R0, #32
    BL       uart_char
    @ imprime resultado como float
    VMOV.F64 D0, D6
    BL       uart_float
    MOV      R0, #10
    BL       uart_char
    MOV     R7, #1
    SWI     0

@ ========== Sub-rotinas JTAG UART ==========

@ uart_char: imprime caractere em R0
uart_char:
    PUSH    {R1, R2, LR}
    LDR     R1, =0xFF201000
uart_char_wait:
    LDR     R2, [R1, #4]
    LSR     R2, R2, #16
    CMP     R2, #0
    BEQ     uart_char_wait
    STR     R0, [R1]
    POP     {R1, R2, PC}

@ uart_int: imprime inteiro em R0 (com sinal)
uart_int:
    PUSH    {R0-R5, LR}
    MOV     R4, R0
    CMP     R4, #0
    BGE     ui_pos
    MOV     R0, #45
    BL      uart_char
    RSB     R4, R4, #0
ui_pos:
    MOV     R5, #0
    CMP     R4, #0
    BNE     ui_push
    MOV     R0, #48
    BL      uart_char
    B       ui_done
ui_push:
    CMP     R4, #0
    BEQ     ui_print
    MOV     R1, #10
    MOV     R2, #0
ui_div:
    CMP     R4, R1
    BLT     ui_div_end
    SUB     R4, R4, R1
    ADD     R2, R2, #1
    B       ui_div
ui_div_end:
    ADD     R4, R4, #48
    PUSH    {R4}
    ADD     R5, R5, #1
    MOV     R4, R2
    B       ui_push
ui_print:
    CMP     R5, #0
    BEQ     ui_done
    POP     {R0}
    BL      uart_char
    SUB     R5, R5, #1
    B       ui_print
ui_done:
    POP     {R0-R5, PC}

@ uart_float: imprime D0 com 2 casas decimais
uart_float:
    PUSH    {R0-R3, LR}
    VPUSH   {D1-D3}
    @ checa negativo
    VMOV    R0, R1, D0
    CMP     R1, #0
    BGE     uf_pos
    MOV     R0, #45
    BL      uart_char
    VNEG.F64 D0, D0
uf_pos:
    @ parte inteira
    VCVT.S32.F64 S4, D0
    VMOV    R0, S4
    PUSH    {R0}
    BL      uart_int
    @ ponto decimal
    MOV     R0, #46
    BL      uart_char
    @ parte fracionaria: (D0 - int) * 100
    POP     {R0}
    VMOV    S4, R0
    VCVT.F64.S32 D1, S4
    VSUB.F64 D2, D0, D1
    MOV     R0, #100
    VMOV    S4, R0
    VCVT.F64.S32 D3, S4
    VMUL.F64 D2, D2, D3
    VCVT.S32.F64 S4, D2
    VMOV    R0, S4
    @ valor absoluto da parte fracionaria
    CMP     R0, #0
    RSBLT   R0, R0, #0
    @ leading zero se < 10
    CMP     R0, #10
    BGE     uf_two
    PUSH    {R0}
    MOV     R0, #48
    BL      uart_char
    POP     {R0}
uf_two:
    BL      uart_int
    VPOP    {D1-D3}
    POP     {R0-R3, PC}
