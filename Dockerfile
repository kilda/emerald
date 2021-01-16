FROM python:3.8-alpine
RUN pip install supervisor
RUN apk add make gcc musl-dev g++ python3-dev linux-headers zeromq-dev npm
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY backend/requirements.txt /
RUN pip install -r requirements.txt
RUN mkdir /app
COPY backend/watch/api.py /app/
COPY backend/watch/app.py /app/
COPY backend/watch/__init__.py /app/

COPY frontend/emerald-ui /app/emerald-ui
WORKDIR /app/emerald-ui
RUN npm install
RUN npm run-script build
RUN cp -r /app/emerald-ui/build /app
EXPOSE 8080
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]