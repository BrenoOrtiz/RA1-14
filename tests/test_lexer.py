"""Testes unitarios do analisador lexico (AFD) — lexer.py.

Cobre todos os tipos de token, transicoes de estado, numeros inteiros
e decimais (IEEE 754 64-bit), operadores, identificadores, parenteses,
erros lexicos e casos-limite.
"""

import sys
import os
import unittest

# Adiciona o diretorio raiz ao path para importar os modulos do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lexer import tokenizar, LexerError


class TestTokenizarNumeros(unittest.TestCase):
    """Testes de reconhecimento de numeros inteiros e decimais."""

    def test_inteiro_simples(self):
        tokens = tokenizar("42")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0], {"tipo": "NUMERO", "valor": "42"})

    def test_inteiro_zero(self):
        tokens = tokenizar("0")
        self.assertEqual(tokens[0], {"tipo": "NUMERO", "valor": "0"})

    def test_decimal_simples(self):
        tokens = tokenizar("3.14")
        self.assertEqual(tokens[0], {"tipo": "NUMERO", "valor": "3.14"})

    def test_decimal_com_parte_inteira_zero(self):
        tokens = tokenizar("0.5")
        self.assertEqual(tokens[0], {"tipo": "NUMERO", "valor": "0.5"})

    def test_decimal_com_muitas_casas(self):
        tokens = tokenizar("123.456789")
        self.assertEqual(tokens[0], {"tipo": "NUMERO", "valor": "123.456789"})

    def test_numero_grande(self):
        tokens = tokenizar("9999999")
        self.assertEqual(tokens[0], {"tipo": "NUMERO", "valor": "9999999"})

    def test_numero_malformado_dois_pontos(self):
        """Numero com dois pontos decimais deve gerar LexerError."""
        with self.assertRaises(LexerError):
            tokenizar("3.14.5")

    def test_ponto_no_final(self):
        """Numero terminando em ponto: '3.' e reconhecido como NUMERO."""
        tokens = tokenizar("3.")
        self.assertEqual(tokens[0]["tipo"], "NUMERO")
        self.assertEqual(tokens[0]["valor"], "3.")


class TestTokenizarOperadores(unittest.TestCase):
    """Testes de reconhecimento de operadores aritmeticos."""

    def test_operador_soma(self):
        tokens = tokenizar("+")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "+"})

    def test_operador_subtracao(self):
        tokens = tokenizar("-")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "-"})

    def test_operador_multiplicacao(self):
        tokens = tokenizar("*")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "*"})

    def test_operador_divisao(self):
        tokens = tokenizar("/")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "/"})

    def test_operador_modulo(self):
        tokens = tokenizar("%")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "%"})

    def test_operador_potencia(self):
        tokens = tokenizar("^")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "^"})

    def test_divisao_inteira(self):
        tokens = tokenizar("//")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR_INT_DIV", "valor": "//"})

    def test_divisao_seguida_de_numero(self):
        """'/ 5' deve gerar OPERADOR '/' e NUMERO '5'."""
        tokens = tokenizar("/ 5")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR", "valor": "/"})
        self.assertEqual(tokens[1], {"tipo": "NUMERO", "valor": "5"})

    def test_divisao_inteira_seguida_de_numero(self):
        """'// 5' deve gerar OPERADOR_INT_DIV '//' e NUMERO '5'."""
        tokens = tokenizar("// 5")
        self.assertEqual(tokens[0], {"tipo": "OPERADOR_INT_DIV", "valor": "//"})
        self.assertEqual(tokens[1], {"tipo": "NUMERO", "valor": "5"})


class TestTokenizarParenteses(unittest.TestCase):
    """Testes de reconhecimento e balanceamento de parenteses."""

    def test_abre_fecha(self):
        tokens = tokenizar("()")
        self.assertEqual(tokens[0], {"tipo": "ABRE_PAREN", "valor": "("})
        self.assertEqual(tokens[1], {"tipo": "FECHA_PAREN", "valor": ")"})

    def test_parenteses_aninhados(self):
        tokens = tokenizar("(())")
        tipos = [t["tipo"] for t in tokens]
        self.assertEqual(tipos, [
            "ABRE_PAREN", "ABRE_PAREN", "FECHA_PAREN", "FECHA_PAREN"
        ])

    def test_parentese_desbalanceado_falta_fechar(self):
        with self.assertRaises(LexerError):
            tokenizar("(()")

    def test_parentese_desbalanceado_falta_abrir(self):
        with self.assertRaises(LexerError):
            tokenizar("())")

    def test_fecha_sem_abrir(self):
        with self.assertRaises(LexerError):
            tokenizar(")")


class TestTokenizarIdentificadores(unittest.TestCase):
    """Testes de reconhecimento de identificadores e keyword RES."""

    def test_keyword_res(self):
        tokens = tokenizar("RES")
        self.assertEqual(tokens[0], {"tipo": "KEYWORD_RES", "valor": "RES"})

    def test_mem_id_simples(self):
        tokens = tokenizar("MA")
        self.assertEqual(tokens[0], {"tipo": "MEM_ID", "valor": "MA"})

    def test_mem_id_uma_letra(self):
        tokens = tokenizar("X")
        self.assertEqual(tokens[0], {"tipo": "MEM_ID", "valor": "X"})

    def test_mem_id_longo(self):
        tokens = tokenizar("TOTAL")
        self.assertEqual(tokens[0], {"tipo": "MEM_ID", "valor": "TOTAL"})

    def test_identificador_nao_e_res(self):
        """RESULTADO nao e keyword RES, e sim MEM_ID."""
        tokens = tokenizar("RESULTADO")
        self.assertEqual(tokens[0], {"tipo": "MEM_ID", "valor": "RESULTADO"})

    def test_res_no_meio_de_expressao(self):
        tokens = tokenizar("(1 RES)")
        tipos = [t["tipo"] for t in tokens]
        self.assertIn("KEYWORD_RES", tipos)


