#!/usr/bin/env python3
"""
Simple alerting system for Vogelring application
Monitors critical metrics and sends notifications when thresholds are exceeded
"""
import argparse
import json
import logging
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import monitoring functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from monitor import generate_report


class AlertManager:
    """Simple alert manager for system monitoring"""
    
    def __init__(self, config_file: str = None):
        self.config = self.load_config(config_file)
        self.alert_state_file = Path(self.config.get('state_file', '/tmp/vogelring_alerts.json'))
        self.alert_states = self.load_alert_states()
        
        # Setup logging
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('vogelring.alerts')
    
    def load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load configuration from file or environment variables"""
        default_config = {
            'thresholds': {
                'cpu_percent': 85,
                'memory_percent': 90,
                'disk_percent': 95,
                'temperature_celsius': 75,
                'response_time_ms': 5000
            },
            'cooldown_minutes': 30,  # Minimum time between alerts for same issue
            'email': {
                'enabled': False,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': 'vogelring@localhost',
                'to_emails': []
            },
            'webhook': {
                'enabled': False,
                'url': '',
                'timeout': 10
            },
            'log_file': '/var/log/vogelring_alerts.log',
            'state_file': '/tmp/vogelring_alerts.json',
            'log_level': 'INFO'
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                default_config.update(file_config)
            except Exception as e:
                logging.warning(f"Could not load config file {config_file}: {e}")
        
        # Override with environment variables
        env_overrides = {
            'ALERT_CPU_THRESHOLD': ('thresholds', 'cpu_percent'),
            'ALERT_MEMORY_THRESHOLD': ('thresholds', 'memory_percent'),
            'ALERT_DISK_THRESHOLD': ('thresholds', 'disk_percent'),
            'ALERT_TEMP_THRESHOLD': ('thresholds', 'temperature_celsius'),
            'ALERT_COOLDOWN_MINUTES': ('cooldown_minutes',),
            'ALERT_EMAIL_ENABLED': ('email', 'enabled'),
            'ALERT_SMTP_SERVER': ('email', 'smtp_server'),
            'ALERT_SMTP_PORT': ('email', 'smtp_port'),
            'ALERT_EMAIL_FROM': ('email', 'from_email'),
            'ALERT_EMAIL_TO': ('email', 'to_emails'),
            'ALERT_WEBHOOK_URL': ('webhook', 'url'),
        }
        
        for env_var, config_path in env_overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the correct config section
                config_section = default_config
                for key in config_path[:-1]:
                    config_section = config_section[key]
                
                # Convert value to appropriate type
                final_key = config_path[-1]
                if final_key in ['cpu_percent', 'memory_percent', 'disk_percent', 'temperature_celsius', 'response_time_ms', 'cooldown_minutes', 'smtp_port', 'timeout']:
                    config_section[final_key] = int(value)
                elif final_key in ['enabled']:
                    config_section[final_key] = value.lower() in ('true', '1', 'yes', 'on')
                elif final_key == 'to_emails':
                    config_section[final_key] = [email.strip() for email in value.split(',')]
                else:
                    config_section[final_key] = value
        
        return default_config
    
    def load_alert_states(self) -> Dict[str, Any]:
        """Load previous alert states from file"""
        if self.alert_state_file.exists():
            try:
                with open(self.alert_state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load alert states: {e}")
        return {}
    
    def save_alert_states(self):
        """Save alert states to file"""
        try:
            with open(self.alert_state_file, 'w') as f:
                json.dump(self.alert_states, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save alert states: {e}")
    
    def should_send_alert(self, alert_key: str) -> bool:
        """Check if enough time has passed since last alert for this issue"""
        if alert_key not in self.alert_states:
            return True
        
        last_alert_time = datetime.fromisoformat(self.alert_states[alert_key]['last_sent'])
        cooldown = timedelta(minutes=self.config['cooldown_minutes'])
        
        return datetime.now() - last_alert_time > cooldown
    
    def record_alert_sent(self, alert_key: str, message: str):
        """Record that an alert was sent"""
        self.alert_states[alert_key] = {
            'last_sent': datetime.now().isoformat(),
            'message': message
        }
        self.save_alert_states()
    
    def send_email_alert(self, subject: str, message: str) -> bool:
        """Send email alert"""
        if not self.config['email']['enabled'] or not self.config['email']['to_emails']:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from_email']
            msg['To'] = ', '.join(self.config['email']['to_emails'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            if self.config['email']['username']:
                server.starttls()
                server.login(self.config['email']['username'], self.config['email']['password'])
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def send_webhook_alert(self, data: Dict[str, Any]) -> bool:
        """Send webhook alert"""
        if not self.config['webhook']['enabled'] or not self.config['webhook']['url']:
            return False
        
        try:
            import requests
            response = requests.post(
                self.config['webhook']['url'],
                json=data,
                timeout=self.config['webhook']['timeout']
            )
            response.raise_for_status()
            
            self.logger.info(f"Webhook alert sent to {self.config['webhook']['url']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    def check_and_alert(self):
        """Check system status and send alerts if needed"""
        self.logger.info("Starting alert check...")
        
        try:
            report = generate_report()
        except Exception as e:
            self.logger.error(f"Failed to generate monitoring report: {e}")
            return
        
        alerts_sent = []
        
        # Check overall health
        if not report['overall']['healthy']:
            alert_key = 'system_unhealthy'
            if self.should_send_alert(alert_key):
                subject = "🚨 Vogelring System Alert - System Unhealthy"
                message = f"""
