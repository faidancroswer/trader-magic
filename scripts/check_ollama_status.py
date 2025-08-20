#!/usr/bin/env python3
"""
Script to check Ollama status and diagnose connection issues
"""

import os
import sys
import json
import httpx
import time
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def resolve_host(hostname):
    """Resolve hostname to IP address"""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None

def check_ollama_status():
    """Check Ollama status and diagnose issues"""
    print("Checking Ollama status...")
    
    # Get configuration
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    
    print(f"Ollama Host: {ollama_host}")
    print(f"Expected Model: {ollama_model}")
    
    # Parse host and port from URL
    if "://" in ollama_host:
        host_and_port = ollama_host.split("://")[1]
    else:
        host_and_port = ollama_host
    
    if ":" in host_and_port:
        host, port = host_and_port.split(":")
        port = int(port)
    else:
        host = host_and_port
        port = 11434
    
    # Try to resolve the hostname
    print(f"Resolving hostname '{host}'...")
    ip_address = resolve_host(host)
    if ip_address:
        print(f"[INFO] Host '{host}' resolves to IP: {ip_address}")
    else:
        print(f"[ERROR] Cannot resolve hostname '{host}'")
        # Try localhost as fallback
        host = "localhost"
        print(f"[INFO] Trying localhost instead...")
        ip_address = resolve_host(host)
        if ip_address:
            print(f"[INFO] Host 'localhost' resolves to IP: {ip_address}")
            ollama_host = f"http://localhost:{port}"
        else:
            print(f"[ERROR] Cannot resolve hostname 'localhost'")
            return False
    
    # Check if we can reach the Ollama server
    try:
        print("Testing connection to Ollama server...")
        response = httpx.get(f"{ollama_host}/api/version", timeout=10.0)
        response.raise_for_status()
        version_info = response.json()
        print(f"[OK] Ollama server is running (Version: {version_info.get('version', 'unknown')})")
    except httpx.TimeoutException:
        print("[ERROR] Timeout connecting to Ollama server")
        return False
    except httpx.HTTPError as e:
        print(f"[ERROR] HTTP error connecting to Ollama server: {e}")
        # Try direct localhost connection
        if host != "localhost":
            print("[INFO] Trying direct localhost connection...")
            try:
                direct_url = f"http://localhost:{port}/api/version"
                response = httpx.get(direct_url, timeout=10.0)
                response.raise_for_status()
                version_info = response.json()
                print(f"[OK] Ollama server is running on localhost (Version: {version_info.get('version', 'unknown')})")
                ollama_host = direct_url.replace("/api/version", "")
            except Exception as direct_error:
                print(f"[ERROR] Direct localhost connection also failed: {direct_error}")
                return False
        else:
            return False
    except Exception as e:
        print(f"[ERROR] Error connecting to Ollama server: {e}")
        return False
    
    # Check available models
    try:
        print("Checking available models...")
        response = httpx.get(f"{ollama_host}/api/tags", timeout=10.0)
        response.raise_for_status()
        models_data = response.json()
        models = [model["name"] for model in models_data.get("models", [])]
        
        print(f"Available models: {models}")
        
        if ollama_model in models:
            print(f"[OK] Required model '{ollama_model}' is available")
            return True
        else:
            print(f"[ERROR] Required model '{ollama_model}' is not available")
            # Try to pull the model
            print("Attempting to pull the model...")
            try:
                pull_response = httpx.post(
                    f"{ollama_host}/api/pull",
                    json={"name": ollama_model},
                    timeout=300.0  # 5 minutes timeout for pulling
                )
                pull_response.raise_for_status()
                print("[OK] Model pull initiated successfully")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to pull model: {e}")
                return False
    except Exception as e:
        print(f"[ERROR] Error checking models: {e}")
        return False

if __name__ == "__main__":
    print("=== Ollama Status Checker ===")
    success = check_ollama_status()
    if success:
        print("\n[SUCCESS] Ollama is ready for use")
        sys.exit(0)
    else:
        print("\n[FAILURE] Ollama is not ready")
        sys.exit(1)