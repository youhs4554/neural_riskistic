FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /app
RUN set -x && \
    apt update && \
    apt install -y --no-install-recommends \
    libopencv-dev git wget
RUN git clone https://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@github.com/youhs4554/neural_riskistic.git
WORKDIR /app/neural_riskistic/demo
RUN git fetch && git checkout dc2167130895723fb1bfef86eb3717f172e6e5a2
RUN pip install -r requirements.txt
CMD python run.py --room ${ROOM_NUMBER} --model ${MODEL_NAME}