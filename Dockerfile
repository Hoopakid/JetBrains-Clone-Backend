FROM python:3.9-alpine

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apk add --no-cache bash
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
