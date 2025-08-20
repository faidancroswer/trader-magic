# Troubleshooting Ollama Connection Issues

If you're seeing "Failed to connect to Ollama after multiple attempts" in the dashboard, follow these steps:

## 1. Check if Ollama container is running

```bash
docker compose ps | grep ollama
```

You should see the ollama container in the "running" state.

## 2. Check Ollama logs

```bash
docker compose logs ollama
```

Look for any error messages or startup issues.

## 3. Check if Ollama API is responding

```bash
curl http://localhost:11434/api/version
```

You should get a JSON response with version information.

## 4. Check available models

```bash
curl http://localhost:11434/api/tags
```

Verify that your configured model (default: llama3.2:1b) is listed.

## 5. Manually pull the model

If the model is not available, you can manually pull it:

```bash
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3.2:1b"}'
```

## 6. Restart services

If the above steps don't resolve the issue, restart the services:

```bash
./restart.sh
```

## 7. Check the Ollama status script

Run the dedicated status checker:

```bash
python scripts/check_ollama_status.py
```

This will provide detailed information about the Ollama connection and model status.

## Common Issues

1. **Model not downloading**: The llama3.2:1b model is quite large (~1.8GB). Ensure you have enough disk space and a stable internet connection.

2. **Docker network issues**: Make sure all containers are on the same Docker network and can communicate with each other.

3. **Resource constraints**: Ollama requires sufficient RAM to run models. The llama3.2:1b model needs at least 2GB of RAM.

4. **Windows-specific issues**: On Windows, ensure Docker Desktop is properly configured and has access to the required resources.

If you continue to experience issues, please check the GitHub issues or create a new one with the output of:
- `docker compose logs ollama`
- `docker compose logs ai_decision`
- `python scripts/check_ollama_status.py`