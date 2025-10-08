FROM apache/airflow:2.10.4-python3.10
USER root

# Install OpenJDK 17 and basic tools needed for Spark client
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Install minimal Spark client for spark-submit
ENV SPARK_VERSION=3.5.7
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark

RUN wget -q -O /tmp/spark.tgz https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
    && mkdir -p ${SPARK_HOME} \
    && tar -xzf /tmp/spark.tgz -C ${SPARK_HOME} --strip-components=1 \
    && rm /tmp/spark.tgz \
    && chmod -R 755 ${SPARK_HOME}

# Set Spark environment variables
ENV PATH="${SPARK_HOME}/bin:${PATH}"

# Copy requirements file and test scripts for Airflow-specific packages
COPY requirements-airflow.txt /requirements-airflow.txt
COPY test_spark_connectivity.py /opt/airflow/test_spark_connectivity.py
RUN chown airflow: /requirements-airflow.txt /opt/airflow/test_spark_connectivity.py

# Switch to airflow user to install Python packages
USER airflow
RUN pip install --no-cache-dir -r /requirements-airflow.txt

