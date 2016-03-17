FROM benjamincrom/dockerimage_flask_numpy_redis:latest
MAINTAINER Benjamin Crom "benjamincrom@gmail.com"
COPY . /app
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["app.py"]
