import uuid
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class JobManager:
    def __init__(self, max_workers=1):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {} # { job_id: { status: 'queued'|'processing'|'done'|'failed', result: ..., error: ... } }
        self.lock = threading.Lock()

    def submit_job(self, task_func, *args):
        job_id = str(uuid.uuid4())
        
        with self.lock:
            self.jobs[job_id] = {
                "status": "queued",
                "submitted_at": time.time()
            }

        # Submit to thread pool
        self.executor.submit(self._run_job, job_id, task_func, *args)
        return job_id

    def _run_job(self, job_id, task_func, *args):
        # Update to processing
        with self.lock:
             if job_id in self.jobs:
                self.jobs[job_id]["status"] = "processing"

        try:
            # Execute the heavy task
            result = task_func(*args)
            
            with self.lock:
                self.jobs[job_id]["status"] = "done"
                self.jobs[job_id]["result"] = result
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            with self.lock:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["error"] = str(e)

    def get_job(self, job_id):
        with self.lock:
            return self.jobs.get(job_id)

# Singleton Instance
job_manager = JobManager(max_workers=1)
