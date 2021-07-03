FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .    
# To copy web folder into the work directory
CMD [ "python3", "bbank.py" ]