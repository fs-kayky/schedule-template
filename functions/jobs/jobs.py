# A lógica da tarefa fica separada do controle de execução e repetição.
from logger.logger import logger


def tarefa():
    """Adicione aqui as chamadas às suas funções e aos managers."""
    # Substitua pass pelas chamadas que deseja executar a cada ciclo.
    # O template funciona vazio e não abre conexões com bancos.
    pass


def executar_job(scheduler, intervalo):
    """Executa a tarefa e agenda a próxima execução, mesmo após uma falha."""
    try:
        logger.info("Iniciando tarefa.")
        tarefa()
        logger.info("Tarefa concluída.")
    # Registra a falha e o traceback para diagnóstico, sem encerrar a schedule.
    except Exception:
        logger.exception("Falha ao executar tarefa.")
    # Tanto sucesso quanto erro chegam aqui; não há tentativa imediata adicional.
    finally:
        reagendar_tarefa(scheduler, intervalo)


def reagendar_tarefa(scheduler, intervalo):
    """Conta o intervalo a partir do fim da execução anterior."""
    # Agenda somente depois da tarefa terminar: duração do job + intervalo por ciclo.
    scheduler.enter(intervalo, 1, executar_job, argument=(scheduler, intervalo))
    logger.info("Próxima execução em %s segundos.", intervalo)
