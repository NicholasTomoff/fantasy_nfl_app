# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire app source code
COPY . .

# Expose the port your app listens on
EXPOSE 8080

# Run uvicorn with your FastAPI app
# --forwarded-allow-ips=*: Fly terminates TLS and proxies plain HTTP from a
# private address, so without this uvicorn ignores X-Forwarded-Proto and
# builds redirects as http:// -- which an HTTPS page blocks as mixed content.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
