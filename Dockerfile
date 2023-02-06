FROM python:3.9.5
COPY requirements.txt /tmp/requirements.txt
RUN ["pip", "install", "-r", "/tmp/requirements.txt"]
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]