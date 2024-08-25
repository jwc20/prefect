from prefect import flow, task
from sqlalchemy import create_engine, Table, MetaData, select, insert, func
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_URL= os.getenv("POSTGRES_URL")

conn_string = POSTGRES_URL

db = create_engine(conn_string)
metadata = MetaData()

scraped_li_job_listings = Table("scraped_li_job_listings", metadata, autoload_with=db)
job_listings = Table("job_listings", metadata, autoload_with=db)


@task
def fetch_scraped_jobs():
    """Fetch data from the scraped_li_job_listings table."""
    with db.connect() as conn:
        query = select(scraped_li_job_listings)
        result = conn.execute(query)
        return result.fetchall()


@task
def transfer_jobs(scraped_jobs, max_id):
    """Transfer data from scraped_li_job_listings to job_listings."""
    _id = max_id
    with db.connect() as conn:
        for job in scraped_jobs:
            _id += 1
            insert_stmt = insert(job_listings).values(
                id=_id,
                job_title=job.job_title,
                job_link=job.job_link,
                company_name=job.company_name,
                created_at=job.created_at,
                updated_at=job.updated_at,
                job_description_id=None,
                company_id=None,
                source=job.source,
                scraped_from=job.scraped_from,
            )
            conn.execute(insert_stmt)
        conn.commit()


@task
def get_max_id():
    with db.connect() as conn:
        result = conn.scalar(select(func.max(job_listings.c.id)))
        return result
    

@flow(name="job-transfer-flow", log_prints=True)
def job_transfer_flow():
    scraped_jobs = fetch_scraped_jobs()
    max_id = get_max_id()
    transfer_jobs(scraped_jobs, max_id)


# if __name__ == "__main__":
#     job_transfer_flow()
