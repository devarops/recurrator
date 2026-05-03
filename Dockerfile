FROM python:3
WORKDIR /workdir
COPY . .
RUN pip install --upgrade pip && pip install \
    black \
    fastapi \
    flake8 \
    mutmut \
    mypy \
    pylint \
    pytest \
    pytest-cov \
    requests \
    typer \
    uvicorn
