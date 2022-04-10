# Pondr API - `Dev Version`
*Beta Launch Container*
----
#### Author: Abhi Balijepalli
#### Co-Authors: Zyad Elgohary & Ibrahim Saeed


## Docker 
- `docker build -t arthurcourtreg.azurecr.io/perceval  . `
- `docker run -p 8080:8080 registrymerlinv1.azurecr.io/HIDDEN `

- `docker login HIDDEN.azurecr.io`
  - username `N/A`
  - password `get access key from Azure registry`
- `docker push HIDDEN.azurecr.io/perceval`

## Without Docker
- `pip3 install requirements.txt`
- `python3 app.py` - to run locally
