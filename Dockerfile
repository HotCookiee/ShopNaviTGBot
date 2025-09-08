FROM python:3.13.3

ENV PYTHONUNBUFFERED=1

LABEL authors="HootCookes"
WORKDIR /app
COPY packages.txt .
RUN pip install -r packages.txt

COPY . .

CMD ["python", "main.py"]