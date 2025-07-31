import os
import time
from git import Repo
from prometheus_api_client import PrometheusConnect

# --- Configuration ---
# ============================ IMPORTANT ============================
# Based on your tree structure, this is the correct path.
# This is the root folder of your project that contains the .git directory.
GIT_REPO_PATH = '/Users/dp/Documents/capstone-project'
# =================================================================

# The URL to your Prometheus server (we exposed it on localhost)
PROMETHEUS_URL = 'http://localhost:9090'
# The CPU usage threshold that will trigger a move (e.g., 20%)
CPU_THRESHOLD = 20.0

def get_edge_cpu_usage(prom):
    """Queries Prometheus for the CPU usage of the edge node."""
    try:
        # This is a PromQL query to get CPU usage.
        # It might need adjustment based on your specific metrics.
        query = '100 * (1 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m]))))'
        result = prom.custom_query(query=query)
        if result:
            # Extract the CPU value
            cpu_usage = float(result[0]['value'][1])
            print(f"INFO: Current Edge CPU Usage: {cpu_usage:.2f}%")
            return cpu_usage
    except Exception as e:
        print(f"ERROR: Could not connect to Prometheus or query failed: {e}")
        return None
    return 0.0 # Default to 0 if no metrics found

def update_git_repository(move_to_cloud):
    """Edits the replica counts in the YAML files and pushes to Git."""
    print("INFO: Updating Git repository...")
    repo = Repo(GIT_REPO_PATH)

    # Define the paths to the deployment files based on your structure
    # CORRECTED PATHS:
    edge_deployment_path = os.path.join(GIT_REPO_PATH, 'Edge', 'deployment.yaml')
    cloud_deployment_path = os.path.join(GIT_REPO_PATH, 'Cloud', 'deployment.yaml')

    # Read and update the edge deployment file
    with open(edge_deployment_path, 'r') as f:
        edge_content = f.read()
    
    # Read and update the cloud deployment file
    with open(cloud_deployment_path, 'r') as f:
        cloud_content = f.read()

    if move_to_cloud:
        print("INFO: Decision: Move application to CLOUD.")
        new_edge_content = edge_content.replace('replicas: 1', 'replicas: 0')
        new_cloud_content = cloud_content.replace('replicas: 0', 'replicas: 1')
        commit_message = "feat(orchestrator): moving app from edge to cloud"
    else:
        print("INFO: Decision: Move application to EDGE.")
        new_edge_content = edge_content.replace('replicas: 0', 'replicas: 1')
        new_cloud_content = cloud_content.replace('replicas: 1', 'replicas: 0')
        commit_message = "feat(orchestrator): moving app from cloud to edge"
    
    # Write the changes back to the files
    with open(edge_deployment_path, 'w') as f:
        f.write(new_edge_content)
    with open(cloud_deployment_path, 'w') as f:
        f.write(new_cloud_content)

    # Commit and push the changes
    repo.index.add([edge_deployment_path, cloud_deployment_path])
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    origin.push()
    print("INFO: Git push successful!")


def main():
    """The main loop for the orchestrator."""
    print("--- Aether Orchestrator Brain Initializing ---")
    prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)
    
    while True:
        cpu_usage = get_edge_cpu_usage(prom)
        
        if cpu_usage is not None:
            if cpu_usage > CPU_THRESHOLD:
                # If CPU is high, move to cloud
                update_git_repository(move_to_cloud=True)
            else:
                # If CPU is low, move back to edge
                update_git_repository(move_to_cloud=False)
        
        print("INFO: Check complete. Waiting for next cycle (60 seconds)...")
        time.sleep(60)

if __name__ == "__main__":
    main()
