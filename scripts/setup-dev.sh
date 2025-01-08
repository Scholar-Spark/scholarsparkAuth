#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to get project name from pyproject.toml
get_project_name() {
    if [[ -f "pyproject.toml" ]]; then
        # Extract name from pyproject.toml using grep and cut
        PROJECT_NAME=$(grep '^name = ' pyproject.toml | cut -d'"' -f2 || echo "")
        if [[ -n "$PROJECT_NAME" ]]; then
            echo "$PROJECT_NAME"
            return 0
        fi
    fi
    
    echo -e "${RED}Error: Could not find project name in pyproject.toml${NC}"
    echo -e "${YELLOW}Please ensure you're in the project root directory with a valid pyproject.toml${NC}"
    exit 1
}

# Get service name from pyproject.toml
SERVICE_NAME=$(get_project_name)
echo -e "${BLUE}Detected service: ${SERVICE_NAME}${NC}"

# Function to detect OS and distribution
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        source /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

# Function to install dependencies based on OS
install_dependencies() {
    local os=$1
    echo -e "${BLUE}Installing dependencies for $os...${NC}"
    
    case $os in
        "macos")
            if ! command -v brew &> /dev/null; then
                echo -e "${YELLOW}Installing Homebrew...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install minikube kubectl skaffold helm
            ;;
            
        "ubuntu"|"debian")
            sudo apt-get update
            sudo apt-get install -y curl wget apt-transport-https
            
            # Install Helm
            curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
            sudo apt-get update
            sudo apt-get install -y helm
            
            # Install minikube
            curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
            sudo install minikube-linux-amd64 /usr/local/bin/minikube
            rm minikube-linux-amd64
            
            # Install kubectl
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install kubectl /usr/local/bin/kubectl
            rm kubectl
            
            # Install Skaffold
            curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
            sudo install skaffold /usr/local/bin/
            rm skaffold
            ;;
            
        "fedora"|"rhel"|"centos")
            sudo dnf install -y curl wget
            
            # Install Helm
            curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
            
            # Install minikube
            curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
            sudo install minikube-linux-amd64 /usr/local/bin/minikube
            rm minikube-linux-amd64
            
            # Install kubectl
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install kubectl /usr/local/bin/kubectl
            rm kubectl
            
            # Install Skaffold
            curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
            sudo install skaffold /usr/local/bin/
            rm skaffold
            ;;
            
        "arch"|"manjaro")
            sudo pacman -Sy --noconfirm curl wget
            sudo pacman -S --noconfirm minikube kubectl helm
            
            # Install Skaffold
            curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
            sudo install skaffold /usr/local/bin/
            rm skaffold
            ;;

        "nixos")
            # For NixOS, we'll guide users to add these to their configuration
            echo -e "${YELLOW}For NixOS, please add the following to your configuration.nix:${NC}"
            echo -e "
environment.systemPackages = with pkgs; [
  docker
  kubectl
  minikube
  skaffold
  helm
];

virtualisation.docker.enable = true;
"
            echo -e "${YELLOW}Then run: sudo nixos-rebuild switch${NC}"
            read -p "Press Enter once you've updated your NixOS configuration..."
            
            # Verify installations
            if ! command -v docker &> /dev/null || \
               ! command -v kubectl &> /dev/null || \
               ! command -v minikube &> /dev/null || \
               ! command -v skaffold &> /dev/null || \
               ! command -v helm &> /dev/null; then
                echo -e "${RED}Some required tools are missing. Please ensure they are added to your NixOS configuration.${NC}"
                exit 1
            fi
            ;;
            
        *)
            echo -e "${RED}Unsupported operating system${NC}"
            exit 1
            ;;
    esac
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}Docker daemon is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

# Function to get service URL
get_service_url() {
    local retries=0
    local max_retries=30
    local service_url=""

    echo -e "${BLUE}Waiting for service URL...${NC}"
    
    while [ $retries -lt $max_retries ]; do
        service_url=$(minikube service ${SERVICE_NAME} -n scholar-spark-dev --url 2>/dev/null)
        if [ -n "$service_url" ]; then
            echo "$service_url"
            return 0
        fi
        retries=$((retries + 1))
        sleep 2
        echo -n "."
    done
    
    echo -e "\n${RED}Could not get service URL. Using localhost:8000 as fallback${NC}"
    echo "http://localhost:8000"
}

# Print developer-friendly information
print_dev_info() {
    clear
    echo -e "🚀 ${GREEN}Scholar Spark Development Environment${NC}\n"
    echo -e "📦 ${BLUE}Service: ${GREEN}${SERVICE_NAME}${NC}\n"
    echo -e "🔗 ${BLUE}API Endpoints:${NC}"
    echo -e "   ${GREEN}→ API:     ${SERVICE_URL}/api/v1"
    echo -e "   → Docs:    ${SERVICE_URL}/docs"
    echo -e "   → Health:  ${SERVICE_URL}/health${NC}\n"
    echo -e "📝 ${BLUE}Development Tips:${NC}"
    echo -e "   ${GREEN}→ Your code changes will automatically reload"
    echo -e "   → API docs are always up-to-date at /docs"
    echo -e "   → Logs will appear below${NC}\n"
    echo -e "🛠️  ${BLUE}Useful Commands:${NC}"
    echo -e "   ${GREEN}→ CTRL+C to stop the service"
    echo -e "   → ./scripts/dev.sh to restart${NC}\n"
    echo -e "📊 ${BLUE}Monitoring:${NC}"
    echo -e "   ${GREEN}→ Traces: http://localhost:3200"
    echo -e "   → Logs:   http://localhost:3100${NC}\n"
    echo -e "${YELLOW}Starting development server...${NC}\n"
}

