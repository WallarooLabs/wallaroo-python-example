# This is pinned to a stable release. We'll update this
# repository to follow each stable release. If you'd like
# to used something older, you may check the history of
# this repository for something which points at an older
# release here.
FROM wallaroo-labs-docker-wallaroolabs.bintray.io/release/wallaroo:0.4.2
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
EXPOSE 10000-50000
ENTRYPOINT ["/bin/sh", "-c", "\"${*}\""]
