# Chat Service App

This repository contains the Chat Service app, a high-performance real-time messaging platform built using FastAPI, Socket.io, and MongoDB. The Chat Service app provides a robust and feature-rich environment for users to engage in both group chats and private chats with seamless real-time communication.

## Features

- **Real-Time Messaging**: Powered by FastAPI and Socket.io for fast and real-time communication.
- **Group and Private Chats**: Create and join group or private chat rooms with ease.
- **User Authentication**: Uses JWT-based authentication for secure access to chat rooms.
- **Admin Panel**: Manage users and chat rooms with admin APIs.
- **Online Users**: View the list of online users in chat rooms.
- **Multimedia Support**: Send text messages, images, and files in chat rooms.

## Project Structure

- `Chat-Service\server`: Contains all backend code, including FastAPI, database connections, and API routes.
- `Chat-Service\client`: Contains the frontend code for the chat application built with Node.js.

---

## Running the Project Locally

### Step 1: Install MongoDB and Mongosh

You can download and install MongoDB and Mongosh from the [official MongoDB website](https://www.mongodb.com/try/download/community). Follow the instructions for your operating system to install both.

### Step 2: Set up the MongoDB Database

After installing MongoDB, perform the following steps:

1. **Start MongoDB**:
   - On Windows: 
     - Open your terminal.
     - Navigate to the MongoDB installation directory:
       ```bash
       cd "C:\Program Files\MongoDB\Server\<#version>\bin"
       ```
     - Run:
       ```bash
       mongod
       ```
   - On Linux or macOS: Run:
     ```bash
     sudo systemctl start mongod
     ```

2. **Create the `chat_service` database**:
   - Open **Mongosh** and run:
     ```bash
     use chat_service
     ```

3. **Create a username and password for the `chat_service` database**:
   ```bash
   db.createUser({
       user: "your_username",
       pwd: "your_password",
       roles: [{ role: "readWrite", db: "chat_service" }]
   })
   ```

4. **Restart MongoDB to apply the changes:**
   - On Windows:
     - Press `Ctrl+C` inside MongoDB installation directory to stop its server.
     - Run `mongod`.
   - On Linux or macOS: Run:
     ```bash
     sudo systemctl restart mongod
     ```

### Step 3: Install Python Dependencies

Make sure you have Python installed, then:
- Navigate to the project's root directory.
- Install the dependencies from `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### Step 4: Set Up Environment Variables

You need to create two `.env` files
- one for the backend (`Chat-Service\server\.env`) and one for the frontend (`Chat-Service\client\.env`).

**Backend (`Chat-Service\server\.env`):**
  ```env
  SECRET_KEY=<your_generated_secret_key>
  MONGO_USER=<your_mongo_username>
  MONGO_PASSWORD=<your_mongo_password>
  MONGO_HOST=localhost
  MONGO_PORT=27017
  MONGO_DB=chat_service
  ```

**Frontend (`Chat-Service\client\.env`):**
  ```env
  REACT_APP_API_URL=http://localhost:8000
  ```

**Generating a Secret Key**
You can generate a secret key using one of the following methods:

1. Python:
  ```python
  import secrets
  print(secrets.token_urlsafe(32))
  ```

2. OpenSSL:
  ```bash
  openssl rand -base64 32
  ```

3. Django Secret Key Generator (online): [link](https://djecrety.ir/)

### Step 5: Run the FastAPI Backend

Navigate to the backend directory (`Chat-Service\server`) and start the FastAPI server:
  ```bash
  cd Chat-Service\server
  uvicorn main:chat_service_app --reload
  ```

You can access the FastAPI API documentation at http://localhost:8000/docs.

### Step 6: Run the Node.js Frontend (testing Socket.io capabilities)

To test the app's Socket.io capabilities, you'll need to install Node.js from the [official Node.js website](https://nodejs.org/en/download/prebuilt-installer). Then, navigate to the frontend directory (`Chat-Service\client`) and run the following commands:
  ```bash
  cd Chat-Service\client
  npm install
  npm start
  ```

You can test the frontend at http://localhost:3000.

---

## Deploying the Project Using Docker Compose

### Step 1: Prerequisites

Ensure that you have Docker and Docker Compose installed. You can download Docker from [Docker's official website](https://www.docker.com/).

## Step 2: Clone the Repository
  ```bash
  git clone https://github.com/AmirhsFar/danesh-sazan-internship-tasks.git
  cd danesh-sazan-internship-tasks
  ```

### Step 3: Prepare Docker Secrets

Before running the application, you need to securely create the MongoDB username, password, and the FastAPI secret key using Docker Secrets. Here’s how you can do that:
1. Create Docker Secrets for MongoDB Username:
  ```bash
  echo "your_mongo_user" | docker secret create mongo_user -
  ```
2. Create Docker Secrets for MongoDB Password:
  ```bash
  echo "your_mongo_password" | docker secret create mongo_password -
  ```
3. Create Docker Secret for FastAPI Secret Key:
  - Generate a secure secret key using Python (or any method you prefer):
    ```bash
    python3 -c "import secrets; print(secrets.token_hex(32))"
    ```
  - Then, create the Docker Secret:
    ```bash
    echo "your_generated_secret_key" | docker secret create secret_key -
    ```

### Step 4: Build, Run & Set Up Environment Variables with Docker Compose

Once the secrets are set up, build and start the services using Docker Compose with specifying environment variables such as `MONGO_INITDB_DATABASE`, `MONGO_DB`, `MONGO_PORT`, `MONGO_HOST`, and `REACT_APP_API_URL` through the command:
  ```bash
  MONGO_INITDB_DATABASE=chat_service \
  MONGO_DB=chat_service \
  MONGO_PORT=27017 \
  MONGO_HOST=mongo \
  REACT_APP_API_URL=http://localhost:8000 \
  docker-compose up --build
  ```

- `MONGO_INITDB_DATABASE` is used by MongoDB to create the `chat_service` database on initialization.
- `MONGO_DB`, `MONGO_PORT`, and `MONGO_HOST` are used by the FastAPI service to connect to MongoDB.
- `REACT_APP_API_URL` is used by the Node.js frontend to connect to the FastAPI backend.

The build command will build and run the following services:
  - **MongoDB** (database)
  - **FastAPI** (backend)
  - **Node.js** (frontend)
  - **Nginx** (reverse proxy for Node.js and FastAPI)

The application will be available at `http://localhost/`.

### Step 5: Verify MongoDB is Running

Ensure that the MongoDB service is up and running by checking the logs:
  ```bash
  docker logs mongo_db
  ```

You can also connect to the MongoDB instance using a MongoDB client or using mongosh to ensure the chat_service database has been created and that everything is set up properly.

### Step 6: Access the Application

The API documentation for FastAPI will be available at: http://localhost/api/docs.

The frontend will be accessible at: http://localhost/.

---

## Project Flowchart

For a visual understanding of the Chat Service app's workflow, please refer to the `Chat Service Flowchart.jpg` image inside the `server` directory of the `Chat-Service` folder.

---

## Technologies Used

- **FastAPI**: Backend framework for building APIs.
- **Socket.io**: Real-time communication between clients and servers.
- **MongoDB**: NoSQL database for storing chat data.
- **Docker**: Containerization for deploying the app.
- **Nginx**: Reverse proxy for routing requests to Node.js and FastAPI.

For more detailed API information, refer to the FastAPI Swagger docs at `/docs` or check the code under the `server` folder.
