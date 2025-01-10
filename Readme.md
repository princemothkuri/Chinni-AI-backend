# ChinniAI Backend

ChinniAI is an advanced AI-powered assistant designed to help users manage their tasks, alarms, and more. It integrates with various tools to provide a seamless experience for managing daily activities and retrieving information. The backend is built using FastAPI, providing a robust and scalable architecture for handling requests and managing data.

## Features

- **Task Management**: Create, update, and manage tasks and subtasks with ease. Set priorities, due dates, and track progress.
- **Alarm Notifications**: Set alarms with customizable repeat patterns and receive timely notifications.
- **AI Integration**: Leverage AI capabilities to interact with the assistant for various queries and tasks.
- **WebSocket Support**: Real-time notifications and updates using WebSocket connections.
- **Cron Jobs**: Automated background tasks for sending notifications and managing alarms.

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB
- Node.js (for frontend, if applicable)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/princemothkuri/Chinni-AI-backend.git
   cd Chinni-AI-backend
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   - Create a `.env` file in the root directory.
   - Add necessary environment variables, such as `SERPAPI_API_KEY`, `FRONTEND_URL`, and database connection strings.

5. **Run the application**:
   ```bash
   uvicorn main:create_app --host 0.0.0.0 --port 8000 --reload
   ```

### Usage

- Access the API documentation at `http://localhost:8000/docs` to explore available endpoints and test the API.
- Integrate with the frontend by setting the `FRONTEND_URL` in the `.env` file.

### Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.
