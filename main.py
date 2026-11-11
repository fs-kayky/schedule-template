# Ponto de entrada: lê a configuração e mantém a fila de tarefas ativa.
import os
import sched
import time

from dotenv import load_dotenv
from functions.jobs.jobs import executar_job
from logger.logger import logger


def main():
    # Carrega o .env; variáveis já definidas no ambiente têm preferência.
    load_dotenv()
    # int rejeita texto/decimais; a validação abaixo rejeita zero e negativos.
    intervalo = int(os.getenv("SCHEDULE_INTERVAL_SECONDS", "21600"))
    if intervalo <= 0:
        raise ValueError("SCHEDULE_INTERVAL_SECONDS deve ser maior que zero.")

    # monotonic mede tempo decorrido sem depender de ajustes no relógio do sistema.
    # sleep aguarda os eventos sem manter um loop consumindo CPU continuamente.
    scheduler = sched.scheduler(time.monotonic, time.sleep)
    # A primeira execução acontece após o intervalo configurado.
    # enter(atraso, prioridade, função, argumentos): menor prioridade numérica vem antes.
    # Passamos a função sem parênteses para ela executar apenas no momento agendado.
    scheduler.enter(intervalo, 1, executar_job, argument=(scheduler, intervalo))
    logger.info("Schedule iniciada. Intervalo: %s segundos.", intervalo)
    try:
        # Bloqueia enquanto houver eventos; cada job adiciona sua próxima execução.
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Schedule encerrada.")


# Importar este módulo não inicia o agendamento; executar main.py inicia.
if __name__ == "__main__":
    main()
