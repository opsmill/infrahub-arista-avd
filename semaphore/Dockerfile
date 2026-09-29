FROM semaphoreui/semaphore:v2.17.12

ENV ANSIBLE_COLLECTIONS_PATH=/opt/semaphore/collections:/usr/share/ansible/collections

USER root

RUN apk add --no-cache python3 py3-pip && \
    pip3 uninstall --yes ansible && \
    pip3 install --break-system-packages \
      "ansible-core==2.19.13" \
      infrahub-sdk \
      "pyavd[ansible]==6.3.0" && \
    pip3 check

USER semaphore
RUN mkdir -p /opt/semaphore/collections
RUN ansible-galaxy collection install \
      opsmill.infrahub:1.9.0 \
      arista.avd:6.3.0 \
      -p /opt/semaphore/collections
