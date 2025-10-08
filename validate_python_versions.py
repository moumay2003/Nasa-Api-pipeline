#!/usr/bin/env python3
"""
Python Version Validation Script
Validates that all containers use consistent Python versions
"""

import subprocess
import sys
import json
from datetime import datetime

def run_command(command, description):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "", f"Command timed out: {command}", False
    except Exception as e:
        return "", f"Error running command: {e}", False

def validate_python_versions():
    """Validate Python versions across all containers"""
    
    print("🐍 PYTHON VERSION VALIDATION")
    print("=" * 50)
    print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    containers_to_check = [
        ("airflow-webserver", "docker-compose exec -T airflow-webserver python --version"),
        ("airflow-scheduler", "docker-compose exec -T airflow-scheduler python --version"),
        ("spark-master", "docker-compose exec -T spark-master python3 --version"),
        ("spark-worker", "docker-compose exec -T spark-worker python3 --version"),
        ("spark-worker-2", "docker-compose exec -T spark-worker-2 python3 --version"),
    ]
    
    results = {}
    all_consistent = True
    expected_version = "3.10"
    
    for container_name, command in containers_to_check:
        print(f"🔍 Checking {container_name}...")
        stdout, stderr, success = run_command(command, f"Check {container_name} Python version")
        
        if success and stdout:
            version = stdout.strip()
            results[container_name] = {"version": version, "status": "✅ Running"}
            
            # Check if version contains expected version
            if expected_version not in version:
                all_consistent = False
                print(f"   ❌ {version} (Expected Python {expected_version})")
            else:
                print(f"   ✅ {version}")
        else:
            results[container_name] = {"version": "N/A", "status": "❌ Not running or error"}
            all_consistent = False
            print(f"   ❌ Container not accessible: {stderr}")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    for container, info in results.items():
        status_icon = "✅" if "✅" in info["status"] else "❌"
        print(f"{status_icon} {container:20} | {info['version']:30} | {info['status']}")
    
    print("\n" + "=" * 50)
    if all_consistent:
        print("🎉 SUCCESS: All containers use consistent Python versions!")
        print(f"   All containers are using Python {expected_version}")
    else:
        print("⚠️  WARNING: Python version inconsistencies detected!")
        print(f"   Expected: Python {expected_version} across all containers")
        print("   Action needed: Rebuild containers with correct Python version")
    
    print("=" * 50)
    
    # Additional Spark-specific validation
    print("\n🔥 SPARK CONFIGURATION VALIDATION")
    print("-" * 30)
    
    spark_env_vars = [
        "PYSPARK_PYTHON",
        "PYSPARK_DRIVER_PYTHON"
    ]
    
    for container in ["spark-master", "spark-worker", "spark-worker-2"]:
        print(f"\n🔍 {container} environment:")
        for var in spark_env_vars:
            cmd = f"docker-compose exec -T {container} env | grep {var}"
            stdout, stderr, success = run_command(cmd, f"Check {var} in {container}")
            if success and stdout:
                print(f"   ✅ {stdout}")
            else:
                print(f"   ❌ {var} not set")
    
    return all_consistent

def check_container_status():
    """Check if all required containers are running"""
    print("\n🐳 CONTAINER STATUS CHECK")
    print("-" * 30)
    
    cmd = "docker-compose ps --format json"
    stdout, stderr, success = run_command(cmd, "Check container status")
    
    if not success:
        print("❌ Failed to check container status")
        return False
    
    try:
        # Handle both single container and multiple containers output
        if stdout.strip().startswith('['):
            containers = json.loads(stdout)
        else:
            # Multiple JSON objects, one per line
            containers = [json.loads(line) for line in stdout.strip().split('\n') if line.strip()]
        
        required_services = [
            "airflow-webserver", "airflow-scheduler", 
            "spark-master", "spark-worker", "spark-worker-2",
            "mysql", "postgres"
        ]
        
        running_services = []
        for container in containers:
            service_name = container.get('Service', 'unknown')
            state = container.get('State', 'unknown')
            if state == 'running':
                running_services.append(service_name)
            print(f"   {service_name:20} | {state}")
        
        missing_services = set(required_services) - set(running_services)
        if missing_services:
            print(f"\n❌ Missing services: {', '.join(missing_services)}")
            return False
        else:
            print(f"\n✅ All required services are running!")
            return True
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse container status: {e}")
        return False

if __name__ == "__main__":
    print("Starting Python version validation...\n")
    
    # Check container status first
    containers_ok = check_container_status()
    
    if containers_ok:
        # Validate Python versions
        versions_ok = validate_python_versions()
        
        if versions_ok:
            print("\n🎉 All validations passed! Your environment is ready.")
            sys.exit(0)
        else:
            print("\n⚠️  Some validations failed. Please check the issues above.")
            sys.exit(1)
    else:
        print("\n❌ Containers are not running properly. Please start your environment first:")
        print("   docker-compose up -d")
        sys.exit(1)