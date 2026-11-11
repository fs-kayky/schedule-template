# Logging padrão do Python, compartilhado entre o scheduler e os jobs.
import logging

# INFO mostra início, conclusão e reagendamento; exception também inclui traceback.
# O horário exibido segue o fuso do ambiente em que o processo está rodando.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
# Nome fixo para identificar os registros deste template.
logger = logging.getLogger("schedule-template")
