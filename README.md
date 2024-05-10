# CareerHub: Backend

CareerHub is a Job/Internship Platform with AI Magic for Fast Placements. The Documentation of the API can be accessed at the `/docs` endpoint.

## Installation

1. Install Pipenv

```bash
pip3 install pipenv
```

2. Install Dependencies

```bash
pipenv install
```

3. Run the Application

```bash
pipenv run uvicorn app:app --reload --host 0.0.0.0
```

## API Documentation

The API is built using FastAPI, and the documentation is automatically generated using OpenAPI standards. You can access the interactive documentation at the `/docs` endpoint when the application is running.

## File Structure

- `app.py`: This file contains the main FastAPI application and all the API routes and logic.
- `data_class.py`: This file contains the Pydantic data models used in the application.

## API Routes

### User Registration and Authentication

- `POST /register`: Register a new user with basic information, education, skills, languages, and password.
- `POST /token`: Get a JWT token by providing username and password.

### User Profile

- `GET /resume`: Get the current user's resume.
- `PUT /resume`: Modify the current user's resume.
- `PUT /change-password`: Change the current user's password.

### Company and Recruiter Management

- `POST /register/company`: Register a new company.
- `DELETE /register/company`: Unregister a company.
- `POST /register/recruiter`: Register a user as a recruiter for a company.
- `DELETE /register/recruiter`: Remove a user as a recruiter from a company.
- `GET /recruiter`: Get a list of all recruiters.
- `GET /company`: Get a list of all companies.
- `GET /company/{company_handle}`: Get details of a specific company.
- `GET /company/{company_handle}/recruiters`: Get a list of recruiters for a specific company.

### Job and Internship Opportunities

- `POST /opportunities`: Create a new job or internship opportunity.
- `GET /opportunities`: Get a list of job and internship opportunities with filtering options.
- `GET /opportunities/{opportunity_id}`: Get details of a specific job or internship opportunity.
- `PUT /opportunities/{opportunity_id}`: Update an existing job or internship opportunity.
- `DELETE /opportunities/{opportunity_id}`: Delete a job or internship opportunity.
- `POST /opportunities/{opportunity_id}/apply`: Apply for a job or internship opportunity.
- `GET /opportunities/{opportunity_id}/applications`: Get a list of candidates who applied for a job or internship opportunity.

## Environment Variables

The application requires the following environment variables to be set:

- `MONGODB_URI`: The connection URI for the MongoDB database.
- `TOKEN_SECRET_KEY`: The secret key used for generating and verifying JWT tokens.
- `ACCESS_TOKEN_EXPIRE_MINUTES` (optional): The expiration time for access tokens in minutes (default: 20).

This README provides an overview of the application, installation instructions, API documentation structure, file structure, API routes, and required environment variables. You can modify and expand this documentation further based on your specific requirements.
