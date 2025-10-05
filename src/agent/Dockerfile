FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all agent files
COPY main_agent.py .
COPY tool_agent.py .
COPY research_agent.py .
COPY api_server.py .

# Copy environment variables file
COPY .env .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the API server
CMD ["python", "api_server.py"]
