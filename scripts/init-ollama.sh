#!/bin/sh
# Script to wait for Ollama server and pull the model

# Default to llama3 if not set
MODEL="${OLLAMA_MODEL:-llama3.2:1b}"
echo "Will pull model: $MODEL"

# Wait for Ollama to be ready
echo "Waiting for Ollama server to be ready..."
for i in $(seq 1 60); do
  if curl -s http://ollama:11434/api/version > /dev/null 2>&1; then
    echo "Ollama server is ready!"
    
    # Check if model is already available
    if curl -s http://ollama:11434/api/tags | grep -q "$MODEL"; then
      echo "Model $MODEL is already available"
      exit 0
    else
      echo "Pulling model: $MODEL"
      curl -X POST http://ollama:11434/api/pull -H "Content-Type: application/json" -d "{\"name\":\"$MODEL\"}"
      echo "Model pull initiated. This may take some time to complete."
      
      # Wait for model to be ready
      echo "Waiting for model to be ready..."
      for j in $(seq 1 30); do
        if curl -s http://ollama:11434/api/tags | grep -q "$MODEL"; then
          echo "Model $MODEL is ready!"
          exit 0
        fi
        echo "Waiting for model to be ready (attempt $j/30)"
        sleep 10
      done
      
      echo "Model did not become ready within timeout period"
      exit 1
    fi
  fi
  echo "Waiting for Ollama server (attempt $i/60)"
  sleep 5
done

# If we get here, we timed out
echo "Timed out waiting for Ollama server"
exit 1
