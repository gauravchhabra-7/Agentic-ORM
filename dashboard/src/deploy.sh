#!/bin/bash

# ORM-MVP Dashboard Deployment Script
# Deploys React dashboard to S3 + CloudFront

set -e

# Configuration
PROJECT_NAME="orm-mvp-dashboard"
REGION="ap-south-1"
BUCKET_NAME="${PROJECT_NAME}-$(date +%s)"  # Unique bucket name
DISTRIBUTION_COMMENT="ORM-MVP Dashboard Distribution"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting ORM-MVP Dashboard Deployment${NC}"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found. Please install Node.js and npm first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Build the React app
echo -e "${YELLOW}📦 Building React application...${NC}"
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Build failed - dist directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build completed successfully${NC}"

# Create S3 bucket
echo -e "${YELLOW}🪣 Creating S3 bucket: ${BUCKET_NAME}${NC}"

if aws s3 mb s3://${BUCKET_NAME} --region ${REGION}; then
    echo -e "${GREEN}✅ S3 bucket created: ${BUCKET_NAME}${NC}"
else
    echo -e "${RED}❌ Failed to create S3 bucket${NC}"
    exit 1
fi

# Configure bucket for static website hosting
echo -e "${YELLOW}🌐 Configuring static website hosting...${NC}"

aws s3 website s3://${BUCKET_NAME} \
    --index-document index.html \
    --error-document index.html \
    --region ${REGION}

# Create bucket policy for public read access
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${BUCKET_NAME} \
    --policy file://bucket-policy.json \
    --region ${REGION}

rm bucket-policy.json

echo -e "${GREEN}✅ Static website hosting configured${NC}"

# Upload files to S3
echo -e "${YELLOW}📤 Uploading files to S3...${NC}"

aws s3 sync dist/ s3://${BUCKET_NAME} \
    --region ${REGION} \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "*.html" \
    --exclude "*.json"

# Upload HTML files with shorter cache
aws s3 sync dist/ s3://${BUCKET_NAME} \
    --region ${REGION} \
    --delete \
    --cache-control "public, max-age=0, must-revalidate" \
    --include "*.html" \
    --include "*.json"

echo -e "${GREEN}✅ Files uploaded to S3${NC}"

# Create CloudFront distribution
echo -e "${YELLOW}☁️ Creating CloudFront distribution...${NC}"

cat > distribution-config.json << EOF
{
    "CallerReference": "${PROJECT_NAME}-$(date +%s)",
    "Comment": "${DISTRIBUTION_COMMENT}",
    "DefaultCacheBehavior": {
        "TargetOriginId": "${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3-website.${REGION}.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "Enabled": true,
    "DefaultRootObject": "index.html",
    "PriceClass": "PriceClass_100",
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    }
}
EOF

DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://distribution-config.json \
    --region ${REGION} \
    --query 'Distribution.Id' \
    --output text)

rm distribution-config.json

if [ -n "$DISTRIBUTION_ID" ]; then
    echo -e "${GREEN}✅ CloudFront distribution created: ${DISTRIBUTION_ID}${NC}"
else
    echo -e "${RED}❌ Failed to create CloudFront distribution${NC}"
    exit 1
fi

# Get distribution domain name
DISTRIBUTION_DOMAIN=$(aws cloudfront get-distribution \
    --id ${DISTRIBUTION_ID} \
    --query 'Distribution.DomainName' \
    --output text)

# Get S3 website URL
S3_WEBSITE_URL="http://${BUCKET_NAME}.s3-website.${REGION}.amazonaws.com"

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo "  • S3 Bucket: ${BUCKET_NAME}"
echo "  • S3 Website URL: ${S3_WEBSITE_URL}"
echo "  • CloudFront Distribution ID: ${DISTRIBUTION_ID}"
echo "  • CloudFront URL: https://${DISTRIBUTION_DOMAIN}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "  1. CloudFront distribution is deploying (takes 5-15 minutes)"
echo "  2. Test S3 website: ${S3_WEBSITE_URL}"
echo "  3. Once deployed, access via: https://${DISTRIBUTION_DOMAIN}"
echo "  4. Update your dashboard-api Lambda with CORS for: https://${DISTRIBUTION_DOMAIN}"
echo ""
echo -e "${GREEN}✅ Dashboard is now live and ready for your demo video!${NC}"

# Save deployment info
cat > deployment-info.txt << EOF
ORM-MVP Dashboard Deployment Information
Generated: $(date)

S3 Bucket: ${BUCKET_NAME}
S3 Website URL: ${S3_WEBSITE_URL}
CloudFront Distribution ID: ${DISTRIBUTION_ID}
CloudFront URL: https://${DISTRIBUTION_DOMAIN}
Region: ${REGION}

Commands to manage deployment:
- Update files: aws s3 sync dist/ s3://${BUCKET_NAME} --delete
- Invalidate CloudFront: aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --paths "/*"
- Delete resources: aws s3 rb s3://${BUCKET_NAME} --force && aws cloudfront delete-distribution --id ${DISTRIBUTION_ID}
EOF

echo "Deployment info saved to: deployment-info.txt"