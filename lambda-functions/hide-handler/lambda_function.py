"""
ORM Platform - Hide Handler Lambda
Automatically hides toxic or inappropriate comments
Triggered by SQS messages from classification function
"""

import json
import sys
import os

# Add shared utilities to path
#sys.path.append('/opt/python')
#sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.utils import AWSService, MetaAPIClient, lambda_response, validate_required_env_vars, logger
from datetime import datetime, timezone


def lambda_handler(event, context):
    """
    Main Lambda handler for comment hiding functionality
    """
    
    logger.info("Starting hide handler process")
    
    # Validate environment variables
    required_vars = ['COMMENTS_TABLE', 'CONFIG_TABLE', 'SECRET_NAME']
    if not validate_required_env_vars(required_vars):
        return lambda_response(500, {'error': 'Missing required environment variables'})
    
    try:
        # Initialize services
        aws_service = AWSService()
        secrets = aws_service.get_secrets()
        
        # Initialize Meta API client
        meta_client = MetaAPIClient(secrets['meta_access_token'])
        
        processed_count = 0
        errors = []
        
        # Process each SQS record
        for record in event.get('Records', []):
            try:
                # Parse SQS message
                message_body = json.loads(record['body'])
                
                if message_body.get('action') == 'hide':
                    comment_id = message_body['comment_id']
                    client_id = message_body['client_id']
                    classification = message_body.get('classification', {})
                    
                    logger.info(f"Processing hide for comment: {comment_id}")
                    
                    # Process the hide action
                    success = process_hide(
                        aws_service,
                        meta_client,
                        comment_id,
                        client_id,
                        classification
                    )
                    
                    if success:
                        processed_count += 1
                    else:
                        errors.append(f"Failed to hide comment {comment_id}")
                
            except Exception as e:
                error_msg = f"Error processing record: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log audit information
        aws_service.save_audit_log('hide_batch_completed', {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'records_received': len(event.get('Records', [])),
            'comments_hidden': processed_count,
            'errors': errors
        })
        
        logger.info(f"Hide processing completed: {processed_count} hidden, {len(errors)} errors")
        
        return lambda_response(200, {
            'status': 'success',
            'comments_hidden': processed_count,
            'errors': len(errors)
        })
        
    except Exception as e:
        logger.error(f"Hide handler failed: {str(e)}")
        return lambda_response(500, {'status': 'error', 'message': str(e)})


