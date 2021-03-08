from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import logzero
import smtplib
import socket
import os
import traceback
import requests
import subprocess
import json
from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, JobORM
import configparser


class TaskHelper:

    def __init__(self, name):
        self.name = name
        self.config = configparser.ConfigParser()
        self.config.read('/etc/{}.ini'.format(self.name))
        self.to_list = config.get('DEFAULT', 'to_list', fallback='asmorodskyi@suse.com')
        if self.config['DEFAULT'].getboolean('log_to_file', fallback=True):
            self.logger = logzero.setup_logger(
                name=name, logfile='/var/log/{0}/{0}.log'.format(self.name), formatter=logzero.LogFormatter(
                    fmt='%(color)s[%(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s',
                    datefmt='%d-%m %H:%M:%S'))
        else:
            self.logger = logzero.setup_logger(
                name=name, formatter=logzero.LogFormatter(
                    fmt='%(color)s%(module)s:%(lineno)d|%(end_color)s %(message)s'))

    def send_mail(self, subject, message, html_message: str = None):
        try:
            if html_message:
                mimetext = MIMEMultipart('alternative')
                part1 = MIMEText(message, 'plain')
                part2 = MIMEText(html_message, 'html')
                mimetext.attach(part1)
                mimetext.attach(part2)
            else:
                mimetext = MIMEText(message)
            mimetext['Subject'] = subject
            mimetext['From'] = 'asmorodskyi@suse.com'
            mimetext['To'] = self.to_list
            server = smtplib.SMTP('relay.suse.de', 25)
            server.ehlo()
            server.sendmail('asmorodskyi@suse.com', self.to_list.split(','), mimetext.as_string())
        except Exception:
            self.logger.error("Fail to send email - {}".format(traceback.format_exc()))

    def handle_error(self, error=''):
        if not error:
            error = traceback.format_exc()
        self.logger.error(error)
        self.send_mail('[{}] ERROR - {}'.format(self.name, socket.gethostname()), error)

    def get_latest_build(self, job_group_id=262):
        build = '1'
        try:
            group_json = requests.get('https://openqa.suse.de/group_overview/{}.json'.format(job_group_id),
                                      verify=False).json()
            build = group_json['build_results'][0]['build']
        except Exception as e:
            self.logger.error("Failed to get build from openQA - %s", e)
        finally:
            return build

    def shell_exec(self, cmd, log=False, is_json=False):
        try:
            if log:
                self.logger.info(cmd)
            output = subprocess.check_output(cmd, shell=True)
            if is_json:
                o_json = json.loads(output)
                if log:
                    self.logger.info("%s", o_json)
                return o_json
            else:
                if log:
                    self.logger.info("%s", output)
                return output
        except subprocess.CalledProcessError:
            self.handle_error('Command died')


class GitHelper(TaskHelper):

    def __init__(self):
        super().__init__("GitHelper")
        self.repo = Repo(os.getcwd())
        self.remote = None
        try:
            if self.repo.remotes.asmorodskyi.exists():
                self.remote = self.repo.remotes.asmorodskyi
        except Exception:
            self.remote = self.repo.remotes.origin


class openQAHelper(TaskHelper):

    def __init__(self, name, for_o3, load_cache=False, groupid: str = None):
        super(openQAHelper, self).__init__(name)
        self.for_o3 = for_o3
        if groupid:
            self.my_osd_groups = [int(num_str) for num_str in str(groupid).split(',')]
        else:
            self.my_osd_groups = [262, 219, 274, 275]
        if self.for_o3:
            self.OPENQA_URL_BASE = 'https://openqa.opensuse.org/'
        else:
            self.OPENQA_URL_BASE = 'https://openqa.suse.de/'
        self.OPENQA_API_BASE = self.OPENQA_URL_BASE + 'api/v1/'
        if load_cache:
            engine = create_engine('sqlite:////scripts/openqa_cache.db')
            Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            self.job_query = self.session.query(JobORM)
            self.logger.info("{} objects was in cache".format(self.job_query.count()))

    def get_previous_builds(self, job_group_id: int, deep: int = 3):
        builds = []
        group_json = requests.get('{}group_overview/{}.json'.format(self.OPENQA_URL_BASE, job_group_id),
                                  verify=False).json()
        if len(group_json['build_results']) > deep:
            for i in range(0, deep):
                builds.append(group_json['build_results'][i + 1]['build'])
        return builds

    def groupID_to_name(self, groupid):
        groupid = int(groupid)
        if groupid == 170 or groupid == 262:
            return "Network"
        elif groupid == 219:
            return "Azure"
        elif groupid == 274:
            return "EC2"
        elif groupid == 275:
            return "GCE"
        elif groupid == 276:
            return "PC Tools Image"
        elif groupid == 131:
            return "SLES JeOS"
        else:
            return str(groupid)

    def refresh_cache(self, groupid):
        job_group_jobs = requests.get(
            '{}job_groups/{}/jobs'.format(self.OPENQA_API_BASE, groupid), verify=False).json()
        self.logger.info('Got {} jobs for {}'.format(len(job_group_jobs['ids']), self.groupID_to_name(groupid)))
        for groupid in job_group_jobs['ids']:
            job_orm = self.job_query.get(groupid)
            if job_orm:
                if job_orm.needs_update:
                    job_orm.update_from_json(requests.get(
                        '{}jobs/{}/details'.format(self.OPENQA_API_BASE, groupid), verify=False).json())
                    self.logger.debug('Updating {}'.format(job_orm))
                    self.session.commit()
            else:
                job_orm = JobORM()
                job_orm.update_from_json(requests.get(
                    '{}jobs/{}/details'.format(self.OPENQA_API_BASE, groupid), verify=False).json())
                self.logger.debug('Adding {}'.format(job_orm))
                self.session.add(job_orm)
                self.session.commit()

    def get_bugrefs(self, job_id):
        bugrefs = set()
        comments = requests.get('{}jobs/{}/comments'.format(self.OPENQA_API_BASE, job_id), verify=False).json()
        if 'error' in comments:
            raise RuntimeError(comments)
        for comment in comments:
            for bug in comment['bugrefs']:
                bugrefs.add(bug)
        return bugrefs


def is_matched(rules, topic, msg):
    for rule in rules:
        rkey, filter_matches = rule
        if rkey.match(topic) and filter_matches(topic, msg):
            return True
