#!/usr/bin/python3

import requests

from myutils import TaskHelper
import argparse
import pickle
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Job:

    def __init__(self, openqa_job):
        self.id = openqa_job['job']['id']
        self.name = openqa_job['job']['settings']['TEST']
        self.instance_type = openqa_job['job']['settings']['PUBLIC_CLOUD_INSTANCE_TYPE']
        self.parents_ok = openqa_job['job']['parents_ok']
        self.result = openqa_job['job']['result']
        self.state = openqa_job['job']['state']
        self.build = openqa_job['job']['settings']['BUILD']
        self.flavor = openqa_job['job']['settings']['FLAVOR']
        self.hdd = openqa_job['job']['settings']['HDD_1']
        self.failed_modules = []
        for module in openqa_job['job']['testresults']:
            if module['result'] == 'failed':
                self.failed_modules.append(module['name'])

    def needs_review(self, latest_build: int) -> bool:
        return bool(self.build == latest_build and self.result != 'passed' and not self.needs_update())

    def needs_update(self) -> bool:
        return bool(self.state not in ['done', 'cancelled'])

    def is_previous(self, job_to_compare, expected_build) -> bool:
        is_previous = bool(job_to_compare.build == expected_build and self.name == job_to_compare.name and \
                           self.instance_type == job_to_compare.instance_type and self.flavor == job_to_compare.flavor)
        if not is_previous:
            return False
        return bool(sorted(job_to_compare.failed_modules) == sorted(self.failed_modules))

    def __str__(self):
        pattern = 'Job(id: {}, name: {}, instance_type: {}, result: {}, state: {}, build: {}, flavor: {},' \
                  ' failed_modules: {})'
        return pattern.format(self.id, self.name, self.instance_type, self.result, self.state, self.build, self.flavor,
                              self.failed_modules)


class Review(TaskHelper):

    def __init__(self, groupid: int, dry_run: bool = False):
        super(Review, self).__init__('review', log_to_file=False)
        self.cached_jobs = {}
        self.dry_run = dry_run
        self.groupid = groupid
        self.latest_build = self.get_latest_build(self.groupid)
        self.logger.info(self.latest_build + ' is latest build')
        self.cached_file = 'jobs{}.pickle'.format(self.groupid)
        if Path(self.cached_file).exists():
            self.logger.info('Cached jobs found loading from ' + self.cached_file)
            with open(self.cached_file, 'rb') as handle:
                self.cached_jobs = pickle.load(handle)
            self.logger.info('Cache has {} jobs'.format(len(self.cached_jobs)))

    def refresh_cache(self, latest_job_ids):
        for id in latest_job_ids['ids']:
            if id not in self.cached_jobs or self.cached_jobs[id].needs_update():
                self.cached_jobs[id] = Job(
                    requests.get('{}jobs/{}/details'.format(self.OPENQA_API_BASE, id), verify=False).json())
                self.logger.debug('Updating {}'.format(self.cached_jobs[id]))

    def run(self):
        self.logger.info('Getting jobs for groupid={}'.format(self.groupid))
        job_group_jobs = requests.get('{}job_groups/{}/jobs'.format(self.OPENQA_API_BASE, self.groupid),
                                      verify=False).json()
        self.logger.info('Got {} jobs'.format(len(job_group_jobs['ids'])))
        self.refresh_cache(job_group_jobs)

        jobs_needs_review = []

        for job in self.cached_jobs:
            if job.needs_review(self.latest_build):
                jobs_needs_review.append(job.id)

        for need_review_id in jobs_needs_review:
            need_review_bugrefs = self.get_bugrefs(need_review_id)
            if len(need_review_bugrefs) > 0:
                self.logger.info('{} already have bug refs'.format(need_review_id))
            else:
                previous_jobs = self.get_previous_jobs(need_review_id)
                bugrefs = set()
                for id in previous_jobs:
                    bugrefs = bugrefs | self.get_bugrefs(id)
                for ref in bugrefs:
                    self.logger.info(
                        'Add a comment to {} with reference {}'.format(self.cached_jobs[need_review_id], ref))
                    if not self.dry_run:
                        self.shell_exec(
                            'openqa-cli api --host {} -X POST jobs/{}/comments text=\'{}\''.format(self.OPENQA_URL_BASE,
                                                                                                   need_review_id, ref),
                            log=True)

        self.logger.info('Saving the cache to ' + self.cached_file)
        with open(self.cached_file, 'wb') as handle:
            pickle.dump(self.cached_jobs, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def get_bugrefs(self, job_id):
        bugrefs = set()
        comments = requests.get('{}jobs/{}/comments'.format(self.OPENQA_API_BASE, job_id), verify=False).json()
        for comment in comments:
            for bug in comment['bugrefs']:
                bugrefs.add(bug)
        return bugrefs

    def get_previous_jobs(self, job_id):
        previous_jobs = []
        for i in [1, 2, 3]:
            previous_build = '00{}'.format(int(self.latest_build) - i)
            for id in self.cached_jobs:
                if id == job_id:
                    continue
                if self.cached_jobs[job_id].is_previous(self.cached_jobs[id], previous_build) and self.cached_jobs[
                    id].result == 'failed':
                    previous_jobs.append(id)
        return previous_jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--groupid', required=True)
    parser.add_argument('--dry_run', action='store_true')
    args = parser.parse_args()

    review = Review(args.groupid, args.dry_run)
    review.run()


if __name__ == "__main__":
    main()
