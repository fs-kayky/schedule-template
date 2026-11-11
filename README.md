# schedule-template

Template de agendamento em Python com um job vazio, logs e managers genéricos de PostgreSQL e SQL Server. Você adiciona as funções e consultas conforme precisar. Iniciar o template não acessa bancos de dados.

## O que é uma schedule?

Uma schedule define quando uma tarefa deve ser executada. O **scheduler** é o componente que guarda os eventos na fila, espera o momento certo e chama a função agendada. O **job** é a unidade de execução; neste projeto, ele chama sua tarefa e cuida dos logs e do próximo agendamento.

Este template usa `sched`, da biblioteca padrão do Python, com repetição por intervalo. Não há horário fixo de calendário: o padrão é esperar 6 horas, executar e esperar mais 6 horas após terminar.

## Como o ciclo funciona

```text
python main.py
    |
    v
Carregar .env e validar o intervalo
    |
    v
Criar scheduler e agendar a primeira execução
    |
    v
Esperar o intervalo configurado <------------------+
    |                                             |
    v                                             |
executar_job() -> tarefa()                         |
    |                                             |
    +-- sucesso: registrar conclusão               |
    +-- erro: registrar erro e traceback           |
    |                                             |
    v                                             |
finally -> reagendar_tarefa() ---------------------+
```

1. `main()` carrega as configurações. O intervalo precisa ser um número inteiro maior que zero.
2. `sched.scheduler(time.monotonic, time.sleep)` cria a fila. `monotonic` mede tempo decorrido sem depender de mudanças no relógio; `sleep` permite aguardar os eventos.
3. `scheduler.enter(intervalo, 1, executar_job, argument=(scheduler, intervalo))` adiciona um evento. Os argumentos são atraso em segundos, prioridade, função e parâmetros da função. Menor número de prioridade vem primeiro quando eventos têm o mesmo instante agendado.
4. `scheduler.run()` mantém o processo esperando e executando os eventos. Ele retorna quando a fila fica vazia; neste template o job normalmente mantém a fila preenchida ao se reagendar.
5. `executar_job()` chama `tarefa()`. É dentro de `tarefa()` que você adiciona sua lógica.
6. O bloco `except Exception` registra falhas comuns. O bloco `finally` agenda a próxima execução tanto no sucesso quanto na falha. Não há retry imediato nem recuperação automática de operações parcialmente concluídas.

**Exemplo:** com intervalo de 60 segundos, se o processo iniciar às 10:00:00, a primeira tarefa começa aproximadamente às 10:01:00. Se durar 10 segundos, a próxima começa aproximadamente às 10:02:10. O tempo da tarefa faz parte do ciclo: duração + intervalo.

## Estrutura do projeto

```text
main.py                                      Entrada e configuração do scheduler
functions/
  jobs/jobs.py                               Tarefa, execução e reagendamento
  database/
    base_manager.py                          Operações e transações compartilhadas
    postgresql/psycopg_manager.py             Conexão PostgreSQL
    sqlserver/pyodbc_manager.py               Conexão SQL Server
logger/logger.py                             Formato e nível dos logs
.env.example                                 Modelo das variáveis de ambiente
requirements.txt                             Dependências Python
Dockerfile                                   Construção da imagem
.dockerignore                                Arquivos excluídos da imagem
docker-compose.yml                          Configuração do serviço Docker
```

Os arquivos `__init__.py` vazios identificam os pacotes Python; não precisam de lógica para este template.

## Executar localmente

Requer Python 3.12 ou superior. No PowerShell, entre na pasta do projeto e execute:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Copie `.env.example` apenas na primeira configuração para não substituir ajustes de um `.env` existente. Para um teste rápido, defina `SCHEDULE_INTERVAL_SECONDS=5` antes de iniciar. O job vazio apenas escreve logs. Use Ctrl+C para encerrar.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `SCHEDULE_INTERVAL_SECONDS` | `21600` | Espera em segundos antes da primeira execução e entre o fim de uma tarefa e a próxima |
| `CONN_STR_POSTGRESQL` | Vazia | String de conexão, necessária somente se usar PostgreSQL |
| `CONN_STR_SQLSERVER` | Vazia | String de conexão ODBC, necessária somente se usar SQL Server |

O `.env` é carregado no início. Variáveis já definidas no ambiente têm preferência. Reinicie o processo após alterar a configuração. Não coloque credenciais no código; `.env` está ignorado pelo Git e excluído da imagem Docker.

## Adicionar sua tarefa

Substitua o `pass` em `functions/jobs/jobs.py` pelas chamadas desejadas. Exemplo sem banco de dados:

```python
def minha_funcao():
    logger.info("Executando minha função.")


def tarefa():
    minha_funcao()
```

Você pode criar módulos dentro de `functions/` e importar suas funções em `jobs.py`. As chamadas dentro de `tarefa()` executam em sequência. Se uma falhar e propagar uma exceção, as chamadas seguintes daquele ciclo não executam; o job registra a falha e agenda outro ciclo.

