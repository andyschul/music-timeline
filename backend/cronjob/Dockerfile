FROM python:3.7
RUN apt-get update && apt-get -y install cron vim

# Adding crons from current directory
ADD crons /etc/cron.d/crons

# Adding entrypoint.sh from current directory
ADD entrypoint.sh /entrypoint.sh

ADD cleaner.py /var/scripts/
ADD load_new_releases.py /var/scripts/

# Adding executable permissions
RUN chmod +x /entrypoint.sh /etc/cron.d/crons /var/scripts/load_new_releases.py

# Setting sample ENV variable
ENV TZ_TEST=Asia/Kolkata

# Create a new crontab file
RUN touch /etc/cron.d/crontab

# Grep all env variable and COPY to crontab file
RUN printenv | sed 's/^\(.*\)$/\1/g' > /etc/cron.d/crontab

# Now append all commands in crons file to crontab file
RUN cat /etc/cron.d/crons >> /etc/cron.d/crontab

# Delete the crons file
RUN rm -f /etc/cron.d/crons

ENTRYPOINT /entrypoint.sh