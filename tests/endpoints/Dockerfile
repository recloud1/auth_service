FROM python:3.10

ENV PYTHONPATH=/var/testing

RUN mkdir -p $PYTHONPATH
WORKDIR $PYTHONPATH

COPY ./requirements.txt ./

RUN apt-get install -y --no-install-recommends  curl
RUN pip install -r requirements.txt

COPY . .

RUN echo "pytest ./src" > ./run_module.sh

ENTRYPOINT ["/bin/bash", "./run_module.sh"]