# Dockerfile
FROM python:3.11.4-bookworm
#WORKDIR /code
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
COPY ./admin_tools.py ./admin_tools.py
COPY ./processed_games.json ./processed_games.json
COPY ./main.py ./main.py
#ENV PYTHONPATH ./preprocess_tools
ENV FLASK_APP=main.py
COPY ./microservices ./microservices
COPY ./openapi.json ./openapi.json
EXPOSE 5006
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5006"]