#!/bin/bash
# installer.sh - 安装器模块

install_uv_interactive() {
    echo "=== UV Installation ==="
    echo "UV can be installed via multiple methods:"
    echo "  1) Homebrew (macOS/Linux)"
    echo "  2) NPM (Cross-platform)"
    echo "  3) Pip (Python package manager)"
    echo "  4) Cargo (Rust package manager)"
    echo "  5) Curl (Official installer script)"
    echo ""

    local managers=($(detect_package_managers))
    echo "Detected package managers: ${managers[*]-none}"
    echo ""

    read -p "Select installation method (1-5): " choice

    case $choice in
        1)
            if [[ " ${managers[*]} " =~ " homebrew " ]]; then
                brew install uv
                return $?
            else
                echo "Homebrew not found. Please install Homebrew first."
                return 1
            fi
            ;;
        2)
            if [[ " ${managers[*]} " =~ " npm " ]]; then
                npm install -g uv
                return $?
            else
                echo "NPM not found. Please install Node.js first."
                return 1
            fi
            ;;
        3)
            if [[ " ${managers[*]} " =~ " pip " ]]; then
                pip install uv
                return $?
            else
                echo "Pip not found. Please install Python first."
                return 1
            fi
            ;;
        4)
            if [[ " ${managers[*]} " =~ " cargo " ]]; then
                cargo install uv
                return $?
            else
                echo "Cargo not found. Please install Rust first."
                return 1
            fi
            ;;
        5)
            curl -LsSf https://astral.sh/uv/install.sh | sh
            return $?
            ;;
        *)
            echo "Invalid choice. Aborting."
            return 1
            ;;
    esac
}

install_python() {
    local version="${1:-}"

    echo "=== Python Installation ==="

    local uv_path=$(detect_uv)
    if [[ -z "$uv_path" ]]; then
        echo "UV not found. Cannot install Python without UV."
        return 1
    fi

    if [[ -n "$version" ]]; then
        echo "Installing Python $version via UV..."
        "$uv_path" python install "$version"
        return $?
    else
        echo "Installing latest Python via UV..."
        "$uv_path" python install
        return $?
    fi
}

install_uv_via_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first."
        return 1
    fi

    echo "Installing UV via Homebrew..."
    brew install uv
    return $?
}

install_uv_via_npm() {
    if ! command -v npm &> /dev/null; then
        echo "NPM not found. Please install Node.js first."
        return 1
    fi

    echo "Installing UV via NPM..."
    npm install -g uv
    return $?
}

install_uv_via_pip() {
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo "Pip not found. Please install Python first."
        return 1
    fi

    echo "Installing UV via Pip..."
    pip install uv || pip3 install uv
    return $?
}

install_uv_via_cargo() {
    if ! command -v cargo &> /dev/null; then
        echo "Cargo not found. Please install Rust first."
        return 1
    fi

    echo "Installing UV via Cargo..."
    cargo install uv
    return $?
}

install_uv_via_curl() {
    echo "Installing UV via official installer script..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    return $?
}

install_uv_auto() {
    local managers=($(detect_package_managers))

    if [[ " ${managers[*]} " =~ " homebrew " ]]; then
        install_uv_via_homebrew
        return $?
    elif [[ " ${managers[*]} " =~ " npm " ]]; then
        install_uv_via_npm
        return $?
    elif [[ " ${managers[*]} " =~ " pip " ]]; then
        install_uv_via_pip
        return $?
    elif [[ " ${managers[*]} " =~ " cargo " ]]; then
        install_uv_via_cargo
        return $?
    elif [[ " ${managers[*]} " =~ " curl " ]]; then
        install_uv_via_curl
        return $?
    else
        echo "No package managers found. Cannot install UV."
        return 1
    fi
}

export -f install_uv_interactive install_python
export -f install_uv_via_homebrew install_uv_via_npm install_uv_via_pip install_uv_via_cargo install_uv_via_curl install_uv_auto
