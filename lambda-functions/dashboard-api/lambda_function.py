"""
ORM Platform - Dashboard API Lambda
Provides REST API endpoints for the dashboard interface
Triggered by API Gateway requests
"""

import json
import sys
import os

# Add shared utilities to path
#sys.path.append('/opt/python')
#sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.utils import AWSService, lambda_response, validate_required_env_vars, logger
from datetime import datetime, timezone, timedelta
import boto3
from decimal import Decimal


def lambda_handler(event, context):
    """
    Main Lambda handler for dashboard API requests
    """
    
    logger.info(f"Dashboard API request: {event.get('httpMethod')} {event.get('path')}")
    
    # Validate environment variables
    required_vars = ['COMMENTS_TABLE', 'CONFIG_TABLE', 'AUDIT_TABLE']
    if not validate_required_env_vars(required_vars):
        return lambda_response(500, {'error': 'Missing required environment variables'})
    
    try:
        # Initialize services
        aws_service = AWSService()
        
        # Route requests
        method = event.get('httpMethod')
        path = event.get('path', '')
        
        # Extract client_id from path or query parameters
        client_id = extract_client_id(event)
        
        if method == 'GET':
            return handle_get_request(aws_service, path, client_id, event)
        elif method == 'POST':
            return handle_post_request(aws_service, path, client_id, event)
        elif method == 'PUT':
            return handle_put_request(aws_service, path, client_id, event)
        elif method == 'DELETE':
            return handle_delete_request(aws_service, path, client_id, event)
        elif method == 'OPTIONS':
            return lambda_response(200, {'message': 'CORS preflight'})
        else:
            return lambda_response(405, {'error': 'Method not allowed'})
        
    except Exception as e:
        logger.error(f"Dashboard API error: {str(e)}")
        return lambda_response(500, {'error': 'Internal server error', 'details': str(e)})


def extract_client_id(event):
    """Extract client_id from request"""
    # Try path parameters first
    path_params = event.get('pathParameters') or {}
    if 'client_id' in path_params:
        return path_params['client_id']
    
    # Try query parameters
    query_params = event.get('queryStringParameters') or {}
    if 'client_id' in query_params:
        return query_params['client_id']
    
    # Try request body
    try:
        body = json.loads(event.get('body', '{}'))
        if 'client_id' in body:
            return body['client_id']
    except:
        pass
    
    return None


def handle_get_request(aws_service: AWSService, path: str, client_id: str, event: dict):
    """Handle GET requests"""
    
    if path == '/health':
        return get_health_status(aws_service)
    elif path == '/metrics' or path.startswith('/metrics/'):
        return get_metrics(aws_service, client_id, event)
    elif path == '/comments' or path.startswith('/comments/'):
        return get_comments(aws_service, client_id, event)
    elif path == '/config' or path.startswith('/config/'):
        return get_config(aws_service, client_id, event)
    elif path == '/audit' or path.startswith('/audit/'):
        return get_audit_logs(aws_service, client_id, event)
    elif path == '/dashboard' or path.startswith('/dashboard/'):
        return get_dashboard_data(aws_service, client_id, event)
    else:
        return lambda_response(404, {'error': 'Endpoint not found'})


def handle_post_request(aws_service: AWSService, path: str, client_id: str, event: dict):
    """Handle POST requests"""
    
    if path == '/config':
        return create_config(aws_service, event)
    elif path == '/test-classification':
        return test_classification(aws_service, event)
    else:
        return lambda_response(404, {'error': 'Endpoint not found'})


def handle_put_request(aws_service: AWSService, path: str, client_id: str, event: dict):
    """Handle PUT requests"""
    
    if path.startswith('/config/'):
        return update_config(aws_service, event)
    elif path.startswith('/comments/'):
        return update_comment(aws_service, event)
    else:
        return lambda_response(404, {'error': 'Endpoint not found'})


def handle_delete_request(aws_service: AWSService, path: str, client_id: str, event: dict):
    """Handle DELETE requests"""
    
    if path.startswith('/config/'):
        return delete_config(aws_service, event)
    else:
        return lambda_response(404, {'error': 'Endpoint not found'})


