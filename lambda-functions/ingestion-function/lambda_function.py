"""
ORM Platform - Comment Ingestion Lambda
Fetches new comments from Meta ads every 5 minutes
Triggered by EventBridge schedule
"""

import json
import sys
import os

# Add shared utilities to path
#sys.path.append('/opt/python')
#sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.utils import AWSService, MetaAPIClient, lambda_response, validate_required_env_vars, logger
from datetime import datetime, timezone, timedelta
import uuid


def lambda_handler(event, context):
    """
    Main Lambda handler for comment ingestion
    Triggered by EventBridge every 5 minutes
    """
    
    logger.info("Starting comment ingestion process")
    
    # Validate environment variables
    required_vars = ['COMMENTS_TABLE', 'CONFIG_TABLE', 'QUEUE_URL', 'SECRET_NAME']
    if not validate_required_env_vars(required_vars):
        return lambda_response(500, {'error': 'Missing required environment variables'})
    
    try:
        # Initialize services
        aws_service = AWSService()
        secrets = aws_service.get_secrets()
        
        # Initialize Meta API client
        meta_client = MetaAPIClient(secrets['meta_access_token'])
        
        # Get active clients from config
        active_clients = get_active_clients(aws_service)
        
        total_processed = 0
        total_new_comments = 0
        
        # Process each client
        for client in active_clients:
            client_id = client['client_id']
            client_config = client['config']
            
            logger.info(f"Processing client: {client_id}")
            
            # Fetch comments for this client
            new_comments = fetch_client_comments(
                meta_client, 
                aws_service, 
                client_id, 
                client_config
            )
            
            total_new_comments += len(new_comments)
            
            # Send new comments to processing queue
            for comment in new_comments:
                success = aws_service.send_to_queue({
                    'action': 'classify_comment',
                    'comment_id': comment['comment_id'],
                    'client_id': client_id
                })
                
                if success:
                    total_processed += 1
        
        # Log audit information
        aws_service.save_audit_log('ingestion_completed', {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'clients_processed': len(active_clients),
            'new_comments_found': total_new_comments,
            'comments_queued': total_processed,
            'execution_duration_ms': context.get_remaining_time_in_millis()
        })
        
        logger.info(f"Ingestion completed: {total_new_comments} new comments, {total_processed} queued")
        
        return lambda_response(200, {
            'status': 'success',
            'clients_processed': len(active_clients),
            'new_comments': total_new_comments,
            'queued_for_processing': total_processed
        })
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        
        # Log error for monitoring
        aws_service.save_audit_log('ingestion_error', {
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return lambda_response(500, {
            'status': 'error',
            'message': str(e)
        })


def get_active_clients(aws_service: AWSService) -> list:
    """
    Get list of active clients from config table
    Returns clients with Meta API configurations
    """
    try:
        table = aws_service.dynamodb.Table(aws_service.config_table)
        
        # Scan for all client configurations of type 'meta_api'
        response = table.scan(
            FilterExpression='config_type = :config_type',
            ExpressionAttributeValues={':config_type': 'meta_api'}
        )
        
        active_clients = []
        
        for item in response.get('Items', []):
            config = item.get('config', {})
            
            # Check if client has required Meta API configuration
            if (config.get('page_id') or config.get('ad_account_id')) and config.get('enabled', True):
                active_clients.append({
                    'client_id': item['client_id'],
                    'config': config
                })
        
        logger.info(f"Found {len(active_clients)} active clients")
        return active_clients
        
    except Exception as e:
        logger.error(f"Failed to get active clients: {e}")
        return []


def fetch_client_comments(meta_client: MetaAPIClient, aws_service: AWSService, 
                         client_id: str, client_config: dict) -> list:
    """
    Fetch new comments for a specific client
    Returns list of new comments that weren't processed before
    """
    
    new_comments = []
    
    try:
        # Determine the last ingestion time (default to 1 hour ago)
        last_ingestion = get_last_ingestion_time(aws_service, client_id)
        
        # Fetch comments from different sources
        all_comments = []
        
        # 1. Facebook Page comments (if configured)
        if client_config.get('page_id'):
            page_comments = fetch_page_comments(
                meta_client, 
                client_config['page_id'], 
                last_ingestion
            )
            all_comments.extend(page_comments)
        
        # 2. Ad comments (if configured)
        if client_config.get('ad_account_id'):
            ad_comments = fetch_ad_comments(
                meta_client, 
                client_config['ad_account_id'], 
                last_ingestion
            )
            all_comments.extend(ad_comments)
        
        # 3. Instagram comments (if configured)
        if client_config.get('instagram_account_id'):
            instagram_comments = fetch_instagram_comments(
                meta_client, 
                client_config['instagram_account_id'], 
                last_ingestion
            )
            all_comments.extend(instagram_comments)
        
        # Process and deduplicate comments
        for comment in all_comments:
            if is_new_comment(aws_service, comment['id']):
                
                # Standardize comment format
                standardized_comment = {
                    'comment_id': comment['id'],
                    'client_id': client_id,
                    'platform': comment.get('platform', 'facebook'),
                    'post_id': comment.get('post_id', ''),
                    'text': comment.get('message', ''),
                    'author_id': comment.get('from', {}).get('id', ''),
                    'author_name': comment.get('from', {}).get('name', ''),
                    'created_time': comment.get('created_time', ''),
                    'like_count': comment.get('like_count', 0),
                    'reply_count': comment.get('comment_count', 0),
                    'raw_data': comment  # Store original data for reference
                }
                
                # Save to database
                if aws_service.save_comment(standardized_comment):
                    new_comments.append(standardized_comment)
                    logger.info(f"Saved new comment: {comment['id']}")
        
        # Update last ingestion time
        update_last_ingestion_time(aws_service, client_id)
        
        return new_comments
        
    except Exception as e:
        logger.error(f"Failed to fetch comments for client {client_id}: {e}")
        return []


def fetch_page_comments(meta_client: MetaAPIClient, page_id: str, since_time: datetime) -> list:
    """Fetch comments from Facebook page posts"""
    try:
        posts = meta_client.get_page_posts(page_id, limit=10)
        comments = []
        
        for post in posts:
            post_comments = post.get('comments', {}).get('data', [])
            
            for comment in post_comments:
                # Add platform and post context
                comment['platform'] = 'facebook'
                comment['post_id'] = post['id']
                
                # Filter by time if specified
                comment_time = datetime.fromisoformat(comment['created_time'].replace('Z', '+00:00'))
                if comment_time > since_time:
                    comments.append(comment)
        
        logger.info(f"Fetched {len(comments)} page comments")
        return comments
        
    except Exception as e:
        logger.error(f"Failed to fetch page comments: {e}")
        return []


def fetch_ad_comments(meta_client: MetaAPIClient, ad_account_id: str, since_time: datetime) -> list:
    """Fetch comments from ad campaigns"""
    try:
        # This is a simplified implementation for MVP
        # In production, you'd get specific ad IDs and their comments
        ad_comments = meta_client.get_ad_comments(ad_account_id)
        
        filtered_comments = []
        for comment in ad_comments:
            comment['platform'] = 'facebook_ads'
            
            # Filter by time if comment has timestamp
            if comment.get('created_time'):
                comment_time = datetime.fromisoformat(comment['created_time'].replace('Z', '+00:00'))
                if comment_time > since_time:
                    filtered_comments.append(comment)
            else:
                # Include comments without timestamp for now
                filtered_comments.append(comment)
        
        logger.info(f"Fetched {len(filtered_comments)} ad comments")
        return filtered_comments
        
    except Exception as e:
        logger.error(f"Failed to fetch ad comments: {e}")
        return []


def fetch_instagram_comments(meta_client: MetaAPIClient, instagram_account_id: str, since_time: datetime) -> list:
    """Fetch comments from Instagram posts"""
    try:
        # For MVP, return empty list
        # In production, implement Instagram Graph API calls
        logger.info("Instagram comment fetching - placeholder for MVP")
        return []
        
    except Exception as e:
        logger.error(f"Failed to fetch Instagram comments: {e}")
        return []


def is_new_comment(aws_service: AWSService, comment_id: str) -> bool:
    """Check if comment already exists in database"""
    try:
        existing_comment = aws_service.get_comment(comment_id)
        return existing_comment is None
    except Exception as e:
        logger.error(f"Failed to check comment existence: {e}")
        return True  # Assume new to avoid missing comments


def get_last_ingestion_time(aws_service: AWSService, client_id: str) -> datetime:
    """Get the last successful ingestion time for a client"""
    try:
        config = aws_service.get_client_config(client_id, 'ingestion_state')
        
        if config and config.get('last_ingestion_time'):
            return datetime.fromisoformat(config['last_ingestion_time'])
        else:
            # Default to 1 hour ago for first run
            return datetime.now(timezone.utc) - timedelta(hours=1)
            
    except Exception as e:
        logger.error(f"Failed to get last ingestion time: {e}")
        return datetime.now(timezone.utc) - timedelta(hours=1)


def update_last_ingestion_time(aws_service: AWSService, client_id: str):
    """Update the last successful ingestion time"""
    try:
        table = aws_service.dynamodb.Table(aws_service.config_table)
        
        table.put_item(Item={
            'client_id': client_id,
            'config_type': 'ingestion_state',
            'config': {
                'last_ingestion_time': datetime.now(timezone.utc).isoformat(),
                'last_update': datetime.now(timezone.utc).isoformat()
            }
        })
        
        logger.info(f"Updated last ingestion time for client {client_id}")
        
    except Exception as e:
        logger.error(f"Failed to update last ingestion time: {e}")


# For local testing
if __name__ == "__main__":
    # Mock event and context for local testing
    test_event = {
        'source': 'aws.events',
        'detail-type': 'Scheduled Event'
    }
    
    class MockContext:
        def get_remaining_time_in_millis(self):
            return 30000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))