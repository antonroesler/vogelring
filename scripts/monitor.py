#!/usr/bin/env python3
"""
Simple monitoring script for Vogelring application on Raspberry Pi
Checks service health and system resources
"""
import argparse
import json
import logging
import requests
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def check_docker_services() -> Dict[str, Any]:
    """Check Docker Compose service status"""
    try:
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        services = []
        for line in result.stdout.strip().split('\n'):
            if line:
                service = json.loads(line)
                services.append({
                    'name': service.get('Service'),
                    'state': service.get('State'),
                    'status': service.get('Status'),
                    'health': service.get('Health', 'unknown')
                })
        
        return {
            'status': 'success',
            'services': services
        }
    except subprocess.CalledProcessError as e:
        return {
            'status': 'error',
            'message': f'Docker command failed: {e}',
            'services': []
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error checking Docker services: {e}',
            'services': []
        }


def check_api_health(base_url: str = 'http://localhost:8000') -> Dict[str, Any]:
    """Check API health endpoints"""
    endpoints = {
        'basic': f'{base_url}/health',
        'detailed': f'{base_url}/health/detailed',
        'ready': f'{base_url}/health/ready',
        'live': f'{base_url}/health/live'
    }
    
    results = {}
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=10)
            results[name] = {
                'status': 'success',
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'data': response.json() if response.status_code == 200 else None
            }
        except requests.exceptions.RequestException as e:
            results[name] = {
                'status': 'error',
                'message': str(e)
            }
    
    return results


def check_nginx_health(base_url: str = 'http://localhost') -> Dict[str, Any]:
    """Check nginx health"""
    try:
        response = requests.get(f'{base_url}/health', timeout=10)
        return {
            'status': 'success',
            'status_code': response.status_code,
            'response_time_ms': response.elapsed.total_seconds() * 1000
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def get_system_resources() -> Dict[str, Any]:
    """Get system resource information"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Load average
        load_avg = psutil.getloadavg()
        
        # Temperature (Raspberry Pi specific)
        temperature = None
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_raw = int(f.read().strip())
                temperature = temp_raw / 1000.0
        except (FileNotFoundError, ValueError, PermissionError):
            pass
        
        resources = {
            'cpu_percent': round(cpu_percent, 2),
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': round(memory.percent, 2)
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'percent': round((disk.used / disk.total) * 100, 2)
            },
            'load_average': {
                '1min': round(load_avg[0], 2),
                '5min': round(load_avg[1], 2),
                '15min': round(load_avg[2], 2)
            }
        }
        
        if temperature is not None:
            resources['temperature_celsius'] = round(temperature, 1)
        
        return {
            'status': 'success',
            'resources': resources
        }
    except ImportError:
        return {
            'status': 'error',
            'message': 'psutil not available'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def check_database_connection() -> Dict[str, Any]:
    """Check database connection via API"""
    try:
        response = requests.get('http://localhost:8000/health/detailed', timeout=10)
        if response.status_code == 200:
            data = response.json()
            db_check = data.get('checks', {}).get('database', {})
            return {
                'status': 'success',
                'database_status': db_check.get('status', 'unknown'),
                'message': db_check.get('message', 'No message')
            }
        else:
            return {
                'status': 'error',
                'message': f'API returned status {response.status_code}'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def generate_report() -> Dict[str, Any]:
    """Generate comprehensive monitoring report"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting monitoring check...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check Docker services
    logger.info("Checking Docker services...")
    report['checks']['docker_services'] = check_docker_services()
    
    # Check API health
    logger.info("Checking API health...")
    report['checks']['api_health'] = check_api_health()
    
    # Check nginx
    logger.info("Checking nginx...")
    report['checks']['nginx'] = check_nginx_health()
    
    # Check database
    logger.info("Checking database...")
    report['checks']['database'] = check_database_connection()
    
    # Check system resources
    logger.info("Checking system resources...")
    report['checks']['system_resources'] = get_system_resources()
    
    # Overall health assessment
    all_healthy = True
    issues = []
    
    # Check for issues
    if report['checks']['docker_services']['status'] != 'success':
        all_healthy = False
        issues.append('Docker services issue')
    
    api_health = report['checks']['api_health']
    if not all(check.get('status') == 'success' for check in api_health.values()):
        all_healthy = False
        issues.append('API health issue')
    
    if report['checks']['nginx']['status'] != 'success':
        all_healthy = False
        issues.append('Nginx issue')
    
    if report['checks']['database']['status'] != 'success':
        all_healthy = False
        issues.append('Database issue')
    
    # Check resource thresholds
    resources = report['checks']['system_resources']
    if resources['status'] == 'success':
        res_data = resources['resources']
        if res_data['cpu_percent'] > 80:
            issues.append(f"High CPU usage: {res_data['cpu_percent']}%")
        if res_data['memory']['percent'] > 85:
            issues.append(f"High memory usage: {res_data['memory']['percent']}%")
        if res_data['disk']['percent'] > 90:
            issues.append(f"High disk usage: {res_data['disk']['percent']}%")
        if 'temperature_celsius' in res_data and res_data['temperature_celsius'] > 70:
            issues.append(f"High temperature: {res_data['temperature_celsius']}°C")
    
    report['overall'] = {
        'healthy': all_healthy,
        'issues': issues
    }
    
    logger.info(f"Monitoring check complete. Overall healthy: {all_healthy}")
    if issues:
        logger.warning(f"Issues found: {', '.join(issues)}")
    
    return report


def main():
    """Main monitoring function"""
    parser = argparse.ArgumentParser(description='Vogelring monitoring script')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    parser.add_argument('--watch', '-w', type=int, metavar='SECONDS', 
                       help='Watch mode - repeat every N seconds')
    parser.add_argument('--api-url', default='http://localhost:8000', 
                       help='API base URL (default: http://localhost:8000)')
    parser.add_argument('--nginx-url', default='http://localhost', 
                       help='Nginx base URL (default: http://localhost)')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    try:
        if args.watch:
            # Watch mode - continuous monitoring
            while True:
                report = generate_report()
                
                if args.json:
                    print(json.dumps(report, indent=2))
                else:
                    print(f"\n=== Monitoring Report - {report['timestamp']} ===")
                    print(f"Overall Status: {'HEALTHY' if report['overall']['healthy'] else 'UNHEALTHY'}")
                    
                    if report['overall']['issues']:
                        print(f"Issues: {', '.join(report['overall']['issues'])}")
                    
                    # Print key metrics
                    resources = report['checks']['system_resources']
                    if resources['status'] == 'success':
                        res_data = resources['resources']
                        print(f"CPU: {res_data['cpu_percent']}% | "
                              f"Memory: {res_data['memory']['percent']}% | "
                              f"Disk: {res_data['disk']['percent']}%")
                        if 'temperature_celsius' in res_data:
                            print(f"Temperature: {res_data['temperature_celsius']}°C")
                
                time.sleep(args.watch)
        else:
            # Single check
            report = generate_report()
            
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print(f"=== Monitoring Report - {report['timestamp']} ===")
                print(f"Overall Status: {'HEALTHY' if report['overall']['healthy'] else 'UNHEALTHY'}")
                
                if report['overall']['issues']:
                    print(f"Issues: {', '.join(report['overall']['issues'])}")
                else:
                    print("No issues detected")
            
            # Exit with error code if unhealthy
            sys.exit(0 if report['overall']['healthy'] else 1)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Monitoring failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()