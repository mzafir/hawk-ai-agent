#!/usr/bin/env python3
"""
AgentCore CloudWatch Monitoring
"""
import boto3
import json
from datetime import datetime

class AgentCoreMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        self.logs = boto3.client('logs', region_name='us-east-1')
        self.log_group = '/aws/agentcore/hawk'
        
    def log_conversation(self, user_input, response, processing_time):
        """Log conversation to CloudWatch"""
        try:
            self.logs.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"conversations-{datetime.now().strftime('%Y-%m-%d')}",
                logEvents=[{
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'message': json.dumps({
                        'user_input': user_input,
                        'response_length': len(response),
                        'processing_time_ms': processing_time,
                        'timestamp': datetime.now().isoformat()
                    })
                }]
            )
        except: pass
    
    def send_metrics(self, metric_name, value, unit='Count'):
        """Send metrics to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='AgentCore/Hawk',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.now()
                }]
            )
        except: pass