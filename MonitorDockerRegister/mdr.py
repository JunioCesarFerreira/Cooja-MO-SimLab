import csv
import subprocess
import time
from datetime import datetime
import argparse

def parse_stats(output_line):
    parts = output_line.split()
    return {
        "container": parts[1],
        "cpu": parts[2],
        "mem_usage": parts[3],
        "mem_limit": parts[5],
        "mem_perc": parts[6],
        "net_io": parts[7],
        "block_io": parts[8],
        "pids": parts[9] if len(parts) > 9 else ""
    }

def monitor(interval, duration, output_file="docker_stats.csv"):
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["timestamp", "container", "cpu", "mem_usage", "mem_limit", "mem_perc", "net_io", "block_io", "pids"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                result = subprocess.run(["docker", "stats", "--no-stream", "--no-trunc"],
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                timestamp = datetime.now().isoformat()

                for line in lines:
                    stats = parse_stats(line)
                    stats["timestamp"] = timestamp
                    writer.writerow(stats)

                time.sleep(interval)
            except Exception as e:
                print(f"Erro durante coleta de métricas: {e}")
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitoramento de containers via docker stats.")
    parser.add_argument("-i", type=int, default=5, help="Intervalo entre coletas (segundos)")
    parser.add_argument("-d", type=int, default=300, help="Duração total do monitoramento (segundos)")
    parser.add_argument("-o", type=str, default="docker_stats.csv", help="Arquivo de saída CSV")
    
    args = parser.parse_args()
    monitor(interval=args.interval, duration=args.duration, output_file=args.output)
