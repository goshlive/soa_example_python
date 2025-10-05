# SOA Example (python)

There are two type of SOA in this demo (SOAP & REST). Navigate to the respective folder and do the following:

### 1. Install dependencies
```pip install spyne zeep lxml```

### 2. Run micro-service
```python micro_server.py```
<br>Access the WSDL at: `http://localhost:8001?wsdl`

### 3. Run other servies
```python main_server.py```
<br>Access the WSDL at: `http://localhost:8000?wsdl`

### 4. Execute client
```python client.py```




