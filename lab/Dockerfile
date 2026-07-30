FROM ubuntu

RUN apt update && apt install -y --no-install-recommends \
    udev \
    netplan.io \
    iputils-ping \
    openssh-server \
    vim \
    locales \
    lldpd \
    tcpdump \
    smcroute \
    sudo \
    && rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8
RUN adduser --disabled-password --gecos "" admin && passwd -d admin
RUN sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords yes/g' /etc/ssh/sshd_config && sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config
RUN echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin && touch /home/admin/.sudo_as_admin_successful
RUN rm -f /etc/machine-id
CMD [ "/lib/systemd/systemd" ]