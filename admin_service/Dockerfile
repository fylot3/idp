FROM python:3.6
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
COPY /app /_app
WORKDIR /_app
EXPOSE 8060
CMD ["python", "main.py"]