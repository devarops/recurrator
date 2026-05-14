FROM python:3
WORKDIR /workdir
COPY . .
RUN apt update && apt install --yes \
    jq
RUN pip install --upgrade pip && pip install \
    black \
    fastapi \
    flake8 \
    frictionless \
    httpx \
    mutmut \
    mypy \
    pylint \
    pytest \
    pytest-cov \
    requests \
    typer \
    uvicorn
