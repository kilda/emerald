FROM python:3.8-alpine
RUN pip install supervisor
RUN apk add make gcc musl-dev g++ python3-dev linux-headers zeromq-dev
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY backend/requirements.txt /
RUN pip install -r requirements.txt
RUN mkdir /app
COPY backend/watch/* /app/
EXPOSE 8080
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]