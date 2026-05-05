import asyncio
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from errors import LeadScriptRuntimeError, LeadScriptSyntaxError
from main import executar_arquivo


TESTS_DIR = Path(__file__).resolve().parent


def executar(nome_arquivo):
    return asyncio.run(executar_arquivo(TESTS_DIR / nome_arquivo))


def test_script_de_sucesso_executa_sem_excecao(capsys):
    executar("test_sucesso.las")

    saida = capsys.readouterr().out
    assert "payload extraido" in saida
    assert "lead classificado com score" in saida
    assert "email para" in saida


def test_erro_de_sintaxe_informa_linha_coluna_e_mensagem():
    with pytest.raises(LeadScriptSyntaxError) as erro:
        executar("test_erro_sintaxe.las")

    mensagem = erro.value.format()
    assert "Erro de Sintaxe" in mensagem
    assert "test_erro_sintaxe.las" in mensagem
    assert "linha 4" in mensagem
    assert "Esperado 'entao:' apos a condicao." in mensagem
    assert "^" in mensagem


def test_erro_de_variavel_inexistente_vira_runtime_error_amigavel():
    with pytest.raises(LeadScriptRuntimeError) as erro:
        executar("test_erro_variavel.las")

    mensagem = erro.value.format()
    assert "Erro de Execucao" in mensagem
    assert "test_erro_variavel.las" in mensagem
    assert "linha 2" in mensagem
    assert "variavel_inexistente" in mensagem
    assert "^" in mensagem
