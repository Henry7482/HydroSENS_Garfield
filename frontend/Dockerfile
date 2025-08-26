# Development build for React/Vite application
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Expose port 5173 (Vite's default dev server port)
EXPOSE 5173

# Start the development server
CMD ["npm", "run", "dev"]
