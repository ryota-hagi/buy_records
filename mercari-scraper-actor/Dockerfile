# Use the official Apify base image
FROM apify/actor-node:16

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm --quiet set progress=false \
    && npm install --only=prod --no-optional

# Copy source code
COPY . ./

# Run the actor
CMD npm start
