# coding=utf-8
"""
    @project: MaxKB
    @file: clean_operate_log_job.py
    @desc: 按清理策略定期删除过期操作日志
"""
from common.job.scheduler import scheduler
from common.utils.lock import lock, RedisLock
from common.utils.logger import maxkb_logger


def clean_operate_log():
    clean_operate_log_lock()


@lock(lock_key='clean_operate_log_job_execute', timeout=60)
def clean_operate_log_lock():
    from django.utils.translation import gettext_lazy as _
    from system_manage.serializers.log_management import clean_expired_log
    maxkb_logger.info(_('start clean operation log'))
    clean_expired_log()
    maxkb_logger.info(_('end clean operation log'))


def run():
    rlock = RedisLock()
    if rlock.try_lock('clean_operate_log_job', 30 * 30):
        try:
            maxkb_logger.debug('get lock clean_operate_log_job')

            existing_job = scheduler.get_job(job_id='clean_operate_log')
            if existing_job is not None:
                existing_job.remove()
            scheduler.add_job(clean_operate_log, 'cron', hour='0', minute='20', id='clean_operate_log',
                              misfire_grace_time=300, max_instances=1)
        finally:
            rlock.un_lock('clean_operate_log_job')
