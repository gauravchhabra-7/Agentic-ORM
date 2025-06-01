"""
Shared utilities for ORM Platform Lambda functions
Handles AWS services, API integrations, and common operations
"""

import json
import boto3
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AWSService:
    """Handles all AWS service interactions"""
    
    def __init__(self):
        # AWS Lambda automatically provides AWS_REGION, or we can detect it
        self.region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION', 'ap-south-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.sqs = boto3.client('sqs', region_name=self.region)
        self.secrets = boto3.client('secretsmanager', region_name=self.region)
        
        # Table names from environment variables
        self.comments_table = os.environ.get('COMMENTS_TABLE')
        self.config_table = os.environ.get('CONFIG_TABLE')
        self.audit_table = os.environ.get('AUDIT_TABLE')
        self.queue_url = os.environ.get('QUEUE_URL')
    
    def get_secrets(self) -> Dict[str, str]:
        """Retrieve API keys from Secrets Manager"""
        try:
            secret_name = os.environ.get('SECRET_NAME', 'orm-platform-api-keys-dev')
            response = self.secrets.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Failed to retrieve secrets: {e}")
            raise
    
    def save_comment(self, comment_data: Dict[str, Any]) -> bool:
        """Save comment to DynamoDB"""
        try:
            table = self.dynamodb.Table(self.comments_table)
            
            # Add metadata
            comment_data.update({
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending'
            })
            
            table.put_item(Item=comment_data)
            logger.info(f"Saved comment: {comment_data.get('comment_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to save comment: {e}")
            return False
    
    def get_comment(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve comment from DynamoDB"""
        try:
            table = self.dynamodb.Table(self.comments_table)
            response = table.get_item(Key={'comment_id': comment_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get comment {comment_id}: {e}")
            return None
    
    def update_comment(self, comment_id: str, updates: Dict[str, Any]) -> bool:
        """Update comment in DynamoDB"""
        try:
            table = self.dynamodb.Table(self.comments_table)
            
            # Build update expression with reserved keyword handling
            update_expr = "SET updated_at = :updated_at"
            expr_values = {':updated_at': datetime.now(timezone.utc).isoformat()}
            expr_names = {}
            
            for key, value in updates.items():
                safe_key = f"#{key}"
                update_expr += f", {safe_key} = :{key}"
                expr_values[f":{key}"] = value
                expr_names[safe_key] = key
            
            table.update_item(
                Key={'comment_id': comment_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values,
                ExpressionAttributeNames=expr_names
            )
            
            logger.info(f"Updated comment {comment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update comment {comment_id}: {e}")
            return False
    
    def get_client_config(self, client_id: str, config_type: str) -> Optional[Dict[str, Any]]:
        """Get client configuration from DynamoDB"""
        try:
            table = self.dynamodb.Table(self.config_table)
            response = table.get_item(
                Key={'client_id': client_id, 'config_type': config_type}
            )
            return response.get('Item', {}).get('config', {})
        except Exception as e:
            logger.error(f"Failed to get config for {client_id}: {e}")
            return {}
    
    def save_audit_log(self, action_type: str, details: Dict[str, Any]) -> bool:
        """Save audit log to DynamoDB"""
        try:
            table = self.dynamodb.Table(self.audit_table)
            
            log_entry = {
                'log_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action_type': action_type,
                'details': details
            }
            
            table.put_item(Item=log_entry)
            logger.info(f"Saved audit log: {action_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
            return False
    
    def send_to_queue(self, message: Dict[str, Any], delay_seconds: int = 0) -> bool:
        """Send message to SQS queue"""
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message),
                DelaySeconds=delay_seconds
            )
            
            logger.info(f"Sent message to queue: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to queue: {e}")
            return False


class MetaAPIClient:
    """Handles Meta Graph API interactions"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v23.0"
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    def get_page_posts(self, page_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Get recent posts from a Facebook page"""
        import requests
        
        try:
            url = f"{self.base_url}/{page_id}/posts"
            params = {
                'fields': 'id,message,created_time,comments.limit(100){id,message,created_time,from,like_count}',
                'limit': limit,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Failed to get page posts: {e}")
            return []
    
    def get_ad_comments(self, ad_account_id: str) -> List[Dict[str, Any]]:
        """Get comments from ad campaigns"""
        import requests
        
        try:
            # Get ad campaigns first
            url = f"{self.base_url}/act_{ad_account_id}/campaigns"
            params = {
                'fields': 'id,name,status',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            campaigns = response.json().get('data', [])
            all_comments = []
            
            # Get comments for each campaign
            for campaign in campaigns[:5]:  # Limit to 5 campaigns for MVP
                campaign_comments = self._get_campaign_comments(campaign['id'])
                all_comments.extend(campaign_comments)
            
            return all_comments
            
        except Exception as e:
            logger.error(f"Failed to get ad comments: {e}")
            return []
    
    def _get_campaign_comments(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get comments for a specific campaign"""
        import requests
        
        try:
            # This is a simplified version - actual implementation depends on your ad structure
            url = f"{self.base_url}/{campaign_id}/insights"
            params = {
                'fields': 'ad_id',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # For MVP, return mock data structure
            # In production, you'd iterate through ads and get their comments
            return []
            
        except Exception as e:
            logger.error(f"Failed to get campaign comments: {e}")
            return []
    
    def reply_to_comment(self, comment_id: str, message: str) -> bool:
        """Reply to a comment"""
        import requests
        
        try:
            url = f"{self.base_url}/{comment_id}/replies"
            params = {
                'message': message,
                'access_token': self.access_token
            }
            
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            logger.info(f"Replied to comment {comment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reply to comment {comment_id}: {e}")
            return False
    
    def hide_comment(self, comment_id: str) -> bool:
        """Hide a comment from public view"""
        import requests
        
        try:
            url = f"{self.base_url}/{comment_id}"
            data = {
                'is_hidden': 'true',
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            logger.info(f"Hidden comment {comment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to hide comment {comment_id}: {e}")
            return False
        
    def get_instagram_media_comments(self, instagram_account_id: str, since_time=None) -> List[Dict[str, Any]]:
        """
        Auto-detect all new comments across all Instagram media posts
        Uses proper Media → Comments edge pattern
        """
        import requests
        from datetime import datetime, timezone, timedelta
        
        try:
            all_comments = []
            
            # Step 1: Get all media from Instagram account
            media_url = f"{self.base_url}/{instagram_account_id}/media"
            media_params = {
                'fields': 'id,caption,media_type,timestamp,permalink',
                'limit': 50,  # Get recent 50 posts
                'access_token': self.access_token
            }
            
            logger.info(f"Fetching Instagram media for account {instagram_account_id}")
            media_response = requests.get(media_url, params=media_params)
            media_response.raise_for_status()
            
            media_list = media_response.json().get('data', [])
            logger.info(f"Found {len(media_list)} Instagram media posts")
            
            # Step 2: For each media, get its comments using the edge
            for media in media_list:
                media_id = media.get('id')
                media_timestamp = media.get('timestamp')
                
                # Get comments for this specific media
                comments_url = f"{self.base_url}/{media_id}/comments"
                comments_params = {
                    'fields': 'id,text,timestamp,like_count,user{id,username},replies{id,text,timestamp,user{username}}',
                    'limit': 100,  # Get up to 100 comments per post
                    'access_token': self.access_token
                }
                
                try:
                    comments_response = requests.get(comments_url, params=comments_params)
                    comments_response.raise_for_status()
                    
                    media_comments = comments_response.json().get('data', [])
                    
                    # Filter for new comments since last ingestion
                    for comment in media_comments:
                        comment_time = comment.get('timestamp')
                        
                        # Skip old comments if since_time is specified
                        if since_time and comment_time:
                            fixed_time = comment_time.replace('Z', '+00:00').replace('+0000', '+00:00')
                            comment_dt = datetime.fromisoformat(fixed_time)
                            if comment_dt <= since_time:
                                continue
                        
                        # Standardize comment format for ORM processing
                        standardized_comment = {
                            'comment_id': comment.get('id'),
                            'platform': 'instagram',
                            'media_id': media_id,
                            'media_type': media.get('media_type'),
                            'media_permalink': media.get('permalink'),
                            'text': comment.get('text', ''),
                            'author_id': comment.get('user', {}).get('id', ''),
                            'author_username': comment.get('user', {}).get('username', ''),
                            'created_time': comment.get('timestamp', ''),
                            'like_count': comment.get('like_count', 0),
                            'has_replies': len(comment.get('replies', {}).get('data', [])) > 0,
                            'raw_data': comment
                        }
                        
                        all_comments.append(standardized_comment)
                        
                    logger.info(f"Media {media_id}: Found {len(media_comments)} comments")
                    
                except Exception as e:
                    logger.warning(f"Failed to get comments for media {media_id}: {e}")
                    continue
            
            logger.info(f"Total new Instagram comments found: {len(all_comments)}")
            return all_comments
            
        except Exception as e:
            logger.error(f"Failed to fetch Instagram media comments: {e}")
            return []


class OpenAIClient:
    """Handles OpenAI API interactions for classification"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def classify_comment(self, comment_text: str, business_context: str = "") -> Dict[str, Any]:
        """Classify a comment using OpenAI"""
        import requests
        
        try:
            prompt = self._build_classification_prompt(comment_text, business_context)
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an expert content moderator for social media comments."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            classification_text = result['choices'][0]['message']['content']
            
            return self._parse_classification(classification_text)
            
        except Exception as e:
            logger.error(f"Failed to classify comment: {e}")
            return self._default_classification()
    
    def _build_classification_prompt(self, comment_text: str, business_context: str) -> str:
        """Build the classification prompt"""
        return f"""
Analyze this social media comment and classify it according to the following criteria:

Comment: "{comment_text}"
Business Context: {business_context or "General business"}

Please provide a JSON response with these exact fields:
{{
    "sentiment": "positive|neutral|negative",
    "urgency": "low|medium|high",
    "intent": "question|complaint|compliment|spam|general",
    "toxicity_score": 0-10,
    "requires_response": true/false,
    "suggested_action": "reply|hide|escalate|ignore",
    "confidence": 0-100
}}

Consider:
- Positive sentiment: compliments, satisfaction, recommendations
- Negative sentiment: complaints, dissatisfaction, criticism
- High urgency: legal threats, severe complaints, viral negative content
- Medium urgency: legitimate complaints, specific issues
- Low urgency: general questions, positive feedback
- Toxicity score: 7+ should be hidden, 5-6 monitored, <5 normal
"""
    
    def _parse_classification(self, classification_text: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured data"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', classification_text, re.DOTALL)
            
            if json_match:
                classification = json.loads(json_match.group())
                
                # Validate and clean the classification
                return {
                    'sentiment': classification.get('sentiment', 'neutral'),
                    'urgency': classification.get('urgency', 'low'),
                    'intent': classification.get('intent', 'general'),
                    'toxicity_score': int(classification.get('toxicity_score', 0)),
                    'requires_response': bool(classification.get('requires_response', False)),
                    'suggested_action': classification.get('suggested_action', 'ignore'),
                    'confidence': int(classification.get('confidence', 50))
                }
            else:
                logger.warning("Could not parse JSON from OpenAI response")
                return self._default_classification()
                
        except Exception as e:
            logger.error(f"Failed to parse classification: {e}")
            return self._default_classification()
    
    def _default_classification(self) -> Dict[str, Any]:
        """Return default classification when parsing fails"""
        return {
            'sentiment': 'neutral',
            'urgency': 'low',
            'intent': 'general',
            'toxicity_score': 0,
            'requires_response': False,
            'suggested_action': 'ignore',
            'confidence': 0
        }


def lambda_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Standard Lambda response format"""
    return {
        'statusCode': status_code,
        'headers': headers or {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body)
    }


def validate_required_env_vars(required_vars: List[str]) -> bool:
    """Validate that required environment variables are set"""
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    return True