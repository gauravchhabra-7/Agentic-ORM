"""
ORM Platform - Comment Classification Lambda
Uses OpenAI to classify comments and determine appropriate actions
Triggered by SQS messages from ingestion function
"""

import json
import sys
import os

# Add shared utilities to path
#sys.path.append('/opt/python')
#sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.utils import AWSService, OpenAIClient, lambda_response, validate_required_env_vars, logger
from datetime import datetime, timezone
import uuid


def lambda_handler(event, context):
    """
    Main Lambda handler for comment classification
    Processes SQS messages containing comment IDs
    """
    
    logger.info("Starting comment classification process")
    
    # Validate environment variables
    required_vars = ['COMMENTS_TABLE', 'CONFIG_TABLE', 'QUEUE_URL', 'SECRET_NAME']
    if not validate_required_env_vars(required_vars):
        return lambda_response(500, {'error': 'Missing required environment variables'})
    
    try:
        # Initialize services
        aws_service = AWSService()
        secrets = aws_service.get_secrets()
        
        # Initialize OpenAI client
        openai_client = OpenAIClient(secrets['openai_api_key'])
        
        processed_count = 0
        errors = []
        
        # Process each SQS record
        for record in event.get('Records', []):
            try:
                # Parse SQS message
                message_body = json.loads(record['body'])
                
                # Only process classify_comment actions
                if message_body.get('action') != 'classify_comment':
                    continue
                    
                comment_id = message_body['comment_id']
                client_id = message_body['client_id'] 
                       
                logger.info(f"Processing comment: {comment_id}")
                
                # Classify the comment
                success = classify_comment(
                    aws_service, 
                    openai_client, 
                    comment_id, 
                    client_id
                )
                
                if success:
                    processed_count += 1
                else:
                    errors.append(f"Failed to classify comment {comment_id}")
                
            except Exception as e:
                error_msg = f"Error processing record: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log audit information
        aws_service.save_audit_log('classification_batch_completed', {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'records_received': len(event.get('Records', [])),
            'records_processed': processed_count,
            'errors': errors,
            'execution_duration_ms': context.get_remaining_time_in_millis()
        })
        
        logger.info(f"Classification completed: {processed_count} processed, {len(errors)} errors")
        
        return lambda_response(200, {
            'status': 'success',
            'processed': processed_count,
            'errors': len(errors)
        })
        
    except Exception as e:
        logger.error(f"Classification batch failed: {str(e)}")
        
        # Log error for monitoring
        aws_service.save_audit_log('classification_batch_error', {
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return lambda_response(500, {
            'status': 'error',
            'message': str(e)
        })


def classify_comment(aws_service: AWSService, openai_client: OpenAIClient, 
                    comment_id: str, client_id: str) -> bool:
    """
    Classify a single comment and determine the appropriate action
    """
    
    try:
        # Get comment from database
        comment = aws_service.get_comment(comment_id)
        if not comment:
            logger.error(f"Comment not found: {comment_id}")
            return False
        
        # Get client-specific classification rules
        client_config = aws_service.get_client_config(client_id, 'classification_rules')
        business_context = client_config.get('business_context', '')
        
        # Classify using OpenAI
        classification = openai_client.classify_comment(
            comment['text'], 
            business_context
        )
        
        # Apply client-specific rules and thresholds
        refined_classification = apply_client_rules(classification, client_config)
        
        # Determine action based on classification
        action = determine_action(refined_classification, client_config)
        
        # Update comment with classification results
        update_data = {
            'classification': refined_classification,
            'suggested_action': action,
            'status': 'classified',
            'classification_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        success = aws_service.update_comment(comment_id, update_data)
        
        if success:
            # Queue for action if needed
            if action != 'ignore':
                queue_for_action(aws_service, comment_id, client_id, action, refined_classification)
            
            # Log successful classification
            aws_service.save_audit_log('comment_classified', {
                'comment_id': comment_id,
                'client_id': client_id,
                'classification': refined_classification,
                'action': action,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Classified comment {comment_id}: {action}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to classify comment {comment_id}: {e}")
        
        # Mark comment as classification failed
        aws_service.update_comment(comment_id, {
            'status': 'classification_failed',
            'error': str(e),
            'classification_timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return False


def apply_client_rules(classification: dict, client_config: dict) -> dict:
    """
    Apply client-specific rules to refine classification
    """
    
    refined = classification.copy()
    
    try:
        # Apply toxicity threshold overrides
        toxicity_threshold = client_config.get('toxicity_threshold', 7)
        if refined['toxicity_score'] >= toxicity_threshold:
            refined['suggested_action'] = 'hide'
        
        # Apply urgency rules
        urgency_keywords = client_config.get('urgency_keywords', [])
        comment_text = refined.get('comment_text', '').lower()
        
        for keyword in urgency_keywords:
            if keyword.lower() in comment_text:
                refined['urgency'] = 'high'
                break
        
        # Apply sentiment overrides
        positive_keywords = client_config.get('positive_keywords', [])
        negative_keywords = client_config.get('negative_keywords', [])
        
        for keyword in positive_keywords:
            if keyword.lower() in comment_text:
                refined['sentiment'] = 'positive'
                break
        
        for keyword in negative_keywords:
            if keyword.lower() in comment_text:
                refined['sentiment'] = 'negative'
                break
        
        # Apply custom intent detection
        intent_keywords = client_config.get('intent_keywords', {})
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword.lower() in comment_text:
                    refined['intent'] = intent
                    break
        
        # Apply business hours response rules
        business_hours = client_config.get('business_hours', {})
        if business_hours and should_respond_in_business_hours(business_hours):
            if refined['requires_response']:
                refined['urgency'] = max(refined['urgency'], 'medium')
        
        logger.debug(f"Applied client rules: {refined}")
        return refined
        
    except Exception as e:
        logger.error(f"Failed to apply client rules: {e}")
        return classification


def determine_action(classification: dict, client_config: dict) -> str:
    """
    Determine the appropriate action based on classification and client config
    """
    
    try:
        # Priority 1: Hide toxic content
        if classification['toxicity_score'] >= client_config.get('auto_hide_threshold', 7):
            return 'hide'
        
        # Priority 2: Escalate high-urgency issues
        if classification['urgency'] == 'high':
            return 'escalate'
        
        # Priority 3: Auto-reply to questions and complaints
        if classification['requires_response'] and client_config.get('auto_reply_enabled', True):
            if classification['intent'] in ['question', 'complaint']:
                return 'reply'
        
        # Priority 4: Monitor medium urgency items
        if classification['urgency'] == 'medium':
            return 'escalate'  # Send to human for review
        
        # Priority 5: Escalate if confidence is low
        if classification['confidence'] < client_config.get('min_confidence_threshold', 70):
            return 'escalate'
        
        # Default: ignore (log but take no action)
        return 'ignore'
        
    except Exception as e:
        logger.error(f"Failed to determine action: {e}")
        return 'escalate'  # Fail-safe to human review


def should_respond_in_business_hours(business_hours: dict) -> bool:
    """
    Check if current time is within business hours
    """
    
    try:
        from datetime import datetime
        import pytz
        
        timezone_str = business_hours.get('timezone', 'UTC')
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        
        current_day = current_time.strftime('%A').lower()
        current_hour = current_time.hour
        
        day_hours = business_hours.get('hours', {}).get(current_day)
        
        if day_hours:
            start_hour = int(day_hours.get('start', '9').split(':')[0])
            end_hour = int(day_hours.get('end', '17').split(':')[0])
            
            return start_hour <= current_hour <= end_hour
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to check business hours: {e}")
        return True  # Default to always respond if check fails


def queue_for_action(aws_service: AWSService, comment_id: str, client_id: str, 
                    action: str, classification: dict):
    """
    Queue comment for specific action (reply, hide, escalate)
    """
    
    try:
        message = {
            'action': action,
            'comment_id': comment_id,
            'client_id': client_id,
            'classification': classification,
            'queued_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Add delay for non-urgent items
        delay_seconds = 0
        if classification['urgency'] == 'low':
            delay_seconds = 300  # 5 minutes
        elif classification['urgency'] == 'medium':
            delay_seconds = 60   # 1 minute
        
        success = aws_service.send_to_queue(message, delay_seconds)
        
        if success:
            logger.info(f"Queued {action} for comment {comment_id}")
        else:
            logger.error(f"Failed to queue {action} for comment {comment_id}")
        
    except Exception as e:
        logger.error(f"Failed to queue action: {e}")


def get_template_for_classification(client_config: dict, classification: dict) -> str:
    """
    Get appropriate response template based on classification
    """
    
    try:
        templates = client_config.get('response_templates', {})
        
        # Match by intent first
        intent_template = templates.get(classification['intent'])
        if intent_template:
            return intent_template
        
        # Match by sentiment
        sentiment_template = templates.get(classification['sentiment'])
        if sentiment_template:
            return sentiment_template
        
        # Default template
        return templates.get('default', "Thank you for your comment. We'll get back to you soon!")
        
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        return "Thank you for your comment. We'll get back to you soon!"


# For local testing
if __name__ == "__main__":
    # Mock SQS event for local testing
    test_event = {
        'Records': [
            {
                'body': json.dumps({
                    'action': 'classify_comment',
                    'comment_id': 'test_comment_123',
                    'client_id': 'test_client'
                })
            }
        ]
    }
    
    class MockContext:
        def get_remaining_time_in_millis(self):
            return 30000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))