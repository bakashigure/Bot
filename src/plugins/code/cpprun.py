import time
import subprocess

def run_content_in_docker(content, *, normal_timeout=2, compile_timeout=10, run_timeout=5):

    with open('./tmp.cc', 'w+') as f:
        f.write(content)

    image = "ubuntu-1"
    name = 'u' + str(time.time_ns())

    prefix = "compile"
    result = ""

    try:
        p = subprocess.run('sudo -S docker container prune -f', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker create -it --name {name} --memory 64m --cpus 1 {image} bash', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker cp ./tmp.cc {name}:/root/tmp.cc', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker start {name}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run(f'sudo -S docker exec {name} bash -c "g++ /root/tmp.cc -o /root/tmp -std=c++20 2>&1"', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=compile_timeout)
        res = p.stdout.rstrip()
        result += res
        result = result.strip()
        prefix = "run"

        p = subprocess.run(f'sudo -S docker exec {name} bash -c "/root/tmp" 2>&1', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=run_timeout)
        res = p.stdout.rstrip()
        result += "\n" + res
        result = result.strip()

        p = subprocess.run("sudo -S docker inspect -f '{{.State.Status}}' " + name, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

    except subprocess.SubprocessError as e:
        if prefix == "compile":
            result += f'\n{prefix} timed out after {compile_timeout} seconds'
            result = result.strip()
        else:
            result += f'\n{prefix} timed out after {run_timeout} seconds'

    except Exception as e:
        result += "\n" + str(e)
        result = result.strip()

    finally:
        p = subprocess.run(f'sudo -S docker kill {name}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

        p = subprocess.run('sudo -S docker container prune -f', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", shell=True, timeout=normal_timeout)
        # print(p.stdout.rstrip())

    return result
