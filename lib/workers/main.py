import requests
import threading
import os
from pprint import pprint
from json import dumps
from concurrent.futures import ThreadPoolExecutor, as_completed
#from .db import insert_result
from config import WORKER_THREADS

# Simple HTTP fetcher
#def fetch_and_store(url, timeout=10):
#    try:
#        resp = requests.get(url, timeout=timeout)
#        snippet = resp.text[:1000]  # keep small
#        insert_result(url, resp.status_code, snippet)
#        return (url, resp.status_code)
#    except requests.RequestException as e:
#        # store failure with status_code 0
#        insert_result(url, 0, str(e)[:1000])
#

def TJob(url,timeout=10):
    tid=threading.get_ident()
    pid=os.getpid()
    print("Hello in in TJob URL=%s  TID:%s PID:%s" % (url,tid,pid))
    return (url, "bk url=%s" %url)



def run_worker(urls, max_workers=None):
    max_workers = max_workers or WORKER_THREADS
    results = []
    print("Hello in run_worker")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(TJob, url): url for url in urls}
        for fut in as_completed(futures):
            pprint(fut)
            url=futures[fut]
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                # unexpected exception from worker
                print("Worker exception for", url, e)
    pprint(results)
    print(dumps(results,indent=4))
    return results

