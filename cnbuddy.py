# -*- coding: utf-8 -*-
'''
Created on Oct 5, 2017

@author: marcoxzh3
'''

_debug = True
_release = True

import getpass, hashlib, json, pytz, sys, time
import mysql.connector
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from keys_utils import import_encrypted_keys
from multiprocessing import Queue, Manager
from piston.steem import Steem
from piston.blog import Blog
from piston.post import Post
from urllib.request import Request, urlopen


def initialize_params(params):
    """
    initialize all parameters
    :param dict the parameters, including:
                config<dict>:     configurations loaded from file 'confi'
                steem<Steem>:     the steem instance which contains private kyes
                manager<Manager>: the multi-thread manager
                tz<timezone>:     the time zone instance
                massage<dict>:    the replied messages, where keys are supported locales and 
                                                           values are the message in different languages
                cners<dict>:      snapshot of all CN users and queue of undetected users
                posts<dict>:      snapshot of all posts and queue of un-upvoted posts
                upvote<Value>:    number of upvotes today
    """
    fp = open('config', 'r')
    config = json.load(fp)
    fp.close()
    # Load wif keys if necessary
    if 'passphrase' in params.keys():
        pw = params['passphrase']
        params.pop('passphrase')
        # Check MD5
        md5target = config['keys_md5']
        hash_md5 = hashlib.md5()
        with open('cnbuddy_keys', 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        pass # with - for
        md5source = hash_md5.hexdigest()
        if md5source != md5target:
            log = 'Fatal error on initialization - corrupted keys:\n'
            log += '   expected: %s\n' % md5target
            log += '      found: %s\n' % md5source
            log += 'About to abort...'
            fp = open('console.log', 'w')
            print(log)
            fp.write(log + '\n')
            fp.close()
            sys.exit(0)
        else:
            log = 'Initializating ...'
            fp = open('console.log', 'w')
            print(log)
            fp.write(log + '\n')
            fp.close()
        pass # if hash_md5.hexdigest() != md5target
        keys = import_encrypted_keys(pw, 'cnbuddy_keys')
        if not _release:
            print(pw)
            print(md5source)
            print(md5target)
            print(json.dumps(keys, indent=2))
        pass # if not _release
        params['keys'] = keys
        params['steem'] = Steem(wif=keys['wif']['posting'], node='wss://steemd.steemitdev.com')
    pass # if 'passphrase' in params.keys()
    params['manager'] = Manager()
    params['config'] = config
    params['tz'] = pytz.timezone(params['config']['time_zone'])
    fp = open('message', 'r')
    params['message'] = json.load(fp)
    fp.close()
    params['cners'] = { 'snapshot': params['manager'].list(), 'queue': Queue() }
    params['posts'] = { 'snapshot': params['manager'].list(), 'queue': Queue() }
    params['upvoted'] = params['manager'].Value('i', 0)
pass # initialize_params(params)


def detect_users(params):
    """
    detect users
    :param dict the parameters (same with initialize_params), including:
                config<dict>:     configurations loaded from file 'confi'
                steem<Steem>:     the steem instance which contains private kyes
                manager<Manager>: the multi-thread manager
                tz<timezone>:     the time zone instance
                massage<dict>:    the replied messages, where keys are supported locales and 
                                                           values are the message in different languages
                cners<dict>:      snapshot of all CN users and queue of undetected users
                posts<dict>:      snapshot of all posts and queue of un-upvoted posts
                upvote<Value>:    number of upvotes today
    """
    try:
        everyone =  list(json.loads(urlopen(Request(params['config']['userurl'], \
                                                    headers={'User-Agent':'Mozilla/5.0'})).read().decode()))
    except Exception as e:
        if _debug:
            fp = open('console.log', 'a')
            log = 'detect_users<%s> exception: %s %s' % (datetime.now(params['tz']), type(e), e)
            print(log)
            fp.write(log + '\n')
            fp.close()
        pass # if _debug
    pass # try - except
    cners, cnt = params['cners'], 0
    for cner in everyone:
        if cner['name'] not in cners['snapshot']:
            cners['snapshot'].append(cner['name'])
            cners['queue'].put(cner)
            cnt += 1
    pass # for - if
    if _debug:
        fp = open('console.log', 'a')
        log = 'detect_users<%s> total = %d; new = %d' % (datetime.now(params['tz']), len(cners['snapshot']), cnt)
        print(log)
        fp.write(log + '\n')
        fp.close()
    pass # if _debug
pass # def detect_users(params)


def detect_posts(params):
    """
    detect posts
    :param dict the parameters (same with initialize_params), including:
                config<dict>:     configurations loaded from file 'confi'
                steem<Steem>:     the steem instance which contains private kyes
                manager<Manager>: the multi-thread manager
                tz<timezone>:     the time zone instance
                massage<dict>:    the replied messages, where keys are supported locales and 
                                                           values are the message in different languages
                cners<dict>:      snapshot of all CN users and queue of undetected users
                posts<dict>:      snapshot of all posts and queue of un-upvoted posts
                upvote<Value>:    number of upvotes today
    """
    while not params['cners']['queue'].empty():
        author = params['cners']['queue'].get()
        today = datetime.now(params['tz']).replace(hour=0, minute=0, second=0)
        if not _release:
            today = today.replace(day=1)
        fir = None
        posts = sorted(Blog(author['name']), key=lambda p: p.created)
        for pst in posts:
            dic = pst.export()
            if params['tz'].localize(dic['created']) >= today:
                fir = dic
                break
        pass # for - if
        if fir is not None:
            fir['upvote_time'] = params['tz'].localize(fir['created']) + \
                                 timedelta(seconds=params['config']['time_upvote'])
            if fir['url'] in params['posts']['snapshot']:
                fp = open('console.log', 'a')
                log = 'detect_posts<%s>: first already up-voted: %s (%s, %s, %s)' % \
                            (datetime.now(params['tz']), author['name'], fir['created'], fir['upvote_time'], fir['url'])
                print(log)
                fp.write(log + '\n')
                fp.close()
                continue
            pass # if fir['url'] in params['posts']['snapshot']
            now = datetime.now(params['tz'])
            if fir['upvote_time'] <= now or not _release:
                fir['upvote_time'] = now + timedelta(seconds=5)
            if _debug:
                if author['name'] != fir['author']:
                    print(author['name'], fir['author'])
                fp = open('console.log', 'a')
                log = 'detect_posts<%s>: first found: %s (%s, %s, %s)' % \
                            (datetime.now(params['tz']), author['name'], fir['created'], fir['upvote_time'], fir['url'])
                print(log)
                fp.write(log + '\n')
                fp.close()
            pass # if _debug
            params['posts']['snapshot'].append(fir['url'])

            # Serialize the first post
            for k, v in fir.items():
                if type(k) is datetime:
                    fir[k] = 'my_serialized_datetime=%d' % int(time.mktime(v.timetuple()))
                elif type(k) is bool:
                    fir[k] = 'my_serialized_boolean=%s' % v
            pass # for k, v in fir.items()
            params['posts']['queue'].put(fir)
            schd = BackgroundScheduler(job_defaults=job_defaults, timezone=params['config']['time_zone'])
            schd.add_job(upvote_reply, args=(params, author, ), id='upvote_reply %s' % fir['url'], \
                              trigger='date', run_date=fir['upvote_time'])
            schd.start()
        else:
            params['cners']['queue'].put(author)
            if _debug:
                fp = open('console.log', 'a')
                log = 'detect_posts<%s>: first not found: %s' % (datetime.now(params['tz']), author['name'])
                print(log)
                fp.write(log + '\n')
                fp.close()
            pass # if _debug
        pass # else - if fir is not None and fir['url'] not in [x['url'] for x in params['posts']['snapshot']]
    pass # while not qUsers['queue'].empty()
pass # def detect_posts(params)


def upvote_reply(params, author):
    """
    upvote and reply the post
    :param dict the parameters (same with initialize_params), including:
                config<dict>:     configurations loaded from file 'confi'
                steem<Steem>:     the steem instance which contains private kyes
                manager<Manager>: the multi-thread manager
                tz<timezone>:     the time zone instance
                massage<dict>:    the replied messages, where keys are supported locales and 
                                                           values are the message in different languages
                cners<dict>:      snapshot of all CN users and queue of undetected users
                posts<dict>:      snapshot of all posts and queue of un-upvoted posts
                upvote<Value>:    number of upvotes today
    :param dict the author's information, see: https://uploadbeta.com/api/steemit/wechat/?cache
    """
    if params['posts']['queue'].empty():
        return
    pst = params['posts']['queue'].get()
    # Restore the serialized version to original
    for k, v in pst.items():
        if type(v) is str and v.startswith('my_serialized_datetime'):
            value = v.split('=')[-1]
            if _debug:
                assert value.isdigit()
            pst[k] = datetime.fromtimestamp(int(value))
        elif type(v) is str and v.startswith('my_serialized_boolean'):
            value = v.split('=')[-1]
            if _debug:
                assert value in ['True', 'False']
            pst[k] = v.split('=')[-1] == 'True'
        pass # elif - if
    pass # for k, v in pst.items()
    db = params['config']['database']
    cnx = mysql.connector.connect(user=db['user'], password=params['keys']['dbkey'], \
                                  host='127.0.0.1', database=db['name'])
    cursor = cnx.cursor()
    try:
        post = Post(pst, steem_instance=params['steem'])
        # Up-vote operation here
        post_urls = list(params['posts']['snapshot'])
        if _debug:
            assert len(post_urls) == len(list(set(post_urls))) and pst['url'] in post_urls
        pass # if _debug
        n = params['upvoted'].value
        vote_weight = 100 * (0.1 if n == 0 else 0.1 * (1.001 ** (2 * n - 3)))
        params['upvoted'] = params['manager'].Value('i', n+1)
        if _debug:
            fp = open('console.log', 'a')
            log = '%3d: %.8f - %s' % (n, vote_weight, pst['author'])
            print(log)
            fp.write(log + '\n')
            fp.close()
        pass # if _debug
        if _release:
            post.upvote(weight=vote_weight, voter=params['config']['me'])
        pass # if _release
        sql = 'INSERT INTO upvote_upvote (author, post_url, post_time, vote_sp, vote_weight, vote_power, vote_time)\
                                  VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\');' % \
                                         (pst['author'], pst['url'], pst['created'].strftime('%Y-%m-%d %H:%M:%S'), \
                             author['sp'], vote_weight, author['vp'], pst['upvote_time'].strftime('%Y-%m-%d %H:%M:%S'))
        cursor.execute(sql)
        cnx.commit()
        if _debug:
            fp = open('console.log', 'a')
            print(sql)
            fp.write(sql + '\n')
            fp.close()
        pass # if _debug

        # Replay operation here
        # TODO: cnbuddy - reply message is improper
        msg = params['message']['zh_CN']
#         if _release:
#             post.reply(msg, author=params['config']['me'])
#         pass # if _release
        reply_time = datetime.now(params['tz'])
        sql = 'INSERT INTO upvote_reply (root_url, parent_author, parent_link, body, reply_time) \
                                 VALUES (\'%s\',\' %s\', \'%s\', \'%s\', \'%s\');' % \
                                (pst['url'], pst['author'], pst['url'], msg, reply_time.strftime('%Y-%m-%d %H:%M:%S'))
        cursor.execute(sql)
        cnx.commit()
        if _debug:
            fp = open('console.log', 'a')
            print(sql)
            fp.write(sql + '\n')
            fp.close()
        pass # if _debug

        if _debug:
            fp = open('console.log', 'a')
            log = 'upvote_reply<%s>: %s--%s' % (datetime.now(params['tz']), pst['author'], pst['url'])
            print(log)
            fp.write(log + '\n')
            fp.close()
            fp = open('posts.log', 'a')
            fp.write('%s\n' % pst['url'])
            fp.close()
        pass # if _debug
    except:
        pass
    pass # try - except

    cnx.close()
pass # def upvote_reply(params, author)

if _debug:
    def debugging(params):
        """
        debugging information
        :param dict the parameters (same with initialize_params), including:
                    config<dict>:     configurations loaded from file 'confi'
                    steem<Steem>:     the steem instance which contains private kyes
                    manager<Manager>: the multi-thread manager
                    tz<timezone>:     the time zone instance
                    massage<dict>:    the replied messages, where keys are supported locales and 
                                                               values are the message in different languages
                    cners<dict>:      snapshot of all CN users and queue of undetected users
                    posts<dict>:      snapshot of all posts and queue of un-upvoted posts
                    upvote<Value>:    number of upvotes today
        """
        cners, posts = params['cners'], params['posts']
        fp = open('console.log', 'a')
        log = 'debugging<%s>: queue(\'cners\')=%d; queue(\'posts\')=%d' % \
                             (datetime.now(params['tz']), cners['queue'].qsize(), posts['queue'].qsize())
        print(log)
        fp.write(log + '\n')
        log = 'debugging<%s>: len(\'cners\')=%d; len(\'posts\')=%d' % \
                             (datetime.now(params['tz']), len(list(cners['snapshot'])), len(list(posts['snapshot'])))
        print(log)
        fp.write(log + '\n')
        fp.close()
    pass # def debugging(params)
pass # if _debug


if __name__ == u'__main__':
    if not _release:
        fp = open('Password.log', 'r')
        params = {'passphrase':fp.read()}
        fp.close()
    else:
        params = {'passphrase':getpass.getpass()}
    initialize_params(params)
    job_defaults = { 'coalesce': False, 'max_instances': params['config']['pool_limit']}

    if _debug:
        scheduler_debug = BackgroundScheduler(job_defaults=job_defaults, timezone=params['config']['time_zone'])
        scheduler_debug.add_job(debugging, args=(params, ), id='debugging', \
                                trigger='interval', seconds=params['config']['detect_post_interval'])
        scheduler_debug.start()
    pass # if _debug

    now = datetime.now(params['tz'])
    scheduler = BlockingScheduler(job_defaults=job_defaults, timezone=params['config']['time_zone'])
    # Add thread to initialize parameters
    if not _release:
        scheduler.add_job(initialize_params, args=(params, ), id='initialize_params', trigger='interval', seconds=86400)
    else:
        ts = [int(x) for x in params['config']['initialize_start'].split(':')]
        next_run = now.replace(hour=ts[0], minute=ts[1], second=ts[2])
        while next_run <= now:
            next_run = next_run + timedelta(seconds=params['config']['initialize_interval'])
        scheduler.add_job(initialize_params, args=(params, ), id='initialize_params', trigger='interval', \
                          seconds=params['config']['initialize_interval'], next_run_time=next_run)
    pass # else - if not _release

    # Add thread to detect users
    if not _release:
        scheduler.add_job(detect_users, args=(params, ), id='detect_users', trigger='interval', seconds=2)
    else:
        ts = [int(x) for x in params['config']['detect_user_start'].split(':')]
        next_run = now.replace(hour=ts[0], minute=ts[1], second=ts[2])
        while next_run <= now:
            next_run = next_run + timedelta(seconds=params['config']['detect_user_interval'])
        scheduler.add_job(detect_users, args=(params, ), id='detect_users', trigger='interval', \
                          seconds=params['config']['detect_user_interval'], next_run_time=next_run)
    pass # else - if not _release

    # Add thread to detect new posts
    if not _release:
        scheduler.add_job(detect_posts, args=(params, ), id='detect_posts', trigger='interval', seconds=2)
    else:
        ts = [int(x) for x in params['config']['detect_post_start'].split(':')]
        next_run = now.replace(hour=ts[0], minute=ts[1], second=ts[2])
        while next_run <= now:
            next_run = next_run + timedelta(seconds=params['config']['detect_post_interval'])
        scheduler.add_job(detect_posts, args=(params, ), id='detect_posts', trigger='interval', \
                          seconds=params['config']['detect_post_interval'], next_run_time=next_run)
    pass # else - if not _release

    scheduler.start()

pass # if __name__ == u'__main__':

