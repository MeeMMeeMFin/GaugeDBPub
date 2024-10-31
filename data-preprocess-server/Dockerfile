# Dockerfile
FROM python:3.11.4-bookworm
#WORKDIR /code
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
COPY ./preprocess_tools/review_scrape.py ./preprocess_tools/review_scrape.py
COPY ./preprocess_tools/preprocess.py ./preprocess_tools/preprocess.py
COPY ./preprocess_tools/data_insert.py ./preprocess_tools/data_insert.py
COPY ./main.py ./main.py
ENV PYTHONPATH ./preprocess_tools
ENV FLASK_APP=main.py
COPY ./microservices ./microservices
COPY ./openapi.json ./openapi.json
EXPOSE 5001
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5001"]