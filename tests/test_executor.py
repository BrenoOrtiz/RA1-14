"""Testes unitarios do executor de expressoes RPN — executor.py.

Cobre todas as operacoes aritmeticas (+, -, *, /, //, %, ^),
variaveis de memoria (store/load), keyword RES, tratamento de erros
(divisao por zero, operandos insuficientes, indice RES invalido),
e precisao IEEE 754 64-bit via float do Python.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from executor import executarExpressao, ExecError
from lexer import tokenizar


def _tokens(expr):
    """Helper: tokeniza uma expressao para usar nos testes."""
    return tokenizar(expr)


class TestOperacoesBasicas(unittest.TestCase):
    """Testes das 7 operacoes aritmeticas com inteiros e decimais."""

    def test_soma_inteiros(self):
        resultado = executarExpressao(_tokens("(10 5 +)"), {}, {})
        self.assertAlmostEqual(resultado, 15.0)

    def test_soma_decimais(self):
        resultado = executarExpressao(_tokens("(3.14 2.86 +)"), {}, {})
        self.assertAlmostEqual(resultado, 6.0)

    def test_subtracao(self):
        resultado = executarExpressao(_tokens("(20 4.3 -)"), {}, {})
        self.assertAlmostEqual(resultado, 15.7)

    def test_multiplicacao(self):
        resultado = executarExpressao(_tokens("(3.14 7 *)"), {}, {})
        self.assertAlmostEqual(resultado, 21.98)

    def test_divisao_real(self):
        resultado = executarExpressao(_tokens("(100.8 4 /)"), {}, {})
        self.assertAlmostEqual(resultado, 25.2)

    def test_divisao_inteira(self):
        resultado = executarExpressao(_tokens("(17 5 //)"), {}, {})
        self.assertAlmostEqual(resultado, 3.0)

    def test_modulo(self):
        resultado = executarExpressao(_tokens("(17 5 %)"), {}, {})
        self.assertAlmostEqual(resultado, 2.0)

    def test_potenciacao(self):
        resultado = executarExpressao(_tokens("(2.5 8 ^)"), {}, {})
        self.assertAlmostEqual(resultado, 1525.87890625)

    def test_potenciacao_base_inteira(self):
        resultado = executarExpressao(_tokens("(2 10 ^)"), {}, {})
        self.assertAlmostEqual(resultado, 1024.0)

    def test_potenciacao_expoente_zero(self):
        resultado = executarExpressao(_tokens("(5 0 ^)"), {}, {})
        self.assertAlmostEqual(resultado, 1.0)


class TestExpressoesAninhadas(unittest.TestCase):
    """Testes de expressoes com parenteses aninhados."""

    def test_subexpressao_simples(self):
        # ((3 4 +) (2 5 *) -) = 7 - 10 = -3
        resultado = executarExpressao(_tokens("((3 4 +) (2 5 *) -)"), {}, {})
        self.assertAlmostEqual(resultado, -3.0)

    def test_subexpressao_tripla(self):
        # ((10 2 +) (3 1 -) *) = 12 * 2 = 24
        resultado = executarExpressao(_tokens("((10 2 +) (3 1 -) *)"), {}, {})
        self.assertAlmostEqual(resultado, 24.0)

    def test_operacao_apos_subexpressao(self):
        # (X Y * 100 +) com X=50.5, Y=30.25 = 1527.625 + 100 = 1627.625
        mem = {"X": 50.5, "Y": 30.25}
        resultado = executarExpressao(_tokens("(X Y * 100 +)"), mem, {})
        self.assertAlmostEqual(resultado, 1627.625)


class TestMemoria(unittest.TestCase):
    """Testes de armazenamento e leitura de variaveis de memoria."""

    def test_store_retorna_none(self):
        mem = {}
        resultado = executarExpressao(_tokens("(15.75 MA)"), mem, {})
        self.assertIsNone(resultado)
        self.assertAlmostEqual(mem["MA"], 15.75)

    def test_load_apos_store(self):
        mem = {"MA": 15.75}
        resultado = executarExpressao(_tokens("(MA 3 *)"), mem, {})
        self.assertAlmostEqual(resultado, 47.25)

    def test_mem_nao_inicializada_retorna_zero(self):
        mem = {}
        resultado = executarExpressao(_tokens("(X 5 +)"), mem, {})
        self.assertAlmostEqual(resultado, 5.0)

    def test_store_e_load_sequencial(self):
        mem = {}
        executarExpressao(_tokens("(50.5 X)"), mem, {})
        executarExpressao(_tokens("(30.25 Y)"), mem, {})
        resultado = executarExpressao(_tokens("(X Y +)"), mem, {})
        self.assertAlmostEqual(resultado, 80.75)

    def test_store_com_expressao(self):
        mem = {"MA": 15.75}
        resultado = executarExpressao(_tokens("(MA 10.25 + TOTAL)"), mem, {})
        self.assertIsNone(resultado)
        self.assertAlmostEqual(mem["TOTAL"], 26.0)

    def test_multiplas_variaveis(self):
        mem = {}
        executarExpressao(_tokens("(100 A)"), mem, {})
        executarExpressao(_tokens("(200 B)"), mem, {})
        executarExpressao(_tokens("(300 C)"), mem, {})
        self.assertAlmostEqual(mem["A"], 100.0)
        self.assertAlmostEqual(mem["B"], 200.0)
        self.assertAlmostEqual(mem["C"], 300.0)


class TestKeywordRES(unittest.TestCase):
    """Testes da keyword RES para referenciar resultados anteriores."""

    def test_res_referencia_linha(self):
        hist = {1: 12.0, 2: 20.41}
        resultado = executarExpressao(_tokens("(1 RES 2 RES +)"), {}, hist)
        self.assertAlmostEqual(resultado, 32.41)

    def test_res_com_operacao(self):
        hist = {1: 12.0}
        resultado = executarExpressao(_tokens("(1 RES 2.5 /)"), {}, hist)
        self.assertAlmostEqual(resultado, 4.8)

    def test_res_indice_invalido(self):
        hist = {1: 10.0}
        with self.assertRaises(ExecError):
            executarExpressao(_tokens("(99 RES 5 +)"), {}, hist)

    def test_res_historico_vazio(self):
        with self.assertRaises(ExecError):
            executarExpressao(_tokens("(1 RES 5 +)"), {}, {})


class TestErrosExecucao(unittest.TestCase):
    """Testes de tratamento de erros durante a execucao."""

    def test_divisao_por_zero(self):
        with self.assertRaises(ExecError):
            executarExpressao(_tokens("(10 0 /)"), {}, {})

    def test_divisao_inteira_por_zero(self):
        with self.assertRaises(ExecError):
            executarExpressao(_tokens("(10 0 //)"), {}, {})

    def test_modulo_por_zero(self):
        with self.assertRaises(ExecError):
            executarExpressao(_tokens("(10 0 %)"), {}, {})

    def test_operandos_insuficientes(self):
        with self.assertRaises(ExecError):
            executarExpressao(_tokens("(5 +)"), {}, {})

    def test_expoente_negativo(self):
        # O executor converte expoente para int; se negativo, levanta erro
        # Criamos tokens manualmente para garantir o cenario
        tokens = [
            {"tipo": "ABRE_PAREN", "valor": "("},
            {"tipo": "NUMERO", "valor": "2"},
            {"tipo": "NUMERO", "valor": "-1"},
            {"tipo": "OPERADOR", "valor": "^"},
            {"tipo": "FECHA_PAREN", "valor": ")"},
        ]
        # O lexer trata '-' como operador, entao nao gera NUMERO negativo
        # Mas se tivermos tokens negativos, a logica deve funcionar
        # Na pratica, o operador - em RPN subtrai, nao gera negativo
        # Este teste verifica robustez com manipulacao direta
        with self.assertRaises(ExecError):
            executarExpressao(tokens, {}, {})


class TestPrecisaoIEEE754(unittest.TestCase):
    """Testes que verificam a precisao de 64-bit (float Python = double C)."""

    def test_float_64_bits(self):
        """Python float tem 64 bits (IEEE 754 double precision)."""
        import struct
        val = 3.14
        packed = struct.pack('d', val)  # 'd' = double = 8 bytes = 64 bits
        self.assertEqual(len(packed), 8)

    def test_precisao_soma(self):
        resultado = executarExpressao(_tokens("(0 1 +)"), {}, {})
        # 0.1 + 0.2 nao e exatamente 0.3 em IEEE 754, mas nao testamos isso
        # Testamos que operacoes sao feitas em float (double)
        self.assertIsInstance(resultado, float)

    def test_resultado_grande_preciso(self):
        resultado = executarExpressao(_tokens("(2 20 ^)"), {}, {})
        self.assertAlmostEqual(resultado, 1048576.0)

    def test_decimal_preciso(self):
        resultado = executarExpressao(_tokens("(100.8 4 /)"), {}, {})
        self.assertAlmostEqual(resultado, 25.2, places=10)


class TestCasosIntegracao(unittest.TestCase):
    """Testes de integracao reproduzindo linhas dos arquivos de teste."""

    def test_teste1_linha11(self):
        """((3 4 +) (2 5 *) -) = 7 - 10 = -3"""
        resultado = executarExpressao(_tokens("((3 4 +) (2 5 *) -)"), {}, {})
        self.assertAlmostEqual(resultado, -3.0)

    def test_teste1_fluxo_completo(self):
        """Simula as linhas 1-6 do teste1.txt."""
        mem = {}
        hist = {}

        r1 = executarExpressao(_tokens("(10 5 +)"), mem, hist)
        hist[1] = r1
        self.assertAlmostEqual(r1, 15.0)

        r2 = executarExpressao(_tokens("(20 4.3 -)"), mem, hist)
        hist[2] = r2
        self.assertAlmostEqual(r2, 15.7)

        r3 = executarExpressao(_tokens("(3.14 7 *)"), mem, hist)
        hist[3] = r3
        self.assertAlmostEqual(r3, 21.98)

        r4 = executarExpressao(_tokens("(15.75 MA)"), mem, hist)
        self.assertIsNone(r4)
        self.assertAlmostEqual(mem["MA"], 15.75)

        r5 = executarExpressao(_tokens("(MA 3 *)"), mem, hist)
        hist[5] = r5
        self.assertAlmostEqual(r5, 47.25)

        r6 = executarExpressao(_tokens("(100.8 4 /)"), mem, hist)
        hist[6] = r6
        self.assertAlmostEqual(r6, 25.2)

    def test_teste3_fluxo_res(self):
        """Simula linhas do teste3.txt com RES."""
        mem = {}
        hist = {}

        r1 = executarExpressao(_tokens("(8 4 +)"), mem, hist)
        hist[1] = r1
        self.assertAlmostEqual(r1, 12.0)

        r2 = executarExpressao(_tokens("(6.5 3.14 *)"), mem, hist)
        hist[2] = r2
        self.assertAlmostEqual(r2, 20.41)

        r4 = executarExpressao(_tokens("(1 RES 2 RES +)"), mem, hist)
        hist[4] = r4
        self.assertAlmostEqual(r4, 32.41)

        r5 = executarExpressao(_tokens("(1 RES 2.5 /)"), mem, hist)
        hist[5] = r5
        self.assertAlmostEqual(r5, 4.8)


if __name__ == "__main__":
    unittest.main()
