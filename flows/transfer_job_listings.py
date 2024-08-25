from prefect import flow, task
from sqlalchemy import create_engine, Table, MetaData, exists, select, insert, func, and_
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL")

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
def get_max_id():
    """Get the maximum ID from the job_listings table."""
    with db.connect() as conn:
        result = conn.scalar(select(func.max(job_listings.c.id)))
        return result

@task
def check_new_records():
    """Check if there are new records in scraped_li_job_listings that are not in job_listings."""
    with db.connect() as conn:
        query = select(scraped_li_job_listings).where(
            ~exists(
                select(1).where(
                    and_(
                        job_listings.c.job_title == scraped_li_job_listings.c.job_title,
                        job_listings.c.job_link == scraped_li_job_listings.c.job_link,
                        job_listings.c.created_at == scraped_li_job_listings.c.created_at,
                    )
                )
            )
        )
        result = conn.execute(query)
        return result.fetchall()

@task
def transfer_jobs(scraped_jobs, max_id):
    """Transfer data from scraped_li_job_listings to job_listings."""
    if not scraped_jobs:
        print("No new records to transfer.")
        return

    _id = max_id if max_id is not None else 0
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
        print(f"Transferred {len(scraped_jobs)} new jobs.")

@flow(name="job-transfer-flow", log_prints=True)
def job_transfer_flow():
    max_id = get_max_id()  # Get the current max ID in job_listings
    new_scraped_jobs = check_new_records()  # Check if there are new records to transfer

    if new_scraped_jobs:
        print(f"Found {len(new_scraped_jobs)} new records to transfer.")
        transfer_jobs(new_scraped_jobs, max_id)  # Transfer new records
    else:
        print("No new records found. Skipping transfer.")