def get_health_status(aws_service: AWSService):
    """Get system health status"""
    
    try:
        # Check DynamoDB tables
        tables_healthy = check_dynamodb_health(aws_service)
        
        # Check recent activity
        recent_activity = get_recent_activity_count(aws_service)
        
        health_status = {
            'status': 'healthy' if tables_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'services': {
                'dynamodb': 'healthy' if tables_healthy else 'error',
                'lambda': 'healthy'
            },
            'recent_activity': recent_activity
        }
        
        return lambda_response(200, health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return lambda_response(500, {'status': 'error', 'error': str(e)})


def get_metrics(aws_service: AWSService, client_id: str, event: dict):
    """Get platform metrics"""
    
    try:
        query_params = event.get('queryStringParameters') or {}
        time_range = query_params.get('range', '24h')
        
        # Calculate time window
        end_time = datetime.now(timezone.utc)
        if time_range == '1h':
            start_time = end_time - timedelta(hours=1)
        elif time_range == '24h':
            start_time = end_time - timedelta(hours=24)
        elif time_range == '7d':
            start_time = end_time - timedelta(days=7)
        elif time_range == '30d':
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(hours=24)
        
        metrics = {
            'time_range': time_range,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_comments': get_comment_count(aws_service, client_id, start_time, end_time),
            'sentiment_breakdown': get_sentiment_breakdown(aws_service, client_id, start_time, end_time),
            'action_breakdown': get_action_breakdown(aws_service, client_id, start_time, end_time),
            'response_times': get_response_times(aws_service, client_id, start_time, end_time),
            'platform_breakdown': get_platform_breakdown(aws_service, client_id, start_time, end_time)
        }
        
        return lambda_response(200, metrics)
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return lambda_response(500, {'error': str(e)})


def get_comments(aws_service: AWSService, client_id: str, event: dict):
    """Get comments with filtering and pagination"""
    
    try:
        query_params = event.get('queryStringParameters') or {}
        
        # Pagination parameters
        limit = int(query_params.get('limit', 50))
        offset = int(query_params.get('offset', 0))
        
        # Filter parameters
        status = query_params.get('status')
        sentiment = query_params.get('sentiment')
        platform = query_params.get('platform')
        
        # Get comments
        comments = query_comments(aws_service, client_id, limit, offset, {
            'status': status,
            'sentiment': sentiment,
            'platform': platform
        })
        
        # Get total count for pagination
        total_count = get_total_comment_count(aws_service, client_id)
        
        response_data = {
            'comments': comments,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total_count,
                'has_more': offset + limit < total_count
            },
            'filters': {
                'status': status,
                'sentiment': sentiment,
                'platform': platform
            }
        }
        
        return lambda_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Failed to get comments: {e}")
        return lambda_response(500, {'error': str(e)})


def get_config(aws_service: AWSService, client_id: str, event: dict):
    """Get client configuration"""
    
    try:
        path_params = event.get('pathParameters') or {}
        config_type = path_params.get('config_type')
        
        if config_type:
            # Get specific config type
            config = aws_service.get_client_config(client_id, config_type)
            return lambda_response(200, {'config_type': config_type, 'config': config})
        else:
            # Get all config types for client
            all_configs = get_all_client_configs(aws_service, client_id)
            return lambda_response(200, {'client_id': client_id, 'configs': all_configs})
        
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return lambda_response(500, {'error': str(e)})


def get_audit_logs(aws_service: AWSService, client_id: str, event: dict):
    """Get audit logs"""
    
    try:
        query_params = event.get('queryStringParameters') or {}
        
        limit = int(query_params.get('limit', 100))
        action_type = query_params.get('action_type')
        
        # Query audit logs
        logs = query_audit_logs(aws_service, action_type, limit)
        
        # Filter by client if specified
        if client_id:
            logs = [log for log in logs if log.get('details', {}).get('client_id') == client_id]
        
        return lambda_response(200, {'logs': logs})
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return lambda_response(500, {'error': str(e)})


def get_dashboard_data(aws_service: AWSService, client_id: str, event: dict):
    """Get comprehensive dashboard data"""
    
    try:
        # Get current time
        now = datetime.now(timezone.utc)
        
        # Recent activity (last 24 hours)
        yesterday = now - timedelta(hours=24)
        
        dashboard_data = {
            'timestamp': now.isoformat(),
            'client_id': client_id,
            'summary': {
                'total_comments_today': get_comment_count(aws_service, client_id, yesterday, now),
                'pending_comments': get_pending_comment_count(aws_service, client_id),
                'escalated_comments': get_escalated_comment_count(aws_service, client_id),
                'auto_replies_sent': get_auto_reply_count(aws_service, client_id, yesterday, now)
            },
            'recent_comments': get_recent_comments(aws_service, client_id, 10),
            'sentiment_trends': get_sentiment_trends(aws_service, client_id),
            'platform_stats': get_platform_breakdown(aws_service, client_id, yesterday, now),
            'action_stats': get_action_breakdown(aws_service, client_id, yesterday, now),
            'alerts': get_active_alerts(aws_service, client_id)
        }
        
        return lambda_response(200, dashboard_data)
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        return lambda_response(500, {'error': str(e)})


# Helper functions for data retrieval

def check_dynamodb_health(aws_service: AWSService) -> bool:
    """Check if DynamoDB tables are accessible"""
    try:
        # Simple query to check table access
        aws_service.dynamodb.Table(aws_service.comments_table).scan(Limit=1)
        return True
    except Exception:
        return False


def get_recent_activity_count(aws_service: AWSService) -> dict:
    """Get count of recent activity"""
    try:
        # This is a simplified version - in production you'd have more sophisticated metrics
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        
        return {
            'comments_24h': 0,  # Would implement actual counting
            'actions_24h': 0,
            'escalations_24h': 0
        }
    except Exception:
        return {'comments_24h': 0, 'actions_24h': 0, 'escalations_24h': 0}


