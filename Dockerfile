FROM python:3.8

COPY requirements.txt /snake/requirements.txt
WORKDIR /snake
RUN pip install -r requirements.txt

COPY . /snake
EXPOSE 8080

ENTRYPOINT ["python", "app/main.py"]