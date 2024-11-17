# Banking System with Client-Server Architecture

This project implements a secure banking system using a client-server architecture. It allows users to register, login, create accounts, and perform transactions such as withdrawals and deposits. The system also includes role-based access control and admin features.

## Features

- User registration and login
- Account creation with initial balance
- Transaction functionality (withdraw/deposit)
- Secure password storage using hashing
- SSL certificate implementation for encrypted communication
- Role-based access control
- Admin panel with downtime monitoring

## Technologies Used

- Python
- Flask (Web framework)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- SSL for secure communication

## Prerequisites

- Python 3.7+
- PostgreSQL

## Installation

1. Clone the repository:

```bash
git clone https://github.com/divyesh-rathod/banking_system_python.git
cd banking-system
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

- On Windows:
  ```
  venv\Scripts\activate
  ```
- On macOS and Linux:
  ```
  source venv/bin/activate
  ```

4. Install the required packages:

```bash
pip install -r requirements.txt
```

5. Set up the PostgreSQL database and update the connection string in `config.py`.

## Usage

To start the application, run:

```bash
python app.py
```

The server will start, and you can access the application through a web browser at `https://localhost:5000`.

## Security Features

- Passwords are securely hashed before storage
- SSL certificate is used for encrypted client-server communication
- Role-based access control restricts user actions based on their assigned role

## Admin Features

Administrators have access to additional features, including:

- Viewing system downtime
- Managing user roles
- Monitoring transaction logs


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask documentation
- PostgreSQL documentation
- SQLAlchemy documentation

For any additional information or support, please contact the project maintainers.

