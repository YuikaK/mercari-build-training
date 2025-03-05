FROM python:3.12-alpine

# setting working directory
WORKDIR /app

# sqlite package
RUN apk add --no-cache python3 py3-pip sqlite

# install library
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# copy the source code of app
COPY . .

EXPOSE 9000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]