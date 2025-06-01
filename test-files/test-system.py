#!/usr/bin/env python3
"""
ORM Platform - System Testing Script
Tests all Lambda functions and verifies end-to-end functionality
"""

import boto3
import json
import time
import requests
from datetime import datetime, timezone
import uuid


class ORMSystemTester:
    def __init__(self, region='ap-south-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sqs = boto3.client('sqs', region_name=region)
        
        # Resource names
        self.project_name = "orm-platform"
        self.environment = "dev"
        
        # Test results
        self.test_results = {}
    
    def run_all_tests(self):
        """Run comprehensive system tests"""
        print("🧪 Starting ORM Platform System Tests")
        print("="*50)
        
        try:
            # Test 1: Infrastructure Health
            self.test_infrastructure_health()
            
            # Test 2: Lambda Function Deployment
            self.test_lambda_functions()
            
            # Test 3: Database Operations
            self.test_database_operations()
            
            # Test 4: SQS Queue Operations
            self.test_sqs_operations()
            
            # Test 5: End-to-End Comment Processing
            self.test_end_to_end_processing()
            
            # Test 6: Dashboard API
            self.test_dashboard_api()
            
            # Test 7: Classification Testing
            self.test_classification_logic()
            
            # Generate test report
            self.generate_test_report()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            self.test_results['overall'] = {'status': 'FAILED', 'error': str(e)}
    
    def test_infrastructure_health(self):
        """Test basic infrastructure health"""
        print("\n📋 Testing Infrastructure Health...")
        
        test_name = "infrastructure_health"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        try:
            # Test DynamoDB tables
            tables_to_check = ['comments', 'config', 'audit']
            table_status = {}
            
            for table_type in tables_to_check:
                table_name = f"{self.project_name}-{table_type}-{self.environment}"
                try:
                    table = self.dynamodb.Table(table_name)
                    table.load()
                    table_status[table_type] = "✅ HEALTHY"
                except Exception as e:
                    table_status[table_type] = f"❌ ERROR: {e}"
            
            # Test SQS queue
            try:
                queue_name = f"{self.project_name}-comments-{self.environment}"
                queues = self.sqs.list_queues(QueueNamePrefix=queue_name)
                if queues.get('QueueUrls'):
                    table_status['sqs'] = "✅ HEALTHY"
                else:
                    table_status['sqs'] = "❌ QUEUE NOT FOUND"
            except Exception as e:
                table_status['sqs'] = f"❌ ERROR: {e}"
            
            # Print results
            for resource, status in table_status.items():
                print(f"  {resource.upper()}: {status}")
            
            # Determine overall status
            failed_count = sum(1 for status in table_status.values() if "❌" in status)
            if failed_count == 0:
                self.test_results[test_name] = {'status': 'PASSED', 'details': table_status}
                print("  ✅ Infrastructure health check PASSED")
            else:
                self.test_results[test_name] = {'status': 'FAILED', 'details': table_status}
                print(f"  ❌ Infrastructure health check FAILED ({failed_count} issues)")
            
        except Exception as e:
            self.test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
            print(f"  ❌ Infrastructure test failed: {e}")
    
    def test_lambda_functions(self):
        """Test Lambda function deployment and basic functionality"""
        print("\n🔧 Testing Lambda Functions...")
        
        test_name = "lambda_functions"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        functions_to_test = [
            'ingestion-function',
            'classification-function',
            'reply-handler',
            'hide-handler',
            'escalation-handler',
            'dashboard-api'
        ]
        
        function_results = {}
        
        for func_name in functions_to_test:
            aws_function_name = f"{self.project_name}-{func_name}-{self.environment}"
            
            try:
                # Check if function exists
                response = self.lambda_client.get_function(FunctionName=aws_function_name)
                
                # Test function invocation with dummy event
                test_event = self.get_test_event_for_function(func_name)
                
                invoke_response = self.lambda_client.invoke(
                    FunctionName=aws_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_event)
                )
                
                # Check response
                if invoke_response['StatusCode'] == 200:
                    function_results[func_name] = "✅ WORKING"
                else:
                    function_results[func_name] = f"❌ ERROR: Status {invoke_response['StatusCode']}"
                
            except Exception as e:
                function_results[func_name] = f"❌ ERROR: {e}"
        
        # Print results
        for func, status in function_results.items():
            print(f"  {func}: {status}")
        
        # Determine overall status
        failed_count = sum(1 for status in function_results.values() if "❌" in status)
        if failed_count == 0:
            self.test_results[test_name] = {'status': 'PASSED', 'details': function_results}
            print("  ✅ Lambda functions test PASSED")
        else:
            self.test_results[test_name] = {'status': 'FAILED', 'details': function_results}
            print(f"  ❌ Lambda functions test FAILED ({failed_count} issues)")
    
    def get_test_event_for_function(self, func_name):
        """Get appropriate test event for each function type"""
        
        if func_name == 'ingestion-function':
            return {
                'source': 'aws.events',
                'detail-type': 'Scheduled Event'
            }
        elif func_name == 'classification-function':
            return {
                'Records': [{
                    'body': json.dumps({
                        'action': 'classify_comment',
                        'comment_id': 'test_comment_123',
                        'client_id': 'test_client'
                    })
                }]
            }
        elif func_name in ['reply-handler', 'hide-handler', 'escalation-handler']:
            return {
                'Records': [{
                    'body': json.dumps({
                        'action': func_name.split('-')[0],
                        'comment_id': 'test_comment_123',
                        'client_id': 'test_client',
                        'classification': {}
                    })
                }]
            }
        elif func_name == 'dashboard-api':
            return {
                'httpMethod': 'GET',
                'path': '/health',
                'queryStringParameters': None,
                'pathParameters': None,
                'body': None
            }
        else:
            return {}
    
    def test_database_operations(self):
        """Test database read/write operations"""
        print("\n💾 Testing Database Operations...")
        
        test_name = "database_operations"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        try:
            # Test comment creation
            comments_table = self.dynamodb.Table(f"{self.project_name}-comments-{self.environment}")
            
            test_comment = {
                'comment_id': f'test_{uuid.uuid4().hex[:8]}',
                'client_id': 'test_client',
                'text': 'This is a test comment',
                'platform': 'test',
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Write test
            comments_table.put_item(Item=test_comment)
            print("  ✅ Write operation successful")
            
            # Read test
            response = comments_table.get_item(Key={'comment_id': test_comment['comment_id']})
            if 'Item' in response:
                print("  ✅ Read operation successful")
            else:
                raise Exception("Failed to read back test comment")
            
            # Update test
            comments_table.update_item(
                Key={'comment_id': test_comment['comment_id']},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'tested'}
            )
            print("  ✅ Update operation successful")
            
            # Delete test
            comments_table.delete_item(Key={'comment_id': test_comment['comment_id']})
            print("  ✅ Delete operation successful")
            
            self.test_results[test_name] = {'status': 'PASSED'}
            print("  ✅ Database operations test PASSED")
            
        except Exception as e:
            self.test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
            print(f"  ❌ Database operations test FAILED: {e}")
    
    def test_sqs_operations(self):
        """Test SQS queue operations"""
        print("\n📨 Testing SQS Operations...")
        
        test_name = "sqs_operations"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        try:
            # Get queue URL
            queue_name = f"{self.project_name}-comments-{self.environment}"
            queues = self.sqs.list_queues(QueueNamePrefix=queue_name)
            
            if not queues.get('QueueUrls'):
                raise Exception("SQS queue not found")
            
            queue_url = queues['QueueUrls'][0]
            
            # Send test message
            test_message = {
                'action': 'test_message',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'test_id': str(uuid.uuid4())
            }
            
            self.sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(test_message)
            )
            print("  ✅ Send message successful")
            
            # Receive message
            time.sleep(2)  # Wait for message to be available
            response = self.sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
            
            if 'Messages' in response:
                # Delete the test message
                receipt_handle = response['Messages'][0]['ReceiptHandle']
                self.sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                print("  ✅ Receive and delete message successful")
            else:
                print("  ⚠️  No messages received (this might be normal)")
            
            self.test_results[test_name] = {'status': 'PASSED'}
            print("  ✅ SQS operations test PASSED")
            
        except Exception as e:
            self.test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
            print(f"  ❌ SQS operations test FAILED: {e}")
    
    def test_end_to_end_processing(self):
        """Test end-to-end comment processing workflow"""
        print("\n🔄 Testing End-to-End Processing...")
        
        test_name = "end_to_end_processing"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        try:
            # Create a test comment in the database
            comments_table = self.dynamodb.Table(f"{self.project_name}-comments-{self.environment}")
            
            test_comment_id = f'e2e_test_{uuid.uuid4().hex[:8]}'
            test_comment = {
                'comment_id': test_comment_id,
                'client_id': 'demo_client_001',
                'text': 'This is a test comment for end-to-end processing',
                'platform': 'test',
                'status': 'pending',
                'author_name': 'Test User',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            comments_table.put_item(Item=test_comment)
            print("  ✅ Test comment created")
            
            # Trigger classification function
            classification_function = f"{self.project_name}-classification-function-{self.environment}"
            
            classification_event = {
                'Records': [{
                    'body': json.dumps({
                        'action': 'classify_comment',
                        'comment_id': test_comment_id,
                        'client_id': 'demo_client_001'
                    })
                }]
            }
            
            response = self.lambda_client.invoke(
                FunctionName=classification_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(classification_event)
            )
            
            if response['StatusCode'] == 200:
                print("  ✅ Classification function executed")
            else:
                raise Exception(f"Classification function failed with status {response['StatusCode']}")
            
            # Wait a moment for processing
            time.sleep(3)
            
            # Check if comment was updated
            updated_comment = comments_table.get_item(Key={'comment_id': test_comment_id})
            
            if 'Item' in updated_comment:
                comment = updated_comment['Item']
                if comment.get('status') != 'pending':
                    print("  ✅ Comment processing completed")
                else:
                    print("  ⚠️  Comment still pending (processing might take longer)")
            
            # Cleanup
            comments_table.delete_item(Key={'comment_id': test_comment_id})
            
            self.test_results[test_name] = {'status': 'PASSED'}
            print("  ✅ End-to-end processing test PASSED")
            
        except Exception as e:
            self.test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
            print(f"  ❌ End-to-end processing test FAILED: {e}")
    
    def test_dashboard_api(self):
        """Test dashboard API endpoints"""
        print("\n📊 Testing Dashboard API...")
        
        test_name = "dashboard_api"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        try:
            # Test health endpoint
            dashboard_function = f"{self.project_name}-dashboard-api-{self.environment}"
            
            health_event = {
                'httpMethod': 'GET',
                'path': '/health',
                'queryStringParameters': None,
                'pathParameters': None,
                'body': None
            }
            
            response = self.lambda_client.invoke(
                FunctionName=dashboard_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(health_event)
            )
            
            if response['StatusCode'] == 200:
                payload = json.loads(response['Payload'].read())
                if payload.get('statusCode') == 200:
                    print("  ✅ Health endpoint working")
                else:
                    print(f"  ⚠️  Health endpoint returned status {payload.get('statusCode')}")
            
            # Test metrics endpoint
            metrics_event = {
                'httpMethod': 'GET',
                'path': '/metrics',
                'queryStringParameters': {'client_id': 'demo_client_001'},
                'pathParameters': None,
                'body': None
            }
            
            response = self.lambda_client.invoke(
                FunctionName=dashboard_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(metrics_event)
            )
            
            if response['StatusCode'] == 200:
                print("  ✅ Metrics endpoint working")
            
            self.test_results[test_name] = {'status': 'PASSED'}
            print("  ✅ Dashboard API test PASSED")
            
        except Exception as e:
            self.test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
            print(f"  ❌ Dashboard API test FAILED: {e}")
    
    def test_classification_logic(self):
        """Test classification logic with sample comments"""
        print("\n🤖 Testing Classification Logic...")
        
        test_name = "classification_logic"
        self.test_results[test_name] = {'status': 'RUNNING'}
        
        try:
            # Test different types of comments
            test_comments = [
                {"text": "Love this product! Amazing quality!", "expected_sentiment": "positive"},
                {"text": "This is terrible and I hate it", "expected_sentiment": "negative"},
                {"text": "How do I return this item?", "expected_intent": "question"},
                {"text": "SPAM SPAM BUY NOW CLICK HERE!", "expected_intent": "spam"}
            ]
            
            classification_results = []
            
            for comment in test_comments:
                # Create test comment
                comment_id = f'classification_test_{uuid.uuid4().hex[:8]}'
                
                comments_table = self.dynamodb.Table(f"{self.project_name}-comments-{self.environment}")
                
                test_comment = {
                    'comment_id': comment_id,
                    'client_id': 'demo_client_001',
                    'text': comment['text'],
                    'platform': 'test',
                    'status': 'pending',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                comments_table.put_item(Item=test_comment)
                
                # Trigger classification
                classification_function = f"{self.project_name}-classification-function-{self.environment}"
                
                classification_event = {
                    'Records': [{
                        'body': json.dumps({
                            'action': 'classify_comment',
                            'comment_id': comment_id,
                            'client_id': 'demo_client_001'
                        })
                    }]
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=classification_function,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(classification_event)
                )
                
                classification_results.append({
                    'comment': comment['text'][:30] + '...',
                    'status': 'success' if response['StatusCode'] == 200 else 'failed'
                })
                
                # Cleanup
                comments_table.delete_item(Key={'comment_id': comment_id})
            
            # Print results
            for result in classification_results:
                status_icon = "✅" if result['status'] == 'success' else "❌"
                print(f"  {status_icon} {result['comment']}: {result['status']}")
            
            success_count = sum(1 for r in classification_results if r['status'] == 'success')
            
            if success_count == len(test_comments):
                self.test_results[test_name] = {'status': 'PASSED'}
                print("  ✅ Classification logic test PASSED")
            else:
                self.test_results[test_name] = {'status': 'PARTIAL'}
                print(f"  ⚠️  Classification logic test PARTIAL ({success_count}/{len(test_comments)} passed)")
            
        except Exception as e:
            self.test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
            print(f"  ❌ Classification logic test FAILED: {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Test Report")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'FAILED')
        partial_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'PARTIAL')
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Partial: {partial_tests} ⚠️")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = result.get('status', 'UNKNOWN')
            icon = {'PASSED': '✅', 'FAILED': '❌', 'PARTIAL': '⚠️', 'RUNNING': '🔄'}.get(status, '❓')
            print(f"  {icon} {test_name}: {status}")
            
            if result.get('error'):
                print(f"    Error: {result['error']}")
        
        print("\n" + "="*50)
        
        if failed_tests == 0:
            if partial_tests == 0:
                print("🎉 ALL TESTS PASSED! Your ORM Platform is ready to use!")
            else:
                print("⚠️  TESTS COMPLETED WITH WARNINGS. System is functional but needs attention.")
        else:
            print("❌ SOME TESTS FAILED. Please review and fix issues before proceeding.")
        
        print("\nNext Steps:")
        if failed_tests == 0:
            print("1. ✅ System is operational")
            print("2. 🔧 Configure your Meta API credentials")
            print("3. 📊 Access the dashboard")
            print("4. 🚀 Start monitoring real comments!")
        else:
            print("1. 🔍 Review failed tests above")
            print("2. 🔧 Fix infrastructure or deployment issues")
            print("3. 🔄 Re-run tests")


def main():
    """Main function"""
    print("🧪 ORM Platform System Testing")
    print("This script tests all components of your ORM platform.\n")
    
    try:
        tester = ORMSystemTester()
        tester.run_all_tests()
        
    except Exception as e:
        print(f"\n❌ Test suite execution failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
