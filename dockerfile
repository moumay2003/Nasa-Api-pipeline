FROM apache/airflow:2.10.4
USER root

# Install OpenJDK 17 instead of 11 which is not available in Debian Bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Copy requirements file (still as root to ensure proper permissions)
COPY requirements.txt /requirements.txt
# Make sure the airflow user can read the requirements file
RUN chown airflow: /requirements.txt

# Switch to airflow user to install Python packages
USER airflow
RUN pip install --no-cache-dir -r /requirements.txt

