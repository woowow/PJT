FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
COPY .env .

CMD ["bash", "-c", "python merge_and_insert.py && python manage.py runserver 0.0.0.0:8000"]
