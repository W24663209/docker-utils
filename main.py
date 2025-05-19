from flask import Flask, jsonify
import docker
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

def get_container_stats(container):
    stats = container.stats(stream=False)
    memory_stats = stats['memory_stats']
    cpu_stats = stats['cpu_stats']

    memory_usage = memory_stats['usage'] / (1024 * 1024 * 1024)  # 内存使用量（GB）
    memory_usage_formatted = "{:.2f}".format(memory_usage)  # 保留两位小数
    cpu_usage = cpu_stats['cpu_usage']['total_usage']
    system_cpu_usage = cpu_stats['system_cpu_usage']
    online_cpus = cpu_stats['online_cpus']

    cpu_percent = (cpu_usage / (system_cpu_usage / online_cpus)) * 100
    cpu_percent_ = "{:.2f}".format(cpu_percent)  # 保留两位小数
    return container.name, memory_usage_formatted, cpu_percent_

def get_container_memory_and_cpu_usage():
    client = docker.from_env()
    containers = client.containers.list(all=True)

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_container_stats, container): container for container in containers}

        stats_data = []
        for future in as_completed(futures):
            container = futures[future]
            try:
                name, memory_usage, cpu_percent = future.result()
                stats_data.append({
                    'name': name,
                    'memory_usage': memory_usage,
                    'cpu_percent': cpu_percent
                })
            except Exception as e:
                print(f"获取失败 {container.name}: {e}")
    # 按内存使用量从大到小排序
    stats_data_sorted = sorted(stats_data, key=lambda x: x['memory_usage'], reverse=True)
    return stats_data_sorted

@app.route('/containers/stats', methods=['GET'])
def get_stats():
    stats = get_container_memory_and_cpu_usage()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