# Function to setup Helm registry authentication
setup_helm_registry() {
    echo -e "${BLUE}Setting up Helm registry authentication...${NC}"
    
    # Check for required tools
    for cmd in gh jq; do
        if ! command -v $cmd &> /dev/null; then
            case $cmd in
                gh)
                    echo -e "${YELLOW}Installing GitHub CLI...${NC}"
                    case $OS in
                        "macos")
                            brew install gh
                            ;;
                        "ubuntu"|"debian")
                            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
                            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
                            sudo apt update
                            sudo apt install -y gh
                            ;;
                        "fedora"|"rhel"|"centos")
                            sudo dnf install -y gh
                            ;;
                        "arch"|"manjaro")
                            sudo pacman -S --noconfirm github-cli
                            ;;
                    esac
                    ;;
                jq)
                    echo -e "${YELLOW}Installing jq...${NC}"
                    case $OS in
                        "macos")
                            brew install jq
                            ;;
                        "ubuntu"|"debian")
                            sudo apt update && sudo apt install -y jq
                            ;;
                        "fedora"|"rhel"|"centos")
                            sudo dnf install -y jq
                            ;;
                        "arch"|"manjaro")
                            sudo pacman -S --noconfirm jq
                            ;;
                    esac
                    ;;
            esac
        fi
    done

    # GitHub login if not already authenticated
    if ! gh auth status &> /dev/null; then
        echo -e "${YELLOW}Please login to GitHub...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]] || [ -n "$DISPLAY" ]; then
            gh auth login --git-protocol ssh --web
        else
            echo -e "${YELLOW}Please visit https://github.com/login/device in your browser${NC}"
            gh auth login --git-protocol ssh --web
        fi
    fi

    # Get GitHub token
    GITHUB_USER=$(gh api user | jq -r .login)
    echo -e "${GREEN}Authenticated as: ${GITHUB_USER}${NC}"
    
    TOKEN=$(gh auth token)
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Failed to get GitHub token${NC}"
        exit 1
    fi

    # Login to Helm registry
    echo -e "${BLUE}Logging into Helm registry...${NC}"
    if ! helm registry login ghcr.io -u "$GITHUB_USER" -p "$TOKEN"; then
        echo -e "${RED}Failed to login to Helm registry${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Successfully authenticated with Helm registry${NC}"
}

# Main setup process
main() {
    # Load environment variables from .env file
    if [ -f .env ]; then
        echo -e "${BLUE}Loading environment variables from .env file...${NC}"
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo -e "${RED}No .env file found. Please create one based on .env.example${NC}"
        exit 1
    fi

    echo -e "${BLUE}Setting up development environment...${NC}"
    
    # Check Docker first
    check_docker
    
    # Detect OS and install dependencies
    OS=$(detect_os)
    echo -e "${BLUE}Detected OS: $OS${NC}"
    
    # Install dependencies if needed
    if [[ ! -x "$(command -v minikube)" ]] || \
       [[ ! -x "$(command -v kubectl)" ]] || \
       [[ ! -x "$(command -v skaffold)" ]] || \
       [[ ! -x "$(command -v helm)" ]]; then
        install_dependencies "$OS"
    fi
    
    # Setup Helm registry authentication
    setup_helm_registry

    # Start minikube if not running
    if ! minikube status &> /dev/null; then
        echo -e "${BLUE}Starting Minikube...${NC}"
        minikube start --driver=docker
    fi
    
    # Configure Docker to use minikube's Docker daemon
    echo -e "${BLUE}Configuring Docker environment...${NC}"
    eval $(minikube docker-env)
    
    # Create namespace if it doesn't exist
    if ! kubectl get namespace scholar-spark-dev &> /dev/null; then
        echo -e "${BLUE}Creating development namespace...${NC}"
        kubectl create namespace scholar-spark-dev
    fi

    # Start skaffold in the background
    echo -e "${BLUE}Starting Skaffold...${NC}"
    skaffold dev --port-forward &
    SKAFFOLD_PID=$!

    # Wait for service to be ready and get URL
    echo -e "${BLUE}Waiting for service to be ready...${NC}"
    sleep 10  # Give skaffold some time to start deployment

    # Get service URL once and store it
    SERVICE_URL=$(get_service_url)
    
    # Print developer-friendly information
    print_dev_info

    # Wait for skaffold to finish
    wait $SKAFFOLD_PID
}

# Run main function
main
