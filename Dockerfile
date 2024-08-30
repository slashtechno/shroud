FROM python:3.12

RUN pip install poetry

WORKDIR /app

COPY . .

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "-m", "shroud"]