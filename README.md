# LeadScript

LeadScript e uma DSL com extensao `.las` para automacao assincrona de leads.
Ela foi criada para expressar regras de qualificacao, notificacao e envio de
leads em massa com uma sintaxe pequena, legivel e orientada ao dominio.

O motor segue uma arquitetura classica de compiladores e interpretadores:

```text
Arquivo .las
   -> Lexer (lexico.py)
   -> Parser recursive descent (parser_1.py)
   -> AST (ast_nodes.py)
   -> Interpretador assincrono asyncio (interpreter.py)
   -> Runner CLI (cli.py)
```

A implementacao atual nao usa Lark. O parser e escrito manualmente por descida
recursiva para manter o projeto didatico, previsivel e facil de evoluir.

## Requisitos

- Python 3.10 ou superior
- `pytest` para rodar testes
- `pyinstaller` para gerar o executavel

Instalacao das ferramentas de desenvolvimento:

```bash
python -m pip install pytest pyinstaller
```

## Como executar em modo desenvolvimento

Com o Python:

```bash
python main.py caminho/para/campanha.las
```

Com a CLI oficial:

```bash
python cli.py rodar caminho/para/campanha.las
```

A CLI aceita caminhos relativos e absolutos. Internamente, o runner resolve o
caminho a partir do diretorio atual antes de ler o arquivo.

## Como gerar o executavel

Use o script de build:

```bash
python build_runner.py
```

Ele executa o PyInstaller com `--onefile`, nomeia o binario como `leadscript` e
inclui explicitamente `asyncio` como import oculto:

```bash
python -m PyInstaller --onefile --name leadscript --clean --hidden-import asyncio cli.py
```

Saida esperada:

```text
dist/leadscript.exe    # Windows
dist/leadscript        # Linux/Mac
```

Uso do binario:

```bash
dist\leadscript.exe rodar campanha.las
```

ou:

```bash
./dist/leadscript rodar campanha.las
```

## Sintaxe da Linguagem

### Variaveis

Variaveis sao criadas por atribuicao direta:

```text
lead = extrair_payload()
score = 92
nome = "Ana Silva"
ativo = verdadeiro
```

### Tipos de dados

```text
inteiro = 10
decimal = 10.5
texto = "Lead aprovado"
booleano = verdadeiro
lista = ["B2B", "Enterprise", "Inbound"]
lead = {"email": "ana@empresa.com", segmento: "B2B"}
vazio = nulo
```

### Acesso a propriedades

Dicionarios podem ser acessados por chave ou por ponto:

```text
email = lead["email"]
segmento = lead.segmento
```

### Operadores

Aritmeticos:

```text
+  -  *  /  %
```

Comparacao:

```text
==  !=  >  <  >=  <=
```

Logicos:

```text
e  ou  nao
```

Tambem sao aceitos `&&`, `||` e `!`.

### Condicional

```text
se score > 80 entao:
    enviar_email(lead["email"], "Bem-vindo", "boas_vindas.html")
senao:
    enviar_discord("https://discord.com/api/webhooks/...", "Lead desqualificado")
fim
```

### Repeticao

```text
leads = [
    {"email": "a@empresa.com", segmento: "B2B"},
    {"email": "b@empresa.com", segmento: "B2C"}
]

para cada lead em leads entao:
    enviar_discord("https://discord.com/api/webhooks/...", lead["email"])
fim
```

### Comentarios

```text
# comentario
// comentario
~~ comentario
```

## Exemplo completo

```text
lead = extrair_payload()
score = classificar_ia(lead, "Validar se o lead e B2B")

se score > 80 entao:
    disparar_webhook("https://api.meusistema.com", lead)
    enviar_email(lead["email"], "Bem-vindo", "boas_vindas.html")
senao:
    enviar_discord("https://discord.com/api/webhooks/...", "Lead desqualificado")
fim
```

## Funcoes nativas

### `extrair_payload()`

Simula a coleta de dados recebidos por webhook.

Retorno:

```text
dicionario com dados do lead
```

### `classificar_ia(lead, prompt)`

Simula uma chamada assincrona para classificacao por IA.

Parametros:

- `lead`: dicionario com os dados do lead
- `prompt`: instrucao textual para avaliacao

Retorno:

```text
numero inteiro representando o score do lead
```

### `disparar_webhook(url, lead)`

Simula um POST assincrono para outro sistema.

Parametros:

- `url`: endpoint de destino
- `lead`: dicionario com dados do lead

Retorno:

```text
dicionario com status da operacao
```

### `enviar_email(para, assunto, template)`

Simula envio assincrono de e-mail.

Parametros:

- `para`: endereco de e-mail do destinatario
- `assunto`: assunto da mensagem
- `template`: nome do template usado

Retorno:

```text
dicionario com status da operacao
```

### `enviar_discord(url, mensagem)`

Simula envio assincrono de notificacao para Discord.

Parametros:

- `url`: webhook do Discord
- `mensagem`: conteudo enviado

Retorno:

```text
dicionario com status da notificacao
```

## Tratamento de erros

LeadScript exibe erros com arquivo, linha, coluna, trecho de codigo e ponteiro:

```text
Erro de Sintaxe no arquivo 'campanha.las' na linha 4, coluna 14:
    se score > 80
                 ^
    Esperado 'entao:' apos a condicao.
```

Os erros principais sao:

- `LeadScriptLexicalError`: caracteres invalidos ou strings mal formadas
- `LeadScriptSyntaxError`: comandos ou expressoes invalidas
- `LeadScriptRuntimeError`: variaveis inexistentes, acessos invalidos e falhas de funcao nativa

## Testes

A suite de testes fica em `tests/` e cobre sucesso, erro de sintaxe e erro de
variavel inexistente.

Execute:

```bash
python -m pytest tests
```

Arquivos de exemplo:

- `tests/test_sucesso.las`
- `tests/test_erro_sintaxe.las`
- `tests/test_erro_variavel.las`

## Estrutura principal

```text
lexico.py          Lexer e tokens
parser_1.py        Parser recursive descent
ast_nodes.py       Nos da AST com linha/coluna
interpreter.py     Motor assincrono e funcoes nativas
main.py            API de execucao do motor
cli.py             Runner de linha de comando
build_runner.py    Build onefile com PyInstaller
errors.py          Erros customizados e formatacao amigavel
tests/             Suite pytest e scripts .las
```
