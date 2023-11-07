FROM python:3.11

WORKDIR /app
RUN mkdir "media"
COPY ./requirements.txt /app/requirements.txt

COPY ./docker_install.sh /app/docker_install.sh
RUN apt update -y && apt install sudo -y
RUN ./docker_install.sh

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app


EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

