FROM python:3
WORKDIR /workdir
COPY . .
RUN chmod +x src/*.sh
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
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

ENTRYPOINT ["/workdir/src/entrypoint.sh"]
