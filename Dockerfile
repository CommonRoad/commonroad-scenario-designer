# taken from commonroad-dataset-converters
FROM python:3.10 AS build

RUN pip install poetry
WORKDIR /app

COPY crtemplate /app/crtemplate
COPY pyproject.toml /app/
COPY README.md /app/

RUN poetry export -o requirements.txt --without-hashes
RUN poetry build -f wheel

# FROM python:3.10-slim AS app

# RUN apt-get update && apt-get install -y gcc cmake

# COPY --from=build /app/requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt && rm /app/requirements.txt

# ARG WHEEL_NAME="commonroad-template-2023.1-py3-non-any.whl"
# COPY --from=build /app/dist/${WHEEL_NAME} /app/
# RUN pip install /app/${WHEEL_NAME} && rm /app/${WHEEL_NAME}

ENTRYPOINT ["crtemplate"]
CMD ["--help"]
