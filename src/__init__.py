from concurrent.futures import ThreadPoolExecutor

from .core.scrapers.indeed import IndeedScraper
from .core.scrapers.ziprecruiter import ZipRecruiterScraper
from .core.scrapers.linkedin import LinkedInScraper
from .core.formatters.csv import CSVFormatter
from .core.scrapers import (
    ScraperInput,
    Site,
    JobResponse,
    OutputFormat,
    CommonResponse,
)

import pandas as pd
from .core.jobs import JobType
from typing import List, Dict, Tuple, Union

SCRAPER_MAPPING = {
    Site.LINKEDIN: LinkedInScraper,
    Site.INDEED: IndeedScraper,
    Site.ZIP_RECRUITER: ZipRecruiterScraper,
}

def _map_str_to_site(site_name: str) -> Site:
    return Site[site_name.upper()]


def scrape_jobs(
        site_name: str | Site | List[Site],
        search_term: str,

        output_format: OutputFormat = OutputFormat.JSON,
        location: str = "",
        distance: int = None,
        is_remote: bool = False,
        job_type: JobType = None,
        easy_apply: bool = False,  # linkedin
        results_wanted: int = 15
) -> pd.DataFrame:
    """
    Asynchronously scrapes job data from multiple job sites.
    :param scraper_input:
    :return: scraper_response
    """

    if type(site_name) == str:
        site_name = _map_str_to_site(site_name)

    site_type = [site_name] if type(site_name) == Site else site_name
    scraper_input = ScraperInput(
        site_type=site_type,
        search_term=search_term,
        location=location,
        distance=distance,
        is_remote=is_remote,
        job_type=job_type,
        easy_apply=easy_apply,
        results_wanted=results_wanted,
        output_format=output_format
    )

    def scrape_site(site: Site) -> Tuple[str, JobResponse]:
        scraper_class = SCRAPER_MAPPING[site]
        scraper = scraper_class()
        scraped_data: JobResponse = scraper.scrape(scraper_input)
        return site.value, scraped_data

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = dict(executor.map(scrape_site, scraper_input.site_type))

    df = pd.DataFrame()

    for site in results:
        for job in results[site].jobs:
            data = job.json()

            data_df = pd.read_json(data, typ='series')
            data_df['site'] = site

            #: concat
            df = pd.concat([df, data_df], axis=1)

    return df


