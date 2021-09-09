FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /app
RUN git clone https://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@github.com/youhs4554/neural_riskistic.git
WORKDIR /app/neural_riskistic
RUN git checkout 62a839ef99c5999dad6328ed993eed68d2c3bde3
WORKDIR /app/neural_riskistic/demo
RUN pip install -r requirements.txt