class TestTokenizarExpressoesCompletas(unittest.TestCase):
    """Testes de expressoes RPN completas com multiplos tokens."""

    def test_soma_inteiros(self):
        tokens = tokenizar("(10 5 +)")
        self.assertEqual(len(tokens), 5)
        self.assertEqual(tokens[0]["tipo"], "ABRE_PAREN")
        self.assertEqual(tokens[1], {"tipo": "NUMERO", "valor": "10"})
        self.assertEqual(tokens[2], {"tipo": "NUMERO", "valor": "5"})
        self.assertEqual(tokens[3], {"tipo": "OPERADOR", "valor": "+"})
        self.assertEqual(tokens[4]["tipo"], "FECHA_PAREN")

    def test_subtracao_decimal(self):
        tokens = tokenizar("(20 4.3 -)")
        self.assertEqual(tokens[1], {"tipo": "NUMERO", "valor": "20"})
        self.assertEqual(tokens[2], {"tipo": "NUMERO", "valor": "4.3"})
        self.assertEqual(tokens[3], {"tipo": "OPERADOR", "valor": "-"})

    def test_divisao_inteira_em_expressao(self):
        tokens = tokenizar("(17 5 //)")
        self.assertEqual(tokens[3], {"tipo": "OPERADOR_INT_DIV", "valor": "//"})

    def test_expressao_aninhada(self):
        tokens = tokenizar("((3 4 +) (2 5 *) -)")
        tipos = [t["tipo"] for t in tokens]
        self.assertEqual(tipos.count("ABRE_PAREN"), 3)
        self.assertEqual(tipos.count("FECHA_PAREN"), 3)

    def test_memoria_store(self):
        tokens = tokenizar("(15.75 MA)")
        self.assertEqual(tokens[1], {"tipo": "NUMERO", "valor": "15.75"})
        self.assertEqual(tokens[2], {"tipo": "MEM_ID", "valor": "MA"})

    def test_expressao_com_res(self):
        tokens = tokenizar("(1 RES 2 RES +)")
        tipos = [t["tipo"] for t in tokens]
        self.assertEqual(tipos.count("KEYWORD_RES"), 2)

    def test_todos_operadores_em_sequencia(self):
        """Verifica que todos os 7 operadores sao reconhecidos."""
        tokens = tokenizar("+ - * / // % ^")
        ops = [t["valor"] for t in tokens]
        self.assertEqual(ops, ["+", "-", "*", "/", "//", "%", "^"])


class TestTokenizarErros(unittest.TestCase):
    """Testes de deteccao de erros lexicos."""

    def test_caractere_hash(self):
        with self.assertRaises(LexerError):
            tokenizar("erro#invalido")

    def test_caractere_arroba(self):
        with self.assertRaises(LexerError):
            tokenizar("d@do")

    def test_caractere_exclamacao(self):
        with self.assertRaises(LexerError):
            tokenizar("val!")

    def test_caractere_cifrao(self):
        with self.assertRaises(LexerError):
            tokenizar("val$invalido")

    def test_letra_minuscula(self):
        with self.assertRaises(LexerError):
            tokenizar("abc")

    def test_caractere_e_comercial(self):
        with self.assertRaises(LexerError):
            tokenizar("&")

    def test_mistura_valido_invalido(self):
        with self.assertRaises(LexerError):
            tokenizar("(10 5 &)")


class TestTokenizarEspacos(unittest.TestCase):
    """Testes de tratamento de espacos e tabulacoes."""

    def test_espacos_multiplos(self):
        tokens = tokenizar("(  10   5   +  )")
        nums = [t for t in tokens if t["tipo"] == "NUMERO"]
        self.assertEqual(len(nums), 2)

    def test_tabulacao(self):
        tokens = tokenizar("(\t10\t5\t+\t)")
        nums = [t for t in tokens if t["tipo"] == "NUMERO"]
        self.assertEqual(len(nums), 2)

    def test_linha_so_espacos(self):
        tokens = tokenizar("   ")
        self.assertEqual(tokens, [])

    def test_linha_vazia(self):
        tokens = tokenizar("")
        self.assertEqual(tokens, [])


class TestTokenizarCasosLimite(unittest.TestCase):
    """Testes de casos-limite do AFD."""

    def test_numero_seguido_de_parentese(self):
        """'(5)' — numero seguido imediatamente de fecha parentese."""
        tokens = tokenizar("(5)")
        self.assertEqual(tokens[1], {"tipo": "NUMERO", "valor": "5"})

    def test_operador_colado_no_parentese(self):
        tokens = tokenizar("(10 5+)")
        # O '5' deve ser reconhecido como numero e '+' como operador
        vals = [t["valor"] for t in tokens]
        self.assertIn("5", vals)
        self.assertIn("+", vals)

    def test_identificador_colado_no_parentese(self):
        tokens = tokenizar("(MA)")
        self.assertEqual(tokens[1], {"tipo": "MEM_ID", "valor": "MA"})

    def test_muitos_tokens(self):
        """Expressao longa com muitos tokens."""
        tokens = tokenizar("((1 2 +) (3 4 *) (5 6 /) + -)")
        self.assertTrue(len(tokens) > 10)


if __name__ == "__main__":
    unittest.main()
