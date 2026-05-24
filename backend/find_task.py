import subprocess
import json
try:
    result = subprocess.run(["team-db", "SELECT id FROM tasks WHERE assigned_to = 'agent-backend-sms-engineer'"], capture_output=True, text=True)
    print(result.stdout)
except Exception as e:
    print(e)
