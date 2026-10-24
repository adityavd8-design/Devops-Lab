import docker

# Create a Docker client
client = docker.from_env()

# Run the container with the AppArmor profile
container = client.containers.run(
    "flask-apparmor",
    ports={'5000/tcp': 5000},
    security_opt=["apparmor=my-apparmor-profile"],
    detach=True
)
print(f"Container started: {container.short_id}")

# Test restricted actions
exit_code, output = container.exec_run("cat /etc/passwd")
print(f"Attempt to read /etc/passwd: Exit Code {exit_code}, Output: {output.decode()}")

# bash itself is the process docker exec starts (profile is attached at that exec),
# so test a binary launched from inside the confined process
exit_code, output = container.exec_run("/bin/bash -c 'ls /app'")
print(f"Attempt to execute /bin/ls from bash: Exit Code {exit_code}, Output: {output.decode()}")

exit_code, output = container.exec_run("python -c \"import subprocess; subprocess.run(['/bin/bash', '-c', 'echo hacked'])\"")
print(f"Attempt to execute /bin/bash from python: Exit Code {exit_code}, Output: {output.decode()}")

# Allowed action - the app directory can still be read
exit_code, output = container.exec_run("python -c \"print(open('/app/app.py').readline())\"")
print(f"Attempt to read /app/app.py: Exit Code {exit_code}, Output: {output.decode()}")

# Stop the container
container.stop()
container.remove()
print("Container stopped")
