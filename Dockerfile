FROM python:3.9.5
COPY requirements.txt /tmp/requirements.txt
RUN ["pip", "install", "-r", "/tmp/requirements.txt",">","/dev/null","2>&1"]
EXPOSE 8080
CMD ["python","main.py"]