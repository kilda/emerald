FROM python:3.8-alpine
RUN pip install supervisor
RUN apk add libstdc++
WORKDIR /opt
RUN wget https://unofficial-builds.nodejs.org/download/release/v16.16.0/node-v16.16.0-linux-x64-musl.tar.gz
RUN mkdir -p /opt/nodejs
RUN tar -zxvf *.tar.gz --directory /opt/nodejs --strip-components=1
RUN rm *.tar.gz
RUN ln -s /opt/nodejs/bin/node /usr/local/bin/node
RUN ln -s /opt/nodejs/bin/npm /usr/local/bin/npm
WORKDIR /
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
EXPOSE 1090
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]