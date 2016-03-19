FROM benjamincrom/dockerimage_flask_numpy_redis:latest
MAINTAINER Benjamin Crom "benjamincrom@gmail.com"
ENV REDIS_URL "redis"
COPY . /app
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["app.py"]
