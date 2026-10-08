# Nomus ERP para Codex

Conector MCP local para consultar e alterar o Nomus ERP pelo Codex, usando a API REST documentada. Funciona no Windows e disponibiliza quatro ferramentas ao assistente. As alterações atingem o ERP configurado e precisam ser solicitadas explicitamente pelo usuário.

## O que você precisa complementar

| Item | O que informar ou preparar | Onde configurar |
| --- | --- | --- |
| Ambiente | Windows, PowerShell e Python 3.10 ou superior; validado com Python 3.13 | No seu computador |
| Codex | Instalação autenticada com suporte a MCP local; CLI para o comando de cadastro abaixo | No seu computador |
| Acesso ao Nomus | API REST disponível e permissões para as operações desejadas | Confirme com o administrador do ERP |
| URL da API | URL HTTPS da sua instância, incluindo o contexto e terminando em `/rest` | O configurador pede esse endereço |
| Chave de integração | Chave da sua própria instância Nomus | Cole somente no campo oculto do configurador |
| Caminho do projeto | Caminho absoluto da pasta em que você instalou o conector | Cadastro MCP do Codex |
| Cadastros e regras | IDs, unidades, tipos de produto, campos obrigatórios e filtros da sua empresa | Consulte o ERP e a documentação antes de executar operações |

Não é necessário editar `nomus_server.py` para configurar outra empresa. O repositório contém o conector e um catálogo de operações públicas. Relatórios, planilhas, cadastros e configurações de uma empresa não fazem parte desta distribuição. Geração de Excel exige uma rotina própria; esse recurso não está implementado neste pacote.

## 1. Instalar

Clone este repositório ou extraia o ZIP e abra o PowerShell dentro da pasta que contém `nomus_server.py`. No caso de um repositório privado, sua conta GitHub precisa ter acesso para baixar.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se `python` não for encontrado, instale o Python com acesso pelo PATH ou use `py` nos dois primeiros comandos. Não é necessário ativar o ambiente virtual. A instalação precisa de acesso à internet para baixar as dependências.

## 2. Informar a URL e a chave da sua empresa

A API usa o endereço da instância com seu contexto e o sufixo `/rest`. Exemplo fictício:

```text
Login: https://sua-empresa.nomus.com.br/seu-contexto/Login.do?metodo=paginaInicial
API:   https://sua-empresa.nomus.com.br/seu-contexto/rest
```

