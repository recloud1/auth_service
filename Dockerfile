FROM python:3.10

RUN mkdir -p /var/app

ENV APP_HOME=/var/app
WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.2.0

RUN pip install "poetry==$POETRY_VERSION"


RUN apt-get update  \
    && apt-get install -y --no-install-recommends  \
       curl \
    && pip install --upgrade --no-cache-dir poetry==$POETRY_VERSION \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./pyproject.toml ./poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY . .

CMD ["python", "app/run.py"]
