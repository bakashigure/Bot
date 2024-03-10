import time
import subprocess

def run_content_in_docker(content, *, normal_timeout=2, run_timeout=5):

    with open('./tmp.py', 'w+') as f:
        f.write(content)

    image = "ubuntu-1"
    name = 'u' + str(time.time_ns())

    result = ""

    try:
        p = subprocess.run('sudo -S docker container prune -f', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker create -it --name {name} --memory 16m --cpus 1 {image} bash', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker cp ./tmp.py {name}:/root/tmp.py', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker start {name}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker exec {name} bash -c "python3 /root/tmp.py 2>&1"', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=run_timeout)
        result = p.stdout.rstrip()
        # print(result)

        p = subprocess.run("sudo -S docker inspect -f '{{.State.Status}}' " + name, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

    except subprocess.SubprocessError as e:
        result = f'timed out after {run_timeout} seconds'

    except Exception as e:
        result = str(e)

    finally:
        p = subprocess.run(f'sudo -S docker kill {name}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run('sudo -S docker container prune -f', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

    return result
