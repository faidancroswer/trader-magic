#!/bin/sh
# Script to check Ollama status and restart if needed

echo "Checking Ollama status..."

# Check if Ollama container is running
if docker ps | grep -q ollama; then
  echo "Ollama container is running"
  
  # Check if Ollama API is responding
  if curl -s http://ollama:11434/api/version > /dev/null 2>&1; then
    echo "Ollama API is responding"
    
    # Check if the required model is available
    MODEL="${OLLAMA_MODEL:-llama3.2:1b}"
    if curl -s http://ollama:11434/api/tags | jq -r '.models[].name' | grep -q "^${MODEL}$"; then
      echo "Required model $MODEL is available"
      exit 0
    else
      echo "Required model $MODEL is not available, pulling model..."
      curl --max-time 300 -X POST http://ollama:11434/api/pull \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$MODEL\"}"
      echo "Model pull initiated"
      exit 0
    fi
  else
    echo "Ollama API is not responding, restarting container..."
    docker restart ollama
    exit 1
  fi
else
  echo "Ollama container is not running, starting container..."
  docker start ollama
  exit 1
fi