Confirme o contexto e o endereço correto com o administrador. Não use a página de login como URL da API. Veja a [introdução oficial à API Nomus](https://atendimento.nomus.com.br/hc/pt-br/articles/35195281009819-Introdu%C3%A7%C3%A3o-%C3%A0-integra%C3%A7%C3%A3o-com-API-REST).

No Nomus, a chave está em **Configuração Geral**, no campo **Chave de acesso para integração com o ERP via REST**. Se não puder visualizar o campo, peça ao administrador para verificar seu acesso. A chave de integração é diferente da senha de login e de uma chave da OpenAI.

Execute:

```powershell
powershell.exe -NoProfile -File .\configurar-chave.ps1
```

Primeiro informe a URL da API. Depois cole a chave no próprio terminal, quando aparecer `Chave de integracao`, e pressione Enter. Esse campo oculta os caracteres. Não cole a chave no chat, no código, em comandos ou no GitHub. O conector monta a autenticação; não converta a chave novamente para Base64.

O configurador cria dois arquivos locais, excluídos pelo `.gitignore`:

- `nomus.local.json`: endereço da API.
- `.secrets/nomus-key.dpapi`: chave criptografada pelo Windows para o usuário e computador atuais.

Execute o configurador novamente para trocar a chave ou a empresa. Em outro computador ou usuário Windows, configure uma nova cópia; não transporte o arquivo criptografado esperando que ele funcione.

## 3. Conferir a configuração local

```powershell
powershell.exe -NoProfile -File .\iniciar-nomus.ps1 -Diagnostico
```

Confira `base_url`, `chave_configurada: true` e `operacoes_documentadas`. O diagnóstico não faz chamadas ao ERP: ele confirma a configuração local, mas não valida a chave ou a permissão de acesso.

## 4. Conectar ao Codex

Com a CLI `codex` disponível, execute na pasta do projeto:

```powershell
$nomusLauncher = (Resolve-Path .\iniciar-nomus.ps1).Path
codex mcp add nomus_erp -- powershell.exe -NoProfile -File "$nomusLauncher"
codex mcp list
```

Reabra o Codex ou inicie uma nova sessão para carregar o servidor. Na CLI, `/mcp` mostra os servidores ativos. O cadastro utiliza apenas o caminho do inicializador; a chave é carregada localmente quando o processo inicia.

Se preferir a configuração manual, adapte [examples/codex.example.toml](examples/codex.example.toml) no arquivo de configuração do Codex, substituindo `C:\CAMINHO\nomus-codex\iniciar-nomus.ps1` pelo caminho absoluto real. Preserve as outras configurações já existentes. A documentação descreve a configuração global e por projeto: [MCP no Codex](https://developers.openai.com/codex/mcp/).

## 5. Fazer a primeira consulta

Peça ao Codex:

> Use nomus_status para conferir a configuração. Depois use nomus_consultar com caminho produtos e pagina 1. Mostre apenas se a consulta funcionou e quantos registros essa página retornou.

Uma resposta HTTP 200 com JSON confirma o acesso daquela consulta. Uma lista vazia pode ser válida. Uma página não representa necessariamente todos os produtos. A primeira consulta acessa dados reais; os resultados retornados pelas ferramentas entram no contexto do Codex. Escolha somente os dados necessários para a tarefa.

## Ferramentas e limites

| Ferramenta | Função |
| --- | --- |
| `nomus_status` | Verifica a configuração local, sem consultar o ERP ou revelar a chave |
| `nomus_catalogo` | Busca nomes, métodos e caminhos disponíveis no catálogo público |
| `nomus_consultar` | Faz GET em um caminho documentado, com `pagina` e `filtro` opcionais |
| `nomus_executar` | Faz POST, PUT ou DELETE no ERP real, com os dados da operação |

O catálogo contém 189 operações documentadas. Não inclui esquemas completos nem exemplos de dados empresariais. Confira campos obrigatórios, filtros e regras na [documentação da API](https://documenter.getpostman.com/view/22813773/2s93JutNgM) e na sua versão do Nomus. Um caminho como `saldosEstoqueProduto/ID` exige o ID interno real, não necessariamente o SKU. Não reutilize IDs de outra empresa.

Cada consulta retorna uma página. Relatórios completos precisam percorrer as páginas pertinentes, registrar falhas e distinguir resultados parciais. Algumas operações documentadas podem não estar disponíveis na instância utilizada. Arquivos binários não são suportados por este conector JSON.

Criações, alterações e exclusões são reais, sem simulação ou desfazer automático. As instruções MCP orientam o assistente a alterar somente quando solicitado; elas não substituem permissões no ERP e no cliente MCP. Após timeout ou resultado incerto de uma gravação, consulte o ERP antes de repetir. O conector não repete gravações automaticamente, não segue redirecionamentos e rejeita caminhos fora do catálogo.

## Resolver problemas

| Sintoma | Verificação |
| --- | --- |
| Python ausente ou versão incompatível | Instale Python 3.10+ e recrie `.venv` |
| `No module named mcp` ou `httpx` | Instale `requirements.txt` usando o Python de `.venv` |
| Scripts bloqueados pelo PowerShell | Consulte a política do seu ambiente; para uma sessão pessoal autorizada, use `Set-ExecutionPolicy -Scope Process RemoteSigned` e tente novamente; políticas da organização podem prevalecer |
| Falha ao ler a chave criptografada | Execute `configurar-chave.ps1` com o mesmo usuário Windows que executa o Codex |
| Chave ausente | Execute o configurador e confira o diagnóstico |
| HTTP 401 ou 403 | Confirme a chave, a instância e as permissões da API com o administrador |
| HTTP 400 | Verifique os campos, o filtro e as regras da operação na documentação |
| HTTP 404, redirecionamento ou resposta sem JSON | Confira a URL REST, o contexto, o caminho e a disponibilidade da operação |
| HTTP 429 | Aguarde antes de fazer novas consultas |
| Falha de comunicação | Verifique internet, VPN, proxy, certificado e disponibilidade do Nomus |
| Servidor não aparece no Codex | Confira o caminho absoluto do inicializador, o cadastro MCP e reabra a sessão |

## Testar sem acessar o ERP

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam credenciais fictícias e respostas HTTP simuladas. Também verificam a comunicação MCP por stdio. Não precisam da chave real. Passar nos testes não confirma as permissões ou a compatibilidade de cada operação na sua empresa.

## Configuração por ambiente

Para uso avançado, `nomus_server.py` aceita `NOMUS_BASE_URL` e `NOMUS_API_KEY` no ambiente do processo. Forneça a chave por um mecanismo seguro da sua infraestrutura. O projeto não carrega arquivos `.env` automaticamente. No inicializador PowerShell, arquivos locais existentes têm prioridade sobre essas variáveis; ele remove a chave do ambiente ao encerrar.

## Cuidados ao publicar mudanças

Publique somente arquivos revisados. O `.gitignore` exclui credenciais, configurações locais, ambientes virtuais, relatórios e formatos comuns de exportação. Ele não protege arquivos já rastreados nem uploads manuais pelo navegador. Novos arquivos JSON ou textos com dados operacionais também precisam de revisão.

Antes de cada commit, confira `git status`, `git diff --cached --name-only` e `git diff --cached`. Adicione arquivos específicos. Não envie resultados da API, logs, planilhas, capturas de tela com dados privados ou chaves, mesmo criptografadas. Use repositório privado para trabalho interno.
