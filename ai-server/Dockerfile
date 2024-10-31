# Dockerfile
FROM python:3.11.4-bookworm
#WORKDIR /code
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
COPY ./feature_builders.py ./feature_builders.py
COPY ./data_pull_tools.py ./data_pull_tools.py
COPY ./ai_builder.py ./ai_builder.py
COPY ./models ./models
COPY ./main.py ./main.py
#ENV PYTHONPATH ./preprocess_tools
ENV FLASK_APP=main.py
COPY ./microservices ./microservices
COPY ./openapi.json ./openapi.json
EXPOSE 5002
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5002"]