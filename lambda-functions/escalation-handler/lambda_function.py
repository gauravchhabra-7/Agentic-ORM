"""
ORM Platform - Escalation Handler Lambda
Sends notifications to Slack/email for comments requiring human intervention
Triggered by SQS messages from classification function
"""

import json
import sys
import os

# Add shared utilities to path
#sys.path.append('/opt/python')
#sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.utils import AWSService, lambda_response, validate_required_env_vars, logger
from datetime import datetime, timezone
import requests


def lambda_handler(event, context):
    """
    Main Lambda handler for escalation notifications
    """
    
    logger.info("Starting escalation handler process")
    
    # Validate environment variables
    required_vars = ['COMMENTS_TABLE', 'CONFIG_TABLE', 'SECRET_NAME']
    if not validate_required_env_vars(required_vars):
        return lambda_response(500, {'error': 'Missing required environment variables'})
    
    try:
        # Initialize services
        aws_service = AWSService()
        secrets = aws_service.get_secrets()
        
        processed_count = 0
        errors = []
        
        # Process each SQS record
        for record in event.get('Records', []):
            try:
                # Parse SQS message
                message_body = json.loads(record['body'])
                
                if message_body.get('action') == 'escalate':
                    comment_id = message_body['comment_id']
                    client_id = message_body['client_id']
                    classification = message_body.get('classification', {})
                    
                    logger.info(f"Processing escalation for comment: {comment_id}")
                    
                    # Process the escalation
                    success = process_escalation(
                        aws_service,
                        secrets,
                        comment_id,
                        client_id,
                        classification
                    )
                    
                    if success:
                        processed_count += 1
                    else:
                        errors.append(f"Failed to escalate comment {comment_id}")
                
                elif message_body.get('action') == 'send_notification':
                    # Handle other notification types (like hide notifications)
                    success = send_notification(aws_service, secrets, message_body)
                    if success:
                        processed_count += 1
                    else:
                        errors.append(f"Failed to send notification: {message_body.get('type', 'unknown')}")
                
            except Exception as e:
                error_msg = f"Error processing record: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log audit information
        aws_service.save_audit_log('escalation_batch_completed', {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'records_received': len(event.get('Records', [])),
            'escalations_sent': processed_count,
            'errors': errors
        })
        
        logger.info(f"Escalation processing completed: {processed_count} sent, {len(errors)} errors")
        
        return lambda_response(200, {
            'status': 'success',
            'escalations_sent': processed_count,
            'errors': len(errors)
        })
        
    except Exception as e:
        logger.error(f"Escalation handler failed: {str(e)}")
        return lambda_response(500, {'status': 'error', 'message': str(e)})


def process_escalation(aws_service: AWSService, secrets: dict, comment_id: str, 
                      client_id: str, classification: dict) -> bool:
    """
    Process escalation for a specific comment
    """
    
    try:
        # Get comment details
        comment = aws_service.get_comment(comment_id)
        if not comment:
            logger.error(f"Comment not found: {comment_id}")
            return False
        
        # Check if already escalated
        if comment.get('escalated'):
            logger.info(f"Comment already escalated: {comment_id}")
            return True
        
        # Get client notification preferences
        notification_config = aws_service.get_client_config(client_id, 'notifications')
        
        # Determine escalation urgency and channels
        escalation_level = determine_escalation_level(classification)
        
        # Send notifications
        notifications_sent = []
        
        # Send Slack notification
        if notification_config.get('slack_enabled', True):
            slack_success = send_slack_notification(
                secrets, 
                comment, 
                classification, 
                client_id, 
                escalation_level,
                notification_config
            )
            if slack_success:
                notifications_sent.append('slack')
        
        # Send email notification (if configured and high priority)
        if (notification_config.get('email_enabled', False) and 
            escalation_level in ['high', 'critical']):
            email_success = send_email_notification(
                aws_service,
                comment, 
                classification, 
                client_id, 
                escalation_level,
                notification_config
            )
            if email_success:
                notifications_sent.append('email')
        
        # Send SMS for critical issues (if configured)
        if (notification_config.get('sms_enabled', False) and 
            escalation_level == 'critical'):
            sms_success = send_sms_notification(
                aws_service,
                comment, 
                classification, 
                client_id,
                notification_config
            )
            if sms_success:
                notifications_sent.append('sms')
        
        # Update comment record
        aws_service.update_comment(comment_id, {
            'escalated': True,
            'escalation_level': escalation_level,
            'notifications_sent': notifications_sent,
            'escalation_timestamp': datetime.now(timezone.utc).isoformat(),
            'action_taken': 'escalated'
        })
        
        # Log successful escalation
        aws_service.save_audit_log('comment_escalated', {
            'comment_id': comment_id,
            'client_id': client_id,
            'escalation_level': escalation_level,
            'notifications_sent': notifications_sent,
            'classification': classification,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Successfully escalated comment: {comment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process escalation for {comment_id}: {e}")
        
        # Mark as failed
        aws_service.update_comment(comment_id, {
            'escalation_failed': True,
            'escalation_error': str(e),
            'escalation_timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return False


def determine_escalation_level(classification: dict) -> str:
    """
    Determine escalation level based on classification
    """
    
    try:
        urgency = classification.get('urgency', 'low')
        toxicity_score = classification.get('toxicity_score', 0)
        sentiment = classification.get('sentiment', 'neutral')
        intent = classification.get('intent', 'general')
        confidence = classification.get('confidence', 0)
        
        # Critical: High toxicity + high confidence
        if toxicity_score >= 8 and confidence >= 80:
            return 'critical'
        
        # Critical: Legal threats or severe complaints
        if intent == 'complaint' and urgency == 'high':
            return 'critical'
        
        # High: Medium-high toxicity or urgent issues
        if toxicity_score >= 6 or urgency == 'high':
            return 'high'
        
        # Medium: Questions, complaints, or moderate issues
        if urgency == 'medium' or intent in ['question', 'complaint']:
            return 'medium'
        
        # Low: Everything else requiring human review
        return 'low'
        
    except Exception as e:
        logger.error(f"Failed to determine escalation level: {e}")
        return 'medium'


def send_slack_notification(secrets: dict, comment: dict, classification: dict, 
                           client_id: str, escalation_level: str, config: dict) -> bool:
    """
    Send notification to Slack
    """
    
    try:
        webhook_url = secrets.get('slack_webhook_url')
        if not webhook_url or webhook_url == 'placeholder-for-now':
            logger.warning("Slack webhook URL not configured")
            return False
        
        # Build Slack message
        message = build_slack_message(comment, classification, client_id, escalation_level, config)
        
        # Send to Slack
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Sent Slack notification for comment: {comment['comment_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False


def build_slack_message(comment: dict, classification: dict, client_id: str, 
                       escalation_level: str, config: dict) -> dict:
    """
    Build Slack message payload
    """
    
    # Determine message color based on escalation level
    colors = {
        'critical': '#FF0000',  # Red
        'high': '#FF6600',      # Orange
        'medium': '#FFCC00',    # Yellow
        'low': '#00CC00'        # Green
    }
    
    color = colors.get(escalation_level, '#CCCCCC')
    
    # Build message blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 {escalation_level.upper()} Priority Comment Alert"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Client:* {client_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Platform:* {comment.get('platform', 'Unknown').title()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Sentiment:* {classification.get('sentiment', 'Unknown').title()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Toxicity:* {classification.get('toxicity_score', 0)}/10"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Comment:*\n> {comment.get('text', 'No text available')[:500]}"
            }
        }
    ]
    
    # Add author info if available
    if comment.get('author_name'):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Author:* {comment['author_name']} (ID: {comment.get('author_id', 'Unknown')})"
            }
        })
    
    # Add action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Comment"
                },
                "value": comment['comment_id'],
                "url": f"https://facebook.com/{comment['comment_id']}"  # This would be the actual comment URL
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Mark Resolved"
                },
                "value": f"resolve_{comment['comment_id']}"
            }
        ]
    })
    
    return {
        "attachments": [
            {
                "color": color,
                "blocks": blocks
            }
        ]
    }


def send_email_notification(aws_service: AWSService, comment: dict, classification: dict, 
                           client_id: str, escalation_level: str, config: dict) -> bool:
    """
    Send email notification using AWS SES
    """
    
    try:
        # For MVP, we'll use a simple email implementation
        # In production, you'd use AWS SES
        
        logger.info(f"Email notification would be sent for comment: {comment['comment_id']}")
        
        # This is a placeholder - implement actual SES integration
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False


def send_sms_notification(aws_service: AWSService, comment: dict, classification: dict, 
                         client_id: str, config: dict) -> bool:
    """
    Send SMS notification using AWS SNS
    """
    
    try:
        # For MVP, we'll use a simple SMS implementation
        # In production, you'd use AWS SNS
        
        logger.info(f"SMS notification would be sent for comment: {comment['comment_id']}")
        
        # This is a placeholder - implement actual SNS integration
        return True
        
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {e}")
        return False


def send_notification(aws_service: AWSService, secrets: dict, notification_data: dict) -> bool:
    """
    Send generic notification (for hide notifications, etc.)
    """
    
    try:
        notification_type = notification_data.get('type')
        
        if notification_type == 'comment_hidden':
            return send_hide_notification_slack(secrets, notification_data)
        
        # Add more notification types as needed
        
        logger.warning(f"Unknown notification type: {notification_type}")
        return False
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def send_hide_notification_slack(secrets: dict, notification_data: dict) -> bool:
    """
    Send Slack notification for hidden comments
    """
    
    try:
        webhook_url = secrets.get('slack_webhook_url')
        if not webhook_url or webhook_url == 'placeholder-for-now':
            return False
        
        message = {
            "text": f"🙈 Comment Hidden",
            "attachments": [
                {
                    "color": "#FF6600",
                    "fields": [
                        {
                            "title": "Client",
                            "value": notification_data.get('client_id'),
                            "short": True
                        },
                        {
                            "title": "Reason",
                            "value": notification_data.get('hide_reason'),
                            "short": True
                        },
                        {
                            "title": "Comment",
                            "value": notification_data.get('comment_text', '')[:200],
                            "short": False
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Sent hide notification to Slack")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send hide notification to Slack: {e}")
        return False


# For local testing
if __name__ == "__main__":
    # Mock SQS event for local testing
    test_event = {
        'Records': [
            {
                'body': json.dumps({
                    'action': 'escalate',
                    'comment_id': 'test_comment_123',
                    'client_id': 'test_client',
                    'classification': {
                        'urgency': 'high',
                        'sentiment': 'negative',
                        'intent': 'complaint',
                        'toxicity_score': 6,
                        'confidence': 85
                    }
                })
            }
        ]
    }
    
    class MockContext:
        def get_remaining_time_in_millis(self):
            return 30000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))