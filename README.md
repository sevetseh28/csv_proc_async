# CSV Processing using async tasks
## Explanation
This project was developed using Python, PostgreSQL, SQLAlchemy ORM, RabbitMQ and Celery.
The ORM is used to increase the producer's independence from the underlying database technology.

It is divided into Consumer and Producer and they are both dockerized.
This allows for separate deployment on different servers and portability.

The Producer includes Python code (producer.py) and the message broker (RabbitMQ).
It receives a CSV path (local to the container) via command line and processes it lazily (using a generator) to find fullnames and email.
- Email is checked against a regex and 254 char limit (http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690)
- Fullname is the first value in a row that doesnt match the email regex and is under 256 chars which should be
enough to hold a fullname.

    ** If one of both is not found then the row is filtered out.
    
For each pair found it sends the task to RabbitMQ for the consumer to execute.
An ```example_csvs``` directory is included on the solution, and you may add your own CSV files on this directory
prior to building the image. 

Since we have no control over the CSV content we first try to guess the encoding and the dialect used
for the CSV format reading the first 1024 bytes and the first line respectively.

The Consumer includes the Python code to run the task and the database itself. It receives tasks 
from the message broker and inserts the tuples into the database.
If there is already a tuple with the same email in the database then it will raise an Integrity error 
(this is enforced by a unique restriction on the field) and abort the tuple insertion.

** The consumer task is a custom task (DBTask) that holds only one session object to the database for each worker.

   

## Usage and deployment
The solution comes ready for separate deployment on different machines. You should only change the ```BROKER_CONN``` on the producer to point your consumer's IP address on the network 
(may be the local network if you are deploying both on the same machine). 
### Consumer
1. First initialize the Database:

    ```docker-compose run worker python /database/initialization.py```

This will create the database and the People table to hold fullnames and emails.

2. Then build and run the containers:
    
    ```docker-compose up```


### Producer

1. First build and run the containers:
    ```docker-compose up```

2. Get into the producer container and inside it run:

    ```python producer.py -p 'example_csvs/100-contacts.csv'```
    
    If you wish to test your own CSV file then you must include it in the example_csvs directory and rebuild the images or use
    a bind mount to share the directory with the host (not desired for portability reasons).


## TODO
* Check before reading the first line (for dialect detection) that the line is not too big to avoid memory issues.
* Easier way to add CSV files (instead of rebuilding the image each time and reading them from file). Perhaps adding an endpoint for CSV uploading.
* Add more complex criteria to match the fullname entity (e.g. when name and surname come in separate fields)
* Add Redis as the result backend
* Enable SSL on RabbitMQ
* Unit tests
