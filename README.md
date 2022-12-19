# Gateway readme

This gateway project is a python project which aims to just send received raw serial data to the cloud through the mqtt protocol

## Setup

To setup and run on Linux and probably macOs and BSD (use python3):  
* `python -m venv .venv`  
* `. .venv/bin/activate`  
* `pip3 install -r requirements.txt`  

To setup and run on Windows :  
* `python -m venv .venv`  
* `.\.venv\Scripts\activate`  
* `pip3 install -r requirements.txt` 

To activate without setting up :  
* `. .venv/bin/activate` or `.\.venv\Scripts\activate`  

To quit just :  
* `deactivate`

## Run

Please fill all the config.ini fields with good sense  

* In the venv `./main.py config.ini`  
* Also for some help `./main.py -h`  

## Protocol spec from the bridge

###  Normal use

The bridge justs sends the number of the board having the button pressed when this happens  

This number should be between between 0 and 19 included since esp-now don't really support more than 10 devices at the same time per bridge

### Special codes from bridge

Special values returned :
* 200 - ready
* 100 - error in setup esp-now

### Errors

Anything different from the spec are not valid and may be considered as errors except the ones before the special codes as theses happens at the setup  