def get_comment_count(aws_service: AWSService, client_id: str, start_time: datetime, end_time: datetime) -> int:
    """Get comment count for time range"""
    try:
        table = aws_service.dynamodb.Table(aws_service.comments_table)
        
        # This is a simplified implementation
        # In production, you'd use GSI with timestamp for efficient querying
        response = table.scan(
            FilterExpression='client_id = :client_id AND created_at BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':client_id': client_id,
                ':start': start_time.isoformat(),
                ':end': end_time.isoformat()
            },
            Select='COUNT'
        )
        
        return response['Count']
    except Exception as e:
        logger.error(f"Failed to get comment count: {e}")
        return 0


def get_sentiment_breakdown(aws_service: AWSService, client_id: str, start_time: datetime, end_time: datetime) -> dict:
    """Get sentiment breakdown"""
    try:
        # This would be implemented with proper aggregation
        # For MVP, return sample data
        return {
            'positive': 45,
            'neutral': 30,
            'negative': 25
        }
    except Exception:
        return {'positive': 0, 'neutral': 0, 'negative': 0}


def get_action_breakdown(aws_service: AWSService, client_id: str, start_time: datetime, end_time: datetime) -> dict:
    """Get action breakdown"""
    try:
        return {
            'auto_replied': 15,
            'hidden': 5,
            'escalated': 10,
            'ignored': 70
        }
    except Exception:
        return {'auto_replied': 0, 'hidden': 0, 'escalated': 0, 'ignored': 0}


def get_response_times(aws_service: AWSService, client_id: str, start_time: datetime, end_time: datetime) -> dict:
    """Get response time metrics"""
    try:
        return {
            'avg_classification_time': 2.3,
            'avg_response_time': 45.6,
            'p95_response_time': 120.0
        }
    except Exception:
        return {'avg_classification_time': 0, 'avg_response_time': 0, 'p95_response_time': 0}


def get_platform_breakdown(aws_service: AWSService, client_id: str, start_time: datetime, end_time: datetime) -> dict:
    """Get platform breakdown"""
    try:
        return {
            'facebook': 60,
            'instagram': 35,
            'facebook_ads': 5
        }
    except Exception:
        return {'facebook': 0, 'instagram': 0, 'facebook_ads': 0}


# Additional helper functions would be implemented here...

def create_config(aws_service: AWSService, event: dict):
    """Create new client configuration"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        client_id = body.get('client_id')
        config_type = body.get('config_type')
        config_data = body.get('config', {})
        
        if not all([client_id, config_type]):
            return lambda_response(400, {'error': 'Missing required fields'})
        
        # Save configuration
        table = aws_service.dynamodb.Table(aws_service.config_table)
        table.put_item(Item={
            'client_id': client_id,
            'config_type': config_type,
            'config': config_data,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        })
        
        return lambda_response(201, {'message': 'Configuration created successfully'})
        
    except Exception as e:
        logger.error(f"Failed to create config: {e}")
        return lambda_response(500, {'error': str(e)})


# Placeholder implementations for other functions
def query_comments(aws_service, client_id, limit, offset, filters):
    """Query comments with filters - placeholder implementation"""
    return []

def get_total_comment_count(aws_service, client_id):
    """Get total comment count - placeholder implementation"""
    return 0

def get_all_client_configs(aws_service, client_id):
    """Get all configs for client - placeholder implementation"""
    return {}

def query_audit_logs(aws_service, action_type, limit):
    """Query audit logs - placeholder implementation"""
    return []

def get_pending_comment_count(aws_service, client_id):
    """Get pending comment count - placeholder implementation"""
    return 0

def get_escalated_comment_count(aws_service, client_id):
    """Get escalated comment count - placeholder implementation"""
    return 0

def get_auto_reply_count(aws_service, client_id, start_time, end_time):
    """Get auto reply count - placeholder implementation"""
    return 0

def get_recent_comments(aws_service, client_id, limit):
    """Get recent comments - placeholder implementation"""
    return []

def get_sentiment_trends(aws_service, client_id):
    """Get sentiment trends - placeholder implementation"""
    return []

def get_active_alerts(aws_service, client_id):
    """Get active alerts - placeholder implementation"""
    return []

def update_config(aws_service, event):
    """Update configuration - placeholder implementation"""
    return lambda_response(200, {'message': 'Config updated'})

def update_comment(aws_service, event):
    """Update comment - placeholder implementation"""
    return lambda_response(200, {'message': 'Comment updated'})

def delete_config(aws_service, event):
    """Delete configuration - placeholder implementation"""
    return lambda_response(200, {'message': 'Config deleted'})

def test_classification(aws_service, event):
    """Test comment classification - placeholder implementation"""
    return lambda_response(200, {'message': 'Classification test completed'})


# For local testing
if __name__ == "__main__":
    # Mock API Gateway event for local testing
    test_event = {
        'httpMethod': 'GET',
        'path': '/health',
        'queryStringParameters': None,
        'pathParameters': None,
        'body': None
    }
    
    class MockContext:
        def get_remaining_time_in_millis(self):
            return 30000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))