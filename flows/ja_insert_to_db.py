import psycopg2

from prefect import flow, task

from time import sleep

@task
def add_number(x,y):
    sleep(5)
    return x+y

@flow
def calculate(x,y):
    _sum = add_number(x,y)
    return _sum

 

if __name__ == "__main__":
    print(calculate(2,3))
    
