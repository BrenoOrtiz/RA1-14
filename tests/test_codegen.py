"""Testes unitarios do gerador de codigo assembly ARMv7 — codegen.py.

Verifica que as instrucoes VFP .F64 (IEEE 754 64-bit) sao geradas
corretamente para cada operacao RPN, incluindo literais, variaveis
de memoria, keyword RES, erros lexicos e sub-rotinas JTAG UART.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from codegen import gerarAssembly, CodegenError
from lexer import tokenizar


def _gerar(expressoes):
    """Helper: gera assembly a partir de uma lista de expressoes string.

    Args:
        expressoes: Lista de strings com expressoes RPN ou "ERRO_LEXICO".

    Returns:
        String com o programa assembly completo.
    """
    lista_tokens = []
    for expr in expressoes:
        if expr == "ERRO_LEXICO":
            lista_tokens.append("ERRO_LEXICO")
        else:
            lista_tokens.append(tokenizar(expr))
    buf = []
    return gerarAssembly(lista_tokens, buf)


class TestEstruturaAssembly(unittest.TestCase):
    """Verifica que o assembly gerado tem a estrutura correta."""

    def test_secao_data(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn(".data", asm)
        self.assertIn(".align 3", asm)

    def test_secao_text(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn(".text", asm)
        self.assertIn(".global _start", asm)
        self.assertIn("_start:", asm)

    def test_inicializacao_fpu(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("FPEXC", asm)
        self.assertIn("MCR", asm)

    def test_terminacao_programa(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("SWI", asm)

    def test_subrotinas_uart(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("uart_char:", asm)
        self.assertIn("uart_int:", asm)
        self.assertIn("uart_float:", asm)

    def test_endereco_jtag_uart(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("0xFF201000", asm)


class TestLiteraisData(unittest.TestCase):
    """Verifica geracao de literais .double na secao .data."""

    def test_literal_inteiro(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn(".double 10", asm)
        self.assertIn(".double 5", asm)

    def test_literal_decimal(self):
        asm = _gerar(["(3.14 7 *)"])
        self.assertIn(".double 3.14", asm)
        self.assertIn(".double 7", asm)

    def test_literal_nao_duplicado(self):
        """Mesmo literal usado duas vezes deve gerar apenas um .double."""
        asm = _gerar(["(5 5 +)"])
        count = asm.count(".double 5")
        self.assertEqual(count, 1)


class TestOperacoesVFP(unittest.TestCase):
    """Verifica que instrucoes VFP .F64 corretas sao geradas."""

    def test_soma_vadd(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("VADD.F64", asm)

    def test_subtracao_vsub(self):
        asm = _gerar(["(20 4.3 -)"])
        self.assertIn("VSUB.F64", asm)

    def test_multiplicacao_vmul(self):
        asm = _gerar(["(3.14 7 *)"])
        self.assertIn("VMUL.F64", asm)

    def test_divisao_vdiv(self):
        asm = _gerar(["(100 4 /)"])
        self.assertIn("VDIV.F64", asm)

    def test_divisao_inteira_vcvt(self):
        """Divisao inteira deve usar VDIV + VCVT para truncar."""
        asm = _gerar(["(17 5 //)"])
        self.assertIn("VDIV.F64", asm)
        self.assertIn("VCVT.S32.F64", asm)
        self.assertIn("VCVT.F64.S32", asm)

    def test_modulo_sequencia(self):
        """Modulo usa VDIV + VCVT + VMUL + VSUB."""
        asm = _gerar(["(17 5 %)"])
        self.assertIn("VDIV.F64", asm)
        self.assertIn("VMUL.F64", asm)
        self.assertIn("VSUB.F64", asm)

    def test_potenciacao_loop(self):
        """Potenciacao gera loop com VMUL."""
        asm = _gerar(["(2 8 ^)"])
        self.assertIn("VMUL.F64", asm)
        self.assertIn("pow_loop", asm)
        self.assertIn("pow_end", asm)
        self.assertIn("CMP", asm)
        self.assertIn("BLE", asm)

    def test_vldr_para_carregar_numeros(self):
        asm = _gerar(["(42 1 +)"])
        self.assertIn("VLDR", asm)


class TestMemoriaAssembly(unittest.TestCase):
    """Verifica geracao de assembly para variaveis de memoria."""

    def test_store_vstr(self):
        asm = _gerar(["(15.75 MA)"])
        self.assertIn("VSTR", asm)
        self.assertIn("mem_ma", asm)

    def test_load_vldr(self):
        asm = _gerar(["(MA 3 *)"])
        self.assertIn("VLDR", asm)
        self.assertIn("mem_ma", asm)

    def test_mem_na_secao_data(self):
        asm = _gerar(["(15.75 MA)"])
        self.assertIn("mem_ma:  .double 0.0", asm)

    def test_multiplas_variaveis(self):
        asm = _gerar(["(10 X)", "(20 Y)"])
        self.assertIn("mem_x", asm)
        self.assertIn("mem_y", asm)


class TestRESAssembly(unittest.TestCase):
    """Verifica geracao de assembly para keyword RES."""

    def test_res_gera_label_hist(self):
        asm = _gerar(["(8 4 +)", "(1 RES 5 +)"])
        self.assertIn("res_hist_1", asm)

    def test_res_carrega_vldr(self):
        asm = _gerar(["(10 5 +)", "(1 RES 3 *)"])
        self.assertIn("VLDR", asm)
        self.assertIn("res_hist_1", asm)

    def test_res_historico_na_data(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("res_hist_1:  .double 0.0", asm)


class TestErroLexicoAssembly(unittest.TestCase):
    """Verifica que erros lexicos geram mensagem no assembly."""

    def test_erro_lexico_gera_mensagem(self):
        asm = _gerar(["ERRO_LEXICO"])
        self.assertIn("Erro lexico", asm)
        self.assertIn("uart_char", asm)

    def test_erro_lexico_nao_quebra_demais(self):
        """Erro lexico em uma linha nao impede geracao das outras."""
        asm = _gerar(["(10 5 +)", "ERRO_LEXICO", "(3 2 *)"])
        self.assertIn("VADD.F64", asm)
        self.assertIn("VMUL.F64", asm)
        self.assertIn("Erro lexico", asm)


class TestExpressoesAninhadas(unittest.TestCase):
    """Verifica geracao de assembly para expressoes com subexpressoes."""

    def test_aninhada_gera_multiplas_ops(self):
        asm = _gerar(["((3 4 +) (2 5 *) -)"])
        self.assertIn("VADD.F64", asm)
        self.assertIn("VMUL.F64", asm)
        self.assertIn("VSUB.F64", asm)

    def test_resultado_salvo_no_historico(self):
        asm = _gerar(["((10 2 +) (3 1 -) *)"])
        self.assertIn("res_hist_1", asm)
        self.assertIn("VSTR", asm)


class TestSaida(unittest.TestCase):
    """Verifica que o assembly imprime resultados no JTAG UART."""

    def test_imprime_numero_linha(self):
        """Deve imprimir 'L' (76) e '=' (61) para cada resultado."""
        asm = _gerar(["(10 5 +)"])
        self.assertIn("MOV      R0, #76", asm)   # 'L'
        self.assertIn("MOV      R0, #61", asm)    # '='

    def test_imprime_newline(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("MOV      R0, #10", asm)    # '\n'

    def test_chama_uart_float(self):
        asm = _gerar(["(10 5 +)"])
        self.assertIn("BL       uart_float", asm)


class TestRetornoFuncao(unittest.TestCase):
    """Verifica que gerarAssembly retorna o bloco e preenche buffer."""

    def test_retorna_string(self):
        buf = []
        retorno = gerarAssembly([tokenizar("(1 2 +)")], buf)
        self.assertIsInstance(retorno, str)
        self.assertTrue(len(retorno) > 0)

    def test_preenche_buffer(self):
        buf = []
        gerarAssembly([tokenizar("(1 2 +)")], buf)
        self.assertEqual(len(buf), 1)
        self.assertIn(".data", buf[0])


if __name__ == "__main__":
    unittest.main()
