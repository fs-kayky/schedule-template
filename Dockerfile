# Base Python em Debian Bookworm.
FROM python:3.12-slim-bookworm

# Envia logs imediatamente para a saída do container.
ENV PYTHONUNBUFFERED=1

# Driver usado apenas se você adicionar tarefas com SQL Server.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates unixodbc \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -f /tmp/packages-microsoft-prod.deb \
    && rm -rf /var/lib/apt/lists/*

# Diretório de execução dentro da imagem.
WORKDIR /app
# Instala dependências antes do código para aproveitar o cache de build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copia apenas arquivos permitidos pelo .dockerignore.
COPY . .
# Inicia o mesmo ponto de entrada usado na execução local.
CMD ["python", "main.py"]
