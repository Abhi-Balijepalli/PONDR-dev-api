# Pondr API - `Dev Version`
*Beta Launch Container*
----
#### Author: Abhi Balijepalli
#### Co-Authors: Zyad Elgohary & Ibrahim Saeed
## Copyright: 
This software and it's content is a copyright of Abhi Balijepalli & © Pondr. Any redistributions or reproduction of part of all of the contents in any form is prohibited other than the following: 
- You may clone the repo and modify for personal non-profit and/or non-commercial projects, as long as you acknowledge the software and repo as the source of the material.
- If you want to use the code for commercial or profit use, please contact abhibalijepalli@gmail.com


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
