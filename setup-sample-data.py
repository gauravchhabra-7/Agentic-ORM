#!/usr/bin/env python3
"""
ORM Platform - Sample Data Setup Script
Creates sample client configurations and test data for MVP demonstration
"""

import boto3
import json
from datetime import datetime, timezone
import uuid

class SampleDataSetup:
    def __init__(self, region='ap-south-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Table names (should match Terraform output)
        self.comments_table_name = 'orm-platform-comments-dev'
        self.config_table_name = 'orm-platform-config-dev'
        self.audit_table_name = 'orm-platform-audit-dev'
    
    def setup_all(self):
        """Set up all sample data"""
        print("🚀 Setting up sample data for ORM Platform...")
        
        try:
            # 1. Create sample client configurations
            self.create_sample_configs()
            
            # 2. Create sample comments for testing
            self.create_sample_comments()
            
            # 3. Create sample audit logs
            self.create_sample_audit_logs()
            
            print("✅ Sample data setup completed successfully!")
            print("\n📋 What was created:")
            print("  • Test client configuration")
            print("  • Response templates")
            print("  • Classification rules")
            print("  • Sample comments for testing")
            print("  • Notification settings")
            
            print("\n🔧 Next steps:")
            print("  1. Update your Meta API keys in AWS Secrets Manager")
            print("  2. Test the ingestion Lambda function")
            print("  3. Monitor the dashboard API endpoints")
            
        except Exception as e:
            print(f"❌ Error setting up sample data: {e}")
            raise
    
    def create_sample_configs(self):
        """Create sample client configurations"""
        print("📝 Creating sample client configurations...")
        
        config_table = self.dynamodb.Table(self.config_table_name)
        
        # Sample client ID
        client_id = "demo_client_001"
        
        # 1. Meta API Configuration
        meta_api_config = {
            'client_id': client_id,
            'config_type': 'meta_api',
            'config': {
                'page_id': '560879270449410',  # User will need to update this
                'ad_account_id': 'your_ad_account_id',  # User will need to update this
                'instagram_account_id': '17841473299661248',  # User will need to update this
                'enabled': True,
                'last_sync': datetime.now(timezone.utc).isoformat()
            },
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 2. Response Templates Configuration
        response_templates_config = {
            'client_id': client_id,
            'config_type': 'response_templates',
            'config': {
                'templates': {
                    'question': "Hi {name}! Thanks for your question. We'll get back to you within 2 hours with a detailed answer. 😊",
                    'complaint': "Hi {name}, we're sorry to hear about your experience. We take all feedback seriously and will investigate this immediately. Please expect a response from our team within 1 hour.",
                    'compliment': "Thank you so much for the kind words, {name}! We're thrilled you had a great experience. 🎉",
                    'positive': "Thanks for the positive feedback, {name}! We really appreciate it! 😊",
                    'negative': "We're sorry to hear this, {name}. We'll look into this right away and make it right.",
                    'high': "Thank you for reaching out, {name}. This has been escalated to our priority team and you'll hear back within 30 minutes.",
                    'default': "Hi {name}! Thank you for your comment. We appreciate your feedback and will respond soon."
                },
                'signature': "Best regards,\nCustomer Success Team",
                'max_reply_length': 500,
                'use_emojis': True
            },
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 3. Classification Rules Configuration
        classification_rules_config = {
            'client_id': client_id,
            'config_type': 'classification_rules',
            'config': {
                'business_context': 'E-commerce business selling electronics and gadgets',
                'toxicity_threshold': 7,
                'auto_reply_enabled': True,
                'min_confidence_threshold': 70,
                'urgency_keywords': ['urgent', 'emergency', 'asap', 'immediately', 'broken', 'defective'],
                'positive_keywords': ['love', 'amazing', 'excellent', 'perfect', 'awesome', 'recommend'],
                'negative_keywords': ['hate', 'terrible', 'awful', 'worst', 'horrible', 'scam'],
                'intent_keywords': {
                    'question': ['how', 'what', 'when', 'where', 'why', '?'],
                    'complaint': ['problem', 'issue', 'broken', 'wrong', 'defective', 'disappointed'],
                    'shipping': ['delivery', 'shipping', 'tracking', 'arrived', 'delayed']
                },
                'business_hours': {
                    'timezone': 'Asia/Kolkata',
                    'hours': {
                        'monday': {'start': '9:00', 'end': '18:00'},
                        'tuesday': {'start': '9:00', 'end': '18:00'},
                        'wednesday': {'start': '9:00', 'end': '18:00'},
                        'thursday': {'start': '9:00', 'end': '18:00'},
                        'friday': {'start': '9:00', 'end': '18:00'},
                        'saturday': {'start': '10:00', 'end': '16:00'},
                        'sunday': {'start': '10:00', 'end': '16:00'}
                    }
                }
            },
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 4. Moderation Rules Configuration
        moderation_rules_config = {
            'client_id': client_id,
            'config_type': 'moderation_rules',
            'config': {
                'auto_hide_threshold': 8,
                'spam_confidence_threshold': 85,
                'repeat_offender_threshold': 3,
                'banned_keywords': ['spam', 'scam', 'fake', 'fraud'],
                'auto_hide_violations': ['toxicity', 'spam', 'harassment']
            },
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 5. Notifications Configuration
        notifications_config = {
            'client_id': client_id,
            'config_type': 'notifications',
            'config': {
                'slack_enabled': True,
                'email_enabled': False,  # Will enable once email is configured
                'sms_enabled': False,    # Will enable once SMS is configured
                'hide_notifications_enabled': True,
                'escalation_notifications_enabled': True,
                'daily_summary_enabled': True
            },
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Save all configurations
        configs = [
            meta_api_config,
            response_templates_config,
            classification_rules_config,
            moderation_rules_config,
            notifications_config
        ]
        
        for config in configs:
            config_table.put_item(Item=config)
            print(f"  ✅ Created {config['config_type']} configuration")
    
    def create_sample_comments(self):
        """Create sample comments for testing"""
        print("💬 Creating sample comments...")
        
        comments_table = self.dynamodb.Table(self.comments_table_name)
        
        sample_comments = [
            {
                'comment_id': f'test_comment_{uuid.uuid4().hex[:8]}',
                'client_id': 'demo_client_001',
                'platform': 'facebook',
                'post_id': 'sample_post_001',
                'text': 'Love this product! Amazing quality and fast shipping. Highly recommend!',
                'author_id': 'user_001',
                'author_name': 'John Smith',
                'created_time': '2024-05-31T10:30:00Z',
                'like_count': 5,
                'reply_count': 0,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'comment_id': f'test_comment_{uuid.uuid4().hex[:8]}',
                'client_id': 'demo_client_001',
                'platform': 'facebook',
                'post_id': 'sample_post_002',
                'text': 'Hi, I have a question about the return policy. How long do I have to return an item?',
                'author_id': 'user_002',
                'author_name': 'Sarah Johnson',
                'created_time': '2024-05-31T11:15:00Z',
                'like_count': 0,
                'reply_count': 0,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'comment_id': f'test_comment_{uuid.uuid4().hex[:8]}',
                'client_id': 'demo_client_001',
                'platform': 'instagram',
                'post_id': 'sample_post_003',
                'text': 'This is the worst product I have ever bought. Complete waste of money!',
                'author_id': 'user_003',
                'author_name': 'Mike Wilson',
                'created_time': '2024-05-31T12:00:00Z',
                'like_count': 0,
                'reply_count': 0,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'comment_id': f'test_comment_{uuid.uuid4().hex[:8]}',
                'client_id': 'demo_client_001',
                'platform': 'facebook_ads',
                'post_id': 'sample_ad_001',
                'text': 'Spam spam spam buy my product click here now!!!',
                'author_id': 'spammer_001',
                'author_name': 'Spam Bot',
                'created_time': '2024-05-31T13:30:00Z',
                'like_count': 0,
                'reply_count': 0,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'comment_id': f'test_comment_{uuid.uuid4().hex[:8]}',
                'client_id': 'demo_client_001',
                'platform': 'facebook',
                'post_id': 'sample_post_004',
                'text': 'When will my order ship? I ordered 3 days ago and still no tracking info.',
                'author_id': 'user_004',
                'author_name': 'Lisa Chen',
                'created_time': '2024-05-31T14:45:00Z',
                'like_count': 2,
                'reply_count': 0,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for comment in sample_comments:
            comments_table.put_item(Item=comment)
            print(f"  ✅ Created sample comment: {comment['text'][:50]}...")
    
    def create_sample_audit_logs(self):
        """Create sample audit logs"""
        print("📊 Creating sample audit logs...")
        
        audit_table = self.dynamodb.Table(self.audit_table_name)
        
        sample_logs = [
            {
                'log_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action_type': 'system_initialized',
                'details': {
                    'message': 'ORM Platform initialized with sample data',
                    'version': '1.0.0',
                    'client_id': 'demo_client_001'
                }
            },
            {
                'log_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action_type': 'configuration_created',
                'details': {
                    'config_type': 'response_templates',
                    'client_id': 'demo_client_001',
                    'templates_count': 7
                }
            }
        ]
        
        for log in sample_logs:
            audit_table.put_item(Item=log)
            print(f"  ✅ Created audit log: {log['action_type']}")
    
    def verify_setup(self):
        """Verify that the setup was successful"""
        print("\n🔍 Verifying setup...")
        
        try:
            # Check comments table
            comments_table = self.dynamodb.Table(self.comments_table_name)
            comments_response = comments_table.scan(Limit=1)
            comments_count = comments_response['Count']
            
            # Check config table
            config_table = self.dynamodb.Table(self.config_table_name)
            config_response = config_table.scan(Limit=1)
            config_count = config_response['Count']
            
            # Check audit table
            audit_table = self.dynamodb.Table(self.audit_table_name)
            audit_response = audit_table.scan(Limit=1)
            audit_count = audit_response['Count']
            
            print(f"  ✅ Comments table: {comments_count} records")
            print(f"  ✅ Config table: {config_count} records")
            print(f"  ✅ Audit table: {audit_count} records")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Verification failed: {e}")
            return False


def main():
    """Main function"""
    print("🎯 ORM Platform Sample Data Setup")
    print("This script creates sample configurations and test data for your MVP.\n")
    
    try:
        # Initialize setup
        setup = SampleDataSetup()
        
        # Run setup
        setup.setup_all()
        
        # Verify
        if setup.verify_setup():
            print("\n🎉 Sample data setup completed successfully!")
        else:
            print("\n⚠️  Setup completed but verification failed.")
        
        print("\n" + "="*50)
        print("IMPORTANT NEXT STEPS:")
        print("="*50)
        print("1. Update Meta API credentials in AWS Secrets Manager:")
        print("   aws secretsmanager update-secret --secret-id orm-platform-api-keys-dev \\")
        print("     --secret-string '{\"openai_api_key\":\"sk-...\",\"meta_access_token\":\"...\", ...}'")
        print("")
        print("2. Update the sample client configuration with your actual:")
        print("   • Facebook Page ID")
        print("   • Ad Account ID")
        print("   • Instagram Account ID")
        print("")
        print("3. Test the system by running the ingestion Lambda manually")
        print("")
        print("4. Check the dashboard API endpoints:")
        print("   • GET /health")
        print("   • GET /metrics")
        print("   • GET /comments")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()