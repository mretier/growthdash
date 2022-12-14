FROM python:3.11-slim

LABEL maintainer "Michael Reiter, michael.reiter@live.com"

WORKDIR /


# install packages
COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt \
	&& rm -rf /root/.cache


# copy files to folder in container
COPY ./ ./

# ENV ENVIRONMENT_FILE=".env"

# EXPOSE 8085

# Run locally on port 8050
# CMD gunicorn --workers 11 --threads 1 --timeout 1200 --bind 0.0.0.0:8050 app:server
# ENTRYPOINT ["gunicorn", "--config", "gunicorn_config.py", "index:server"]
CMD gunicorn --workers 11 --threads 1 --timeout 1200 --bind 0.0.0.0:8050 app:server