Para executar a primeira tarefa imediatamente, altere **somente o primeiro** `scheduler.enter` em `main.py` para usar atraso `0`. Mantenha o intervalo em `reagendar_tarefa()` para as repetições.

Para tarefas com intervalos independentes, crie callbacks próprios e agende cada um na mesma fila; cada callback deve reagendar a si próprio. O template atual tem apenas uma tarefa recorrente. Não agende `tarefa()` diretamente esperando repetição automática: quem implementa a repetição é `executar_job()`.

## Como funcionam os managers

Um manager reúne as operações de acesso a banco. `PsycopgManager` e `PyodbcManager` herdam as operações de `DatabaseManager` e implementam apenas a conexão com o driver correspondente.

| Método | Responsabilidade | Retorno |
| --- | --- | --- |
| `connect()` | Abrir uma conexão usando a string explícita ou a variável de ambiente | Conexão do driver |
| `disconnect(conn)` | Fechar uma conexão existente | Nenhum |
| `session()` | Gerenciar cursor, transação e fechamento em um bloco `with` | Cursor dentro do bloco |
| `fetch_all(query, params=())` | Executar uma consulta com resultado | Lista de dicionários; `[]` se não houver linhas |
| `execute(query, params=())` | Executar uma instrução | `rowcount` do driver |
| `execute_many(query, rows)` | Repetir uma instrução para várias sequências de parâmetros | `rowcount` do driver |

Cada operação abre uma conexão e um cursor. Ao terminar, confirma a transação com `commit`; se ocorrer erro, tenta desfazê-la com `rollback` e propaga a exceção. Por fim, fecha cursor e conexão. Uma falha na abertura da conexão também é propagada ao chamador.

Chamadas separadas de `execute()` são transações separadas. Para agrupar operações em uma única transação, use `with manager.session() as cursor:` e execute as instruções pelo mesmo cursor. O rollback não desfaz chamadas já confirmadas em outras transações nem efeitos externos, como envio de arquivos.

As instâncias prontas para importação são:

```python
from functions.database.postgresql.psycopg_manager import psycopg_manager
from functions.database.sqlserver.pyodbc_manager import pyodbc_manager
```

Importar essas instâncias não abre conexões. Os drivers são importados somente em `connect()`. As consultas devem ser criadas por você e passadas aos métodos; não há SQL de negócio embutido no template.

- Passe valores separadamente em `params`, usando `%s` no PostgreSQL e `?` no SQL Server. Não use f-strings para inserir valores em queries.
- Placeholders representam valores, não nomes de tabelas ou colunas.
- Use nomes ou aliases únicos nas colunas de consultas para evitar chaves duplicadas em `fetch_all()`.
- `rowcount` depende do driver e pode ser `-1` quando a contagem não estiver disponível; não é uma confirmação universal de quantas linhas mudaram.
- Para SQL Server local, instale o driver ODBC indicado na sua string de conexão. A imagem Docker instala o Microsoft ODBC Driver 18.
- Se usar os managers em outro script, carregue o `.env` nesse script ou configure as variáveis no ambiente antes da conexão.

## Logs e falhas

O logger usa nível `INFO` e registra horário, nível, nome e mensagem. O horário dos logs segue o fuso do ambiente; o agendamento por intervalo usa o relógio monotônico e não depende desse fuso.

`logger.info()` registra o andamento; `logger.exception()` dentro do tratamento de erros inclui o traceback. Os logs vão para a saída padrão de erros do processo e aparecem no terminal ou em `docker compose logs`. Não existe arquivo de log configurado.

Erros de configuração no início encerram o programa. Erros comuns dentro da tarefa são registrados e permitem novo ciclo. Ctrl+C interrompe o processo; embora o `finally` possa adicionar um evento antes da saída, ele não será executado depois que o processo terminar.

## Executar com Docker

```sh
docker compose up --build -d
docker compose logs -f
# Parar e remover o container do serviço:
docker compose down
```

O Dockerfile instala as dependências e o driver ODBC, copia o projeto e inicia `main.py`. O `.dockerignore` impede que `.env`, Git e caches entrem na imagem. O Compose lê as variáveis e as passa para o container; não é necessário copiar o `.env` para dentro dele.

`restart: unless-stopped` reinicia o container após encerramentos, salvo quando parado explicitamente. Isso não recupera a fila anterior: cada reinício começa uma nova espera inicial. Não há deploy automático nem dependência de rede externa neste template.

## Limites deste template

- A fila existe somente na memória. Reiniciar perde os agendamentos anteriores; tarefas perdidas enquanto o processo estava desligado não são recuperadas.
- A execução é sequencial. Uma tarefa longa atrasa outros eventos na mesma fila; não há paralelismo automático.
- Cada processo ou container tem sua própria fila. Duas instâncias executam a mesma tarefa duas vezes; não há trava distribuída.
- Não há persistência de resultados, timeout, retry com backoff ou garantia de execução única.
- Um intervalo não representa um horário fixo como “todos os dias às 08:00”. Essa modalidade exige outro cálculo de agendamento.
- Ao adicionar escritas ou efeitos externos, considere como sua função se comporta se for executada novamente após uma falha parcial.
