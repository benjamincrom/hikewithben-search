FROM benjamincrom/flask-numpy-redis:latest
MAINTAINER Benjamin Crom "benjamincrom@gmail.com"
COPY . /app
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["app.py"]
