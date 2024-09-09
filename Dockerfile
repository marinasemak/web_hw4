# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.12-slim

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

COPY pyproject.toml $APP_HOME/pyproject.toml

# Скопіюємо інші файли в робочу директорію контейнера
COPY . /app

VOLUME ["/app"]

# Встановимо залежності усередині контейнера
RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install --only main

# Запустимо наш застосунок всередині контейнера
CMD ["python", "main.py"]
