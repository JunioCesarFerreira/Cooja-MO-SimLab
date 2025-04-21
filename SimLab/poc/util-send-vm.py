import os
import paramiko
from scp import SCPClient

def create_ssh_client(hostname, port, username, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)
    return client

def send_files_scp(client, local_path, remote_path, source_files, target_files):
    if len(source_files) != len(target_files):
        print("The number of source files is not equal number of targets.")
        print(source_files)
        print(target_files)
        return
    with SCPClient(client.get_transport()) as scp:
        for src, dest in zip(source_files, target_files):
            local_file_path = local_path + "/" + src
            remote_file_path = remote_path + "/" + dest
            print(f"Sending {local_file_path} to {remote_file_path}")
            scp.put(local_file_path, remote_file_path)  

def replace_in_file(input_file: str, output_file: str, old_str: str, new_str: str):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        modified_content = content.replace(old_str, new_str)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        print(f"Replacement complete. Output saved to '{output_file}'.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

local_directory = '.'
remote_directory = '/home/ubuntu/contiki-ng/examples/test'
vm_hostname = '172.26.96.1'
vm_username = 'ubuntu'
vm_password = 'ubuntu'  
vm_port = 2222


sim_num = 2
replace_in_file(f"tmp/sim_{sim_num}.xml", f"tmp/sim_{sim_num}.csc", "/opt/contiki-ng/tools/cooja/", "/home/ubuntu/contiki-ng/examples/test/")

local_files = [
    f"./tmp/pos_{sim_num}.dat",
    f"./tmp/sim_{sim_num}.csc",
    "./tmp/Makefile", 
    "./tmp/project-conf.h",
    "./tmp/udp-client.c", 
    "./tmp/udp-server.c"]

remote_files = [
    "positions.dat",
    "simulation.csc",
    "Makefile", 
    "project-conf.h",
    "udp-client.c", 
    "udp-server.c"]

ssh = create_ssh_client(vm_hostname, vm_port, vm_username, vm_password)
send_files_scp(ssh, local_directory, remote_directory, local_files, remote_files)
ssh.close()
print("Transfer completed.")