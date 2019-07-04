# DeltaML - Model Buyer


## Installing

A step by step series that tell you how to get a development env running



```
git clone git@github.com:DeltaML/model-buyer.git
cd model-buyer/
python3 -m venv venv
source venv/bin/activate
pip install -r model_buyer/requirements.txt
```

## Run

### Using command line
``` bash
    gunicorn -b "0.0.0.0:9090" --chdir model_buyer/ wsgi:app --preload
``` 


### Using Pycharm
``` bash
    Script Path: .../model_buyer/virtualenv/bin/gunicorn
	Parameters: -b "0.0.0.0:9090" wsgi:app --preload
	Working directory: ../model_buyer
```
	
### Using Docker

Select _LOCAL_PORT_ number to run some containers
``` bash
    docker build -t federated-learning-model-buyer --rm -f model_buyer/Dockerfile .
    docker run --rm -it -p 9090:9090 federated-learning-model-buyer
``` 



## Usage 
 
### Make model from federated trainer

``` bash
curl -v -H "Content-Type: application/json" -X POST "http://localhost:9090/model" --data @examples/model.json
```


### Get make model 

``` bash
curl -v -H "Content-Type: application/json" -X GET "http://localhost:9090/model/<model_id>"
```


### Get all make model 

``` bash
curl -v -H "Content-Type: application/json" -X GET "http://localhost:9090/model"
```



### Generate prediction

``` bash
curl -v -H "Content-Type: application/json" -X POST "http://localhost:9090/prediction" --data '{"model_id": "<MODEL_ID>"}'
```

### Get prediction 

``` bash
curl -v -H "Content-Type: application/json" -X GET "http://localhost:9090/prediction/<prediction_id>"
```


### Get all prediction 

``` bash
curl -v -H "Content-Type: application/json" -X GET "http://localhost:9090/prediction"
```


## Model buyer configuration

``` python3

config = {
    'server_register_url': "http://cte_federated_trainer:8080/model",
    'key_length': 1024,
    'active_encryption': False
}
```

## Release History

* 0.0.1
    * Work in progress
