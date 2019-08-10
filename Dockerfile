# ---- Base ----
# ---- Python ----
FROM python:3 AS build
MAINTAINER "DeltaML dev@deltaml.com"
COPY requirements.txt .
# install app dependencies
RUN pip install  --user -r requirements.txt

FROM python:stretch AS release
WORKDIR /app
COPY --from=build /root/.local /root/.local
ADD /model_buyer /app/model_buyer
RUN mkdir -p /app/db
ENV PATH=/root/.local/bin:$PAT
ENV ENV_PROD=1
EXPOSE 9090
CMD [ "gunicorn", "-b", "0.0.0.0:9090", "wsgi:app", "--chdir", "model_buyer/", "--preload"]
