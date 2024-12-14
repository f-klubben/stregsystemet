FROM ubuntu:latest
LABEL authors="kress"

ENTRYPOINT ["top", "-b"]