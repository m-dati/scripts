#!/usr/bin/python3

import requests

from myutils import openQAHelper
import argparse
import urllib3
import json
import webbrowser
from models import JobSQL, Base, ReviewCache, KnownIssues
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re
import time


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Review(openQAHelper):

    SQL_WHERE_RESULTS = " and result in ('failed', 'timeout_exceeded', 'incomplete')"

    def __init__(self, dry_run: bool = False, browser: bool = False, aliasgroups: str = None):
        super(Review, self).__init__('review', False, load_cache=True, aliasgroups=aliasgroups)
        self.dry_run = dry_run
        self.browser = browser
        self.tabs_to_open = []
        engine = create_engine('sqlite:////scripts/review.db')
        Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.reviewcache_query = self.session.query(ReviewCache)
        self.known_issues_query = self.session.query(KnownIssues)

    def run(self):
        self.session.query(ReviewCache).delete()
        for groupid in self.my_osd_groups:
            latest_build = self.get_latest_build(groupid)
            previous_builds = self.get_previous_builds(groupid)
            self.logger.info('{} is latest build for {}'.format(latest_build, self.get_group_name(groupid)))
            jobs_to_review = self.osd_get_jobs_where(latest_build, groupid, Review.SQL_WHERE_RESULTS)
            for job in jobs_to_review:
                existing_bugrefs = self.get_bugrefs(job.id)
                if len(existing_bugrefs) == 0 and not self.apply_known_refs(job) and previous_builds:
                    bugrefs = set()
                    previous_jobs = self.osd_query("{} build in ({}) and test='{}' and flavor='{}' and group_id={} {}".format(
                        JobSQL.SELECT_QUERY, previous_builds, job.name, job.flavor, groupid, Review.SQL_WHERE_RESULTS))
                    failed_modules = self.get_failed_modules(job.id)
                    for previous_job in previous_jobs:
                        previous_job_sql = JobSQL(previous_job)
                        previous_job_failed_modules = self.get_failed_modules(previous_job_sql.id)
                        if previous_job_failed_modules == failed_modules:
                            bugrefs = bugrefs | self.get_bugrefs(previous_job_sql.id)
                    if len(bugrefs) == 0:
                        self.logger.info(
                            '{} on {} {}t{} [{}]'.format(job.name, job.flavor, self.OPENQA_URL_BASE, job.id,
                                                         failed_modules))
                        if self.browser:
                            self.tabs_to_open.append("{}t{}".format(self.OPENQA_URL_BASE, job.id))
                        self.session.add(ReviewCache(job.name, failed_modules,
                                                     job.result, self.grep_job_failures(job.id)))
                        self.session.commit()
                    else:
                        for ref in bugrefs:
                            self.add_comment(job, ref)
        if self.tabs_to_open:
            input("Hit enter to see all tabs")
            for tab in self.tabs_to_open:
                time.sleep(2)
                webbrowser.open(tab)

    def add_comment(self, job, comment):
        self.logger.debug('Add a comment to {} with reference {}. {}t{}'.format(
            job, comment, self.OPENQA_URL_BASE, job.id))
        cmd = 'openqa-cli api --host {} -X POST jobs/{}/comments text=\'{}\''.format(self.OPENQA_URL_BASE, job.id,
                                                                                     comment)
        self.shell_exec(cmd, self.dry_run)

    def get_failed_modules(self, job_id):
        rezult = self.osd_query(
            "select name from job_modules where job_id={} and result='failed'".format(job_id))
        failed_modules = ""
        rezult.sort()
        for rez in rezult:
            if not failed_modules:
                failed_modules = "{}".format(rez[0])
            else:
                failed_modules = "{},{}".format(failed_modules, rez[0])
        if failed_modules:
            return failed_modules
        else:
            return "NULL"

    def apply_known_refs(self, job):
        failed_modules = self.get_failed_modules(job.id)
        errors_text = self.grep_job_failures(job.id)
        comment_applied = False
        for item in self.known_issues_query.filter(KnownIssues.job_name == job.name).\
                filter(KnownIssues.failed_modules == failed_modules).filter(KnownIssues.errors_text == errors_text).\
                filter(KnownIssues.job_result == job.result):
            if item.label == 'skip':
                self.logger.debug("Ignoring {} due to skip instruction in known issues".format(job))
            else:
                self.add_comment(job, item.label)
            comment_applied = True
        return comment_applied

    def move_cache(self, query):
        m = re.match(r"([fn]=[a-z_,]*)\|([a-z#0-9]*)", query)
        if m:
            cache_filter = m.group(1).split('=')
            label = m.group(2)
            if cache_filter[0] == 'f':
                for review in self.reviewcache_query.filter(ReviewCache.failed_modules == cache_filter[1]).all():
                    if not self.knownissue_exists(review, label):
                        self.add_knownissue(review, label)
                    self.reviewcache_query.filter(ReviewCache.id == review.id).delete()
                self.session.commit()
            elif cache_filter[0] == 'n':
                for review in self.reviewcache_query.filter(ReviewCache.job_name == cache_filter[1]).all():
                    if not self.knownissue_exists(review, label):
                        self.add_knownissue(review, label)
                    self.reviewcache_query.filter(ReviewCache.id == review.id).delete()
                self.session.commit()
        else:
            raise ValueError("Unkown key")

    def knownissue_exists(self, review, label):
        rez = self.known_issues_query.filter(KnownIssues.job_name == review.job_name).\
            filter(KnownIssues.failed_modules == review.failed_modules).\
            filter(KnownIssues.label == label).filter(KnownIssues.job_result == review.job_result).\
            filter(KnownIssues.errors_text == review.errors_text).one_or_none()
        return bool(rez)

    def add_knownissue(self, review, label):
        self.logger.info("Moving {} to known_issues with label={}".format(review, label))
        self.session.add(KnownIssues(review.job_name, review.job_result,
                                     review.errors_text, review.failed_modules, label))

    def grep_job_failures(self, jobid):
        all_errors = []
        job_json = requests.get('{}api/v1/jobs/{}/details'.format(self.OPENQA_URL_BASE, jobid), verify=False).json()
        for rez in job_json['job']['testresults']:
            if rez['result'] == 'failed':
                for frame in rez['details']:
                    if frame['result'] == 'fail':
                        if 'text_data' in frame and 'wait_serial expected:' not in frame['text_data']:
                            all_errors.append(frame['text_data'].split('\n')[0])
        all_errors.sort()
        return ' '.join(all_errors)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dry_run', action='store_true')
    parser.add_argument('-b', '--browser', action='store_true')
    parser.add_argument('-m', '--movecache')
    parser.add_argument('-a', '--aliasgroups')
    args = parser.parse_args()

    review = Review(args.dry_run, args.browser, args.aliasgroups)
    if args.movecache:
        review.move_cache(args.movecache)
    else:
        review.run()


if __name__ == "__main__":
    main()
