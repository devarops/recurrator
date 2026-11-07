FROM python:3
WORKDIR /workdir
COPY . .
RUN chmod +x src/*.sh
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt update && apt install --yes \
    jq
RUN pip install --upgrade pip && pip install \
    fastapi \
    requests \
    typer \
    uvicorn
# Editable on purpose: src/entrypoint.sh writes the generated modules into
# /workdir/recurrator at container start, and only an editable install makes
# them visible to the import. A wheel would freeze site-packages instead.
RUN pip install --editable .

ENTRYPOINT ["/workdir/src/entrypoint.sh"]
