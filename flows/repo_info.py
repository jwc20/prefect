import httpx
from prefect import flow, task, get_run_logger
from typing import Optional
from datetime import timedelta
from prefect.tasks import task_input_hash



@task(cache_key_fn=task_input_hash, 
      cache_expiration=timedelta(hours=1),
      )
def get_url(url: str, params: Optional[dict[str, any]] = None):
    response = httpx.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_open_issues(repo_name: str, open_issues_count: int, per_page: int = 100):
    issues = []
    pages = range(1, -(open_issues_count // -per_page) + 1)
    for page in pages:
        issues.append(
            get_url.submit(
                f"https://api.github.com/repos/{repo_name}/issues",
                params={"page": page, "per_page": per_page, "state": "open"},
            )
        )
    return [i for p in issues for i in p.result()]

@flow(retries=3, retry_delay_seconds=5, log_prints=True)
def get_repo_info(repo_name: str = "PrefectHQ/prefect"):
    url = f"https://api.github.com/repos/{repo_name}"
    repo_stats = get_url(url)
    issues = get_open_issues(repo_name, repo_stats["open_issues_count"])
    issues_per_user = len(issues) / len(set([i["user"]["id"] for i in issues]))
    
    response = httpx.get(url)
    response.raise_for_status()
    repo = response.json()
    
    # print(f"{repo_name} repository statistics 🤓:")
    # print(f"Stars 🌠 : {repo_stats['stargazers_count']}")
    # print(f"Forks 🍴 : {repo_stats['forks_count']}")
    # print(f"Average open issues per user 💌 : {issues_per_user:.2f}")
    
    logger = get_run_logger()
    logger.info("%s repository statistics 🤓:", repo_name)
    logger.info(f"Stars 🌠 : %d", repo["stargazers_count"])
    logger.info(f"Forks 🍴 : %d", repo["forks_count"])
    logger.info(f"Average open issues per user 💌 : {issues_per_user:.2f}")


# if __name__ == "__main__":
#     get_repo_info.serve(name="my-first-deployment")
    
if __name__ == "__main__":
    get_repo_info.serve(
        name="my-first-deployment",
        cron="* * * * *",
        tags=["testing", "tutorial"],
        description="Given a GitHub repository, logs repository statistics for that repo.",
        version="tutorial/deployments",
    )
