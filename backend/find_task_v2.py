import subprocess
import os
try:
    res = subprocess.run(["team-db", "SELECT id FROM tasks WHERE assigned_to = 'agent-backend-sms-engineer'"], capture_output=True, text=True)
    with open("/home/team/shared/task_id.txt", "w") as f:
        f.write(res.stdout)
except Exception as e:
    with open("/home/team/shared/task_id.txt", "w") as f:
        f.write(str(e))
