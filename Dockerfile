FROM python:3.9.5
COPY requirements.txt /tmp/requirements.txt
RUN ["pip", "install", "-r", "/tmp/requirements.txt"]
EXPOSE 8010
CMD ["python","main.py"]