def process_hide(aws_service: AWSService, meta_client: MetaAPIClient,
                comment_id: str, client_id: str, classification: dict) -> bool:
    """
    Process hiding a specific comment
    """
    
    try:
        # Get comment details
        comment = aws_service.get_comment(comment_id)
        if not comment:
            logger.error(f"Comment not found: {comment_id}")
            return False
        
        # Check if already hidden
        if comment.get('hidden'):
            logger.info(f"Comment already hidden: {comment_id}")
            return True
        
        # Get client configuration for hiding rules
        client_config = aws_service.get_client_config(client_id, 'moderation_rules')
        
        # Verify hide criteria
        should_hide = verify_hide_criteria(comment, classification, client_config)
        
        if not should_hide:
            logger.info(f"Comment does not meet hide criteria: {comment_id}")
            # Update status but don't hide
            aws_service.update_comment(comment_id, {
                'hide_reviewed': True,
                'hide_decision': 'no_action',
                'hide_timestamp': datetime.now(timezone.utc).isoformat()
            })
            return True
        
        # Hide comment via Meta API
        hide_success = meta_client.hide_comment(comment_id)
        
        if hide_success:
            # Update comment record
            aws_service.update_comment(comment_id, {
                'hidden': True,
                'hide_reason': get_hide_reason(classification),
                'hide_timestamp': datetime.now(timezone.utc).isoformat(),
                'action_taken': 'hidden'
            })
            
            # Log successful hide
            aws_service.save_audit_log('comment_hidden', {
                'comment_id': comment_id,
                'client_id': client_id,
                'hide_reason': get_hide_reason(classification),
                'classification': classification,
                'comment_text': comment.get('text', '')[:100],  # First 100 chars for audit
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Send notification if configured
            send_hide_notification(aws_service, comment, classification, client_id)
            
            logger.info(f"Successfully hidden comment: {comment_id}")
            return True
        else:
            logger.error(f"Failed to hide comment via API: {comment_id}")
            
            # Mark as failed
            aws_service.update_comment(comment_id, {
                'hide_failed': True,
                'hide_error': 'API call failed',
                'hide_timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            return False
            
    except Exception as e:
        logger.error(f"Failed to process hide for {comment_id}: {e}")
        
        # Mark as failed
        aws_service.update_comment(comment_id, {
            'hide_failed': True,
            'hide_error': str(e),
            'hide_timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return False


def verify_hide_criteria(comment: dict, classification: dict, client_config: dict) -> bool:
    """
    Verify if comment meets criteria for hiding
    """
    
    try:
        # Check toxicity score threshold
        toxicity_threshold = client_config.get('auto_hide_threshold', 7)
        if classification.get('toxicity_score', 0) >= toxicity_threshold:
            return True
        
        # Check for banned keywords
        banned_keywords = client_config.get('banned_keywords', [])
        comment_text = comment.get('text', '').lower()
        
        for keyword in banned_keywords:
            if keyword.lower() in comment_text:
                logger.info(f"Comment contains banned keyword: {keyword}")
                return True
        
        # Check for spam patterns
        if classification.get('intent') == 'spam':
            spam_threshold = client_config.get('spam_confidence_threshold', 80)
            if classification.get('confidence', 0) >= spam_threshold:
                return True
        
        # Check repeat offender
        if is_repeat_offender(comment, client_config):
            return True
        
        # Check for specific violation types
        violation_types = client_config.get('auto_hide_violations', [])
        if any(violation in get_violation_types(classification) for violation in violation_types):
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to verify hide criteria: {e}")
        return False


def get_hide_reason(classification: dict) -> str:
    """
    Generate human-readable hide reason
    """
    
    try:
        reasons = []
        
        toxicity_score = classification.get('toxicity_score', 0)
        if toxicity_score >= 8:
            reasons.append(f"High toxicity score ({toxicity_score}/10)")
        elif toxicity_score >= 6:
            reasons.append(f"Moderate toxicity score ({toxicity_score}/10)")
        
        if classification.get('intent') == 'spam':
            reasons.append("Identified as spam")
        
        if classification.get('sentiment') == 'negative' and classification.get('urgency') == 'high':
            reasons.append("Negative high-urgency content")
        
        if not reasons:
            reasons.append("Automated moderation rule triggered")
        
        return "; ".join(reasons)
        
    except Exception:
        return "Automated moderation"


def is_repeat_offender(comment: dict, client_config: dict) -> bool:
    """
    Check if comment author is a repeat offender
    """
    
    try:
        # For MVP, implement simple check
        # In production, you'd check comment history
        
        repeat_threshold = client_config.get('repeat_offender_threshold', 3)
        
        # This would be implemented with a proper user tracking system
        # For now, return False
        return False
        
    except Exception as e:
        logger.error(f"Failed to check repeat offender: {e}")
        return False


def get_violation_types(classification: dict) -> list:
    """
    Extract violation types from classification
    """
    
    try:
        violations = []
        
        if classification.get('toxicity_score', 0) >= 7:
            violations.append('toxicity')
        
        if classification.get('intent') == 'spam':
            violations.append('spam')
        
        if classification.get('sentiment') == 'negative' and classification.get('urgency') == 'high':
            violations.append('harassment')
        
        # Add more violation detection logic here
        
        return violations
        
    except Exception:
        return []


def send_hide_notification(aws_service: AWSService, comment: dict, 
                          classification: dict, client_id: str):
    """
    Send notification about hidden comment to client team
    """
    
    try:
        # Get notification preferences
        notification_config = aws_service.get_client_config(client_id, 'notifications')
        
        if not notification_config.get('hide_notifications_enabled', True):
            return
        
        # Prepare notification data
        notification_data = {
            'action': 'send_notification',
            'type': 'comment_hidden',
            'comment_id': comment['comment_id'],
            'client_id': client_id,
            'comment_text': comment.get('text', '')[:200],  # First 200 chars
            'hide_reason': get_hide_reason(classification),
            'toxicity_score': classification.get('toxicity_score', 0),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Send to escalation queue for notification
        aws_service.send_to_queue(notification_data)
        
        logger.info(f"Sent hide notification for comment: {comment['comment_id']}")
        
    except Exception as e:
        logger.error(f"Failed to send hide notification: {e}")


# For local testing
if __name__ == "__main__":
    # Mock SQS event for local testing
    test_event = {
        'Records': [
            {
                'body': json.dumps({
                    'action': 'hide',
                    'comment_id': 'test_comment_123',
                    'client_id': 'test_client',
                    'classification': {
                        'toxicity_score': 8,
                        'sentiment': 'negative',
                        'intent': 'spam',
                        'confidence': 90
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