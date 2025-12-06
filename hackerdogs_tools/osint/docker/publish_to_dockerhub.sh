#!/bin/bash
# Publish osint-tools Docker image to Docker Hub
#
# Usage:
#   ./publish_to_dockerhub.sh [username] [tag]
#
# Examples:
#   ./publish_to_dockerhub.sh myusername                    # Publish as myusername/osint-tools:latest
#   ./publish_to_dockerhub.sh myusername v1.0.0            # Publish as myusername/osint-tools:v1.0.0
#   ./publish_to_dockerhub.sh myusername v1.0.0 latest     # Publish with both tags

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="osint-tools"
DEFAULT_TAG="latest"

# Get Docker Hub username
if [ -z "$1" ]; then
    echo -e "${YELLOW}Docker Hub username not provided.${NC}"
    echo ""
    echo "Usage: $0 <dockerhub_username> [tag] [additional_tag...]"
    echo ""
    echo "Examples:"
    echo "  $0 myusername                    # Publish as myusername/osint-tools:latest"
    echo "  $0 myusername v1.0.0            # Publish as myusername/osint-tools:v1.0.0"
    echo "  $0 myusername v1.0.0 latest     # Publish with both v1.0.0 and latest tags"
    echo ""
    read -p "Enter your Docker Hub username: " DOCKERHUB_USERNAME
    if [ -z "$DOCKERHUB_USERNAME" ]; then
        echo -e "${RED}Error: Docker Hub username is required${NC}"
        exit 1
    fi
else
    DOCKERHUB_USERNAME="$1"
fi

# Get tags (default to 'latest' if not provided)
TAGS=("${@:2}")
if [ ${#TAGS[@]} -eq 0 ]; then
    TAGS=("$DEFAULT_TAG")
fi

FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}"

echo "================================================================================="
echo "Publishing OSINT Tools Docker Image to Docker Hub"
echo "================================================================================="
echo "Docker Hub Username: $DOCKERHUB_USERNAME"
echo "Image Name: $IMAGE_NAME"
echo "Tags: ${TAGS[*]}"
echo "Full Image Name: $FULL_IMAGE_NAME"
echo "================================================================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if user is logged in to Docker Hub
echo -e "${YELLOW}Checking Docker Hub authentication...${NC}"
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}You are not logged in to Docker Hub.${NC}"
    echo "Please log in with: docker login"
    read -p "Do you want to log in now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Docker login failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Error: Docker Hub login required${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker Hub authentication verified${NC}"
fi

# Build the image
echo ""
echo -e "${YELLOW}Building Docker image...${NC}"
echo "This may take 5-10 minutes..."
docker build -t "${FULL_IMAGE_NAME}:${TAGS[0]}" .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Tag with additional tags if provided
if [ ${#TAGS[@]} -gt 1 ]; then
    echo ""
    echo -e "${YELLOW}Tagging image with additional tags...${NC}"
    for tag in "${TAGS[@]:1}"; do
        echo "  Tagging as ${FULL_IMAGE_NAME}:${tag}"
        docker tag "${FULL_IMAGE_NAME}:${TAGS[0]}" "${FULL_IMAGE_NAME}:${tag}"
    done
    echo -e "${GREEN}✅ All tags created${NC}"
fi

# Push images to Docker Hub
echo ""
echo -e "${YELLOW}Pushing images to Docker Hub...${NC}"
for tag in "${TAGS[@]}"; do
    echo ""
    echo "Pushing ${FULL_IMAGE_NAME}:${tag}..."
    docker push "${FULL_IMAGE_NAME}:${tag}"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to push ${FULL_IMAGE_NAME}:${tag}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Successfully pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
done

# Summary
echo ""
echo "================================================================================="
echo -e "${GREEN}✅ Publishing Complete!${NC}"
echo "================================================================================="
echo ""
echo "Published images:"
for tag in "${TAGS[@]}"; do
    echo "  - ${FULL_IMAGE_NAME}:${tag}"
done
echo ""
echo "View on Docker Hub:"
echo "  https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
echo ""
echo "Pull command:"
echo "  docker pull ${FULL_IMAGE_NAME}:${TAGS[0]}"
echo "================================================================================="

