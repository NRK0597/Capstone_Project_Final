FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# MOCK_LLM is defaulted to 1 for fully offline graded path as mentioned in the requirement..
ENV MOCK_LLM=1

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
