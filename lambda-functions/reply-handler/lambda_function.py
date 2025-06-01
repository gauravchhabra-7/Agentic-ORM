"""
ORM Platform - Reply Handler Lambda
Automatically replies to comments using predefined templates
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
import re


def lambda_handler(event, context):
    """
    Main Lambda handler for auto-reply functionality
    """
    
    logger.info("Starting reply handler process")
    
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

                # DEBUG: Log what we received
                logger.info(f"Reply handler received message: {message_body}")
                
                if message_body.get('action') == 'reply':
                    comment_id = message_body['comment_id']
                    client_id = message_body['client_id']
                    classification = message_body.get('classification', {})
                    
                    logger.info(f"Processing reply for comment: {comment_id}")
                    
                    # Process the reply
                    success = process_reply(
                        aws_service,
                        meta_client,
                        comment_id,
                        client_id,
                        classification
                    )
                    
                    if success:
                        processed_count += 1
                    else:
                        errors.append(f"Failed to reply to comment {comment_id}")
                
            except Exception as e:
                error_msg = f"Error processing record: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log audit information
        aws_service.save_audit_log('reply_batch_completed', {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'records_received': len(event.get('Records', [])),
            'replies_sent': processed_count,
            'errors': errors
        })
        
        logger.info(f"Reply processing completed: {processed_count} sent, {len(errors)} errors")
        
        return lambda_response(200, {
            'status': 'success',
            'replies_sent': processed_count,
            'errors': len(errors)
        })
        
    except Exception as e:
        logger.error(f"Reply handler failed: {str(e)}")
        return lambda_response(500, {'status': 'error', 'message': str(e)})


def process_reply(aws_service: AWSService, meta_client: MetaAPIClient,
                 comment_id: str, client_id: str, classification: dict) -> bool:
    """
    Process a reply to a specific comment
    """
    
    try:
        # Get comment details
        comment = aws_service.get_comment(comment_id)
        if not comment:
            logger.error(f"Comment not found: {comment_id}")
            return False
        
        # Check if already replied
        if comment.get('reply_sent'):
            logger.info(f"Already replied to comment: {comment_id}")
            return True
        
        # Get client configuration
        client_config = aws_service.get_client_config(client_id, 'response_templates')
        
        # Generate reply message
        reply_message = generate_reply_message(comment, classification, client_config)
        
        # Send reply via Meta API
        reply_success = meta_client.reply_to_comment(comment_id, reply_message)
        
        if reply_success:
            # Update comment record
            aws_service.update_comment(comment_id, {
                'reply_sent': True,
                'reply_message': reply_message,
                'reply_timestamp': datetime.now(timezone.utc).isoformat(),
                'action_taken': 'replied'
            })
            
            # Log successful reply
            aws_service.save_audit_log('reply_sent', {
                'comment_id': comment_id,
                'client_id': client_id,
                'reply_message': reply_message,
                'classification': classification,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Successfully replied to comment: {comment_id}")
            return True
        else:
            logger.error(f"Failed to send reply to comment: {comment_id}")
            
            # Mark as failed
            aws_service.update_comment(comment_id, {
                'reply_failed': True,
                'reply_error': 'API call failed',
                'reply_timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            return False
            
    except Exception as e:
        logger.error(f"Failed to process reply for {comment_id}: {e}")
        
        # Mark as failed
        aws_service.update_comment(comment_id, {
            'reply_failed': True,
            'reply_error': str(e),
            'reply_timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return False


def generate_reply_message(comment: dict, classification: dict, client_config: dict) -> str:
    """
    Generate appropriate reply message based on comment and classification
    """
    
    try:
        # Get template based on intent and sentiment
        template = get_reply_template(classification, client_config)
        
        # Personalize the message
        personalized_message = personalize_template(template, comment, classification)
        
        # Apply any message transformations
        final_message = apply_message_rules(personalized_message, client_config)
        
        return final_message
        
    except Exception as e:
        logger.error(f"Failed to generate reply message: {e}")
        return "Thank you for your comment! We appreciate your feedback."


def get_reply_template(classification: dict, client_config: dict) -> str:
    """
    Get appropriate reply template based on classification
    """
    
    templates = client_config.get('templates', {})
    
    # Match by intent first
    intent = classification.get('intent', 'general')
    if intent in templates:
        return templates[intent]
    
    # Match by sentiment
    sentiment = classification.get('sentiment', 'neutral')
    if sentiment in templates:
        return templates[sentiment]
    
    # Match by urgency
    urgency = classification.get('urgency', 'low')
    if urgency in templates:
        return templates[urgency]
    
    # Default template
    return templates.get('default', "Thank you for your comment! We appreciate your feedback and will respond soon.")


def personalize_template(template: str, comment: dict, classification: dict) -> str:
    """
    Personalize template with comment-specific information
    """
    
    try:
        # Get author name (if available)
        author_name = comment.get('author_name', '').split()[0] if comment.get('author_name') else ''
        
        # Define replacement variables
        replacements = {
            '{name}': author_name,
            '{first_name}': author_name,
            '{time_of_day}': get_time_of_day_greeting(),
            '{sentiment}': classification.get('sentiment', 'neutral'),
            '{platform}': comment.get('platform', 'social media').title()
        }
        
        # Apply replacements
        personalized = template
        for placeholder, value in replacements.items():
            personalized = personalized.replace(placeholder, value)
        
        # Clean up any remaining placeholders
        personalized = re.sub(r'\{[^}]+\}', '', personalized)
        
        return personalized.strip()
        
    except Exception as e:
        logger.error(f"Failed to personalize template: {e}")
        return template


def get_time_of_day_greeting() -> str:
    """
    Get appropriate greeting based on current time
    """
    
    try:
        from datetime import datetime
        
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Hello"
            
    except Exception:
        return "Hello"


def apply_message_rules(message: str, client_config: dict) -> str:
    """
    Apply client-specific message rules and formatting
    """
    
    try:
        # Apply length limits
        max_length = client_config.get('max_reply_length', 500)
        if len(message) > max_length:
            message = message[:max_length-3] + "..."
        
        # Add signature if configured
        signature = client_config.get('signature')
        if signature:
            message += f"\n\n{signature}"
        
        # Apply any text transformations
        if client_config.get('use_emojis', False):
            message = add_appropriate_emoji(message)
        
        return message
        
    except Exception as e:
        logger.error(f"Failed to apply message rules: {e}")
        return message


def add_appropriate_emoji(message: str) -> str:
    """
    Add appropriate emoji based on message content
    """
    
    try:
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['thank', 'appreciate', 'great']):
            return message + " 😊"
        elif any(word in message_lower for word in ['sorry', 'apologize', 'issue']):
            return message + " 🙏"
        elif any(word in message_lower for word in ['help', 'support', 'assist']):
            return message + " 🤝"
        else:
            return message
            
    except Exception:
        return message


# Sample client configurations for testing
def get_sample_templates():
    """Sample response templates for different scenarios"""
    return {
        'question': "Hi {name}! Thanks for your question. We'll get back to you within 2 hours with a detailed answer. 😊",
        'complaint': "Hi {name}, we're sorry to hear about your experience. We take all feedback seriously and will investigate this immediately. Please expect a response from our team within 1 hour.",
        'compliment': "Thank you so much for the kind words, {name}! We're thrilled you had a great experience. 🎉",
        'positive': "Thanks for the positive feedback, {name}! We really appreciate it! 😊",
        'negative': "We're sorry to hear this, {name}. We'll look into this right away and make it right.",
        'high': "Thank you for reaching out, {name}. This has been escalated to our priority team and you'll hear back within 30 minutes.",
        'default': "Hi {name}! Thank you for your comment. We appreciate your feedback and will respond soon."
    }


# For local testing
if __name__ == "__main__":
    # Mock SQS event for local testing
    test_event = {
        'Records': [
            {
                'body': json.dumps({
                    'action': 'reply',
                    'comment_id': 'test_comment_123',
                    'client_id': 'test_client',
                    'classification': {
                        'intent': 'question',
                        'sentiment': 'neutral',
                        'urgency': 'medium'
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