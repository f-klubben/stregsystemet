FROM fedora:latest

ARG workdir=/home/stregsystemet
ARG author="FRITFIT"

RUN dnf install python3-pip gcc python3-devel python3.7 -y
RUN dnf clean all

RUN mkdir $workdir
ADD ./ $workdir
WORKDIR $workdir
EXPOSE 8000/tcp
EXPOSE 8000/udp
LABEL org.opencontainers.image.authors=$author

RUN python3.7 -m venv venv
RUN /bin/bash -c "source venv/bin/activate && pip install -r requirements.txt"
RUN /bin/bash -c "source venv/bin/activate && python manage.py migrate"
CMD [ "/bin/bash", "-c", "source venv/bin/activate && python manage.py runserver 0:8000" ]