Vogelring system is reporting as unhealthy.

Issues detected:
{chr(10).join(f"- {issue}" for issue in report['overall']['issues'])}

Timestamp: {report['timestamp']}

Please check the system immediately.
"""
                
                self.send_email_alert(subject, message)
                self.send_webhook_alert({
                    'alert_type': 'system_unhealthy',
                    'severity': 'critical',
                    'message': subject,
                    'issues': report['overall']['issues'],
                    'timestamp': report['timestamp']
                })
                
                self.record_alert_sent(alert_key, subject)
                alerts_sent.append(alert_key)
        
        # Check system resources
        resources = report['checks'].get('system_resources', {})
        if resources.get('status') == 'success':
            res_data = resources['resources']
            
            # CPU check
            cpu_percent = res_data.get('cpu_percent', 0)
            if cpu_percent > self.config['thresholds']['cpu_percent']:
                alert_key = 'high_cpu'
                if self.should_send_alert(alert_key):
                    subject = f"⚠️ Vogelring Alert - High CPU Usage ({cpu_percent}%)"
                    message = f"CPU usage is at {cpu_percent}%, exceeding threshold of {self.config['thresholds']['cpu_percent']}%"
                    
                    self.send_email_alert(subject, message)
                    self.send_webhook_alert({
                        'alert_type': 'high_cpu',
                        'severity': 'warning',
                        'value': cpu_percent,
                        'threshold': self.config['thresholds']['cpu_percent'],
                        'timestamp': report['timestamp']
                    })
                    
                    self.record_alert_sent(alert_key, subject)
                    alerts_sent.append(alert_key)
            
            # Memory check
            memory_percent = res_data.get('memory', {}).get('percent', 0)
            if memory_percent > self.config['thresholds']['memory_percent']:
                alert_key = 'high_memory'
                if self.should_send_alert(alert_key):
                    subject = f"⚠️ Vogelring Alert - High Memory Usage ({memory_percent}%)"
                    message = f"Memory usage is at {memory_percent}%, exceeding threshold of {self.config['thresholds']['memory_percent']}%"
                    
                    self.send_email_alert(subject, message)
                    self.send_webhook_alert({
                        'alert_type': 'high_memory',
                        'severity': 'warning',
                        'value': memory_percent,
                        'threshold': self.config['thresholds']['memory_percent'],
                        'timestamp': report['timestamp']
                    })
                    
                    self.record_alert_sent(alert_key, subject)
                    alerts_sent.append(alert_key)
            
            # Disk check
            disk_percent = res_data.get('disk', {}).get('percent', 0)
            if disk_percent > self.config['thresholds']['disk_percent']:
                alert_key = 'high_disk'
                if self.should_send_alert(alert_key):
                    subject = f"🚨 Vogelring Alert - High Disk Usage ({disk_percent}%)"
                    message = f"Disk usage is at {disk_percent}%, exceeding threshold of {self.config['thresholds']['disk_percent']}%"
                    
                    self.send_email_alert(subject, message)
                    self.send_webhook_alert({
                        'alert_type': 'high_disk',
                        'severity': 'critical',
                        'value': disk_percent,
                        'threshold': self.config['thresholds']['disk_percent'],
                        'timestamp': report['timestamp']
                    })
                    
                    self.record_alert_sent(alert_key, subject)
                    alerts_sent.append(alert_key)
            
            # Temperature check (Raspberry Pi)
            temperature = res_data.get('temperature_celsius')
            if temperature and temperature > self.config['thresholds']['temperature_celsius']:
                alert_key = 'high_temperature'
                if self.should_send_alert(alert_key):
                    subject = f"🌡️ Vogelring Alert - High Temperature ({temperature}°C)"
                    message = f"System temperature is at {temperature}°C, exceeding threshold of {self.config['thresholds']['temperature_celsius']}°C"
                    
                    self.send_email_alert(subject, message)
                    self.send_webhook_alert({
                        'alert_type': 'high_temperature',
                        'severity': 'warning',
                        'value': temperature,
                        'threshold': self.config['thresholds']['temperature_celsius'],
                        'timestamp': report['timestamp']
                    })
                    
                    self.record_alert_sent(alert_key, subject)
                    alerts_sent.append(alert_key)
        
        # Check API response times
        api_health = report['checks'].get('api_health', {})
        for endpoint, data in api_health.items():
            if data.get('status') == 'success':
                response_time = data.get('response_time_ms', 0)
                if response_time > self.config['thresholds']['response_time_ms']:
                    alert_key = f'slow_api_{endpoint}'
                    if self.should_send_alert(alert_key):
                        subject = f"⏱️ Vogelring Alert - Slow API Response ({endpoint})"
                        message = f"API endpoint {endpoint} response time is {response_time}ms, exceeding threshold of {self.config['thresholds']['response_time_ms']}ms"
                        
                        self.send_email_alert(subject, message)
                        self.send_webhook_alert({
                            'alert_type': 'slow_api',
                            'severity': 'warning',
                            'endpoint': endpoint,
                            'value': response_time,
                            'threshold': self.config['thresholds']['response_time_ms'],
                            'timestamp': report['timestamp']
                        })
                        
                        self.record_alert_sent(alert_key, subject)
                        alerts_sent.append(alert_key)
        
        if alerts_sent:
            self.logger.warning(f"Sent {len(alerts_sent)} alerts: {', '.join(alerts_sent)}")
        else:
            self.logger.info("No alerts needed - system is healthy")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Vogelring alerting system')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--daemon', '-d', action='store_true', help='Run as daemon')
    parser.add_argument('--interval', '-i', type=int, default=300, help='Check interval in seconds (daemon mode)')
    parser.add_argument('--test', '-t', action='store_true', help='Test alert configuration')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        alert_manager = AlertManager(args.config)
        
        if args.test:
            print("Testing alert configuration...")
            print(f"Configuration: {json.dumps(alert_manager.config, indent=2)}")
            
            # Test email if configured
            if alert_manager.config['email']['enabled']:
                success = alert_manager.send_email_alert(
                    "Vogelring Alert Test",
                    "This is a test alert from the Vogelring monitoring system."
                )
                print(f"Email test: {'SUCCESS' if success else 'FAILED'}")
            
            # Test webhook if configured
            if alert_manager.config['webhook']['enabled']:
                success = alert_manager.send_webhook_alert({
                    'alert_type': 'test',
                    'message': 'Test alert from Vogelring monitoring system',
                    'timestamp': datetime.now().isoformat()
                })
                print(f"Webhook test: {'SUCCESS' if success else 'FAILED'}")
            
            return
        
        if args.daemon:
            print(f"Starting alert daemon with {args.interval}s interval...")
            try:
                while True:
                    alert_manager.check_and_alert()
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nAlert daemon stopped by user")
        else:
            alert_manager.check_and_alert()
    
    except Exception as e:
        logging.error(f"Alert system failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()