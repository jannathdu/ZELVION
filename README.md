# ZELVION

ZELVION is a subscription-based secure network access platform built with a FastAPI backend and a React/Vite frontend.

The current application includes authentication, subscription management, payment-flow simulation, device management, data-usage tracking, payment history, dashboard reporting, security hardening, database migrations, and a one-command local development startup workflow.

> **Current status:** Core MVP release candidate verified.
>
> Real Alipay/WeChat Pay integration, production rate limiting, deployment infrastructure, and production monitoring are still pending.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Environment Configuration](#environment-configuration)
- [Local Setup](#local-setup)
- [One-Command Development Startup](#one-command-development-startup)
- [Backend](#backend)
- [Frontend](#frontend)
- [Database and Alembic](#database-and-alembic)
- [Testing](#testing)
- [Security](#security)
- [Authentication Flow](#authentication-flow)
- [Subscription Flow](#subscription-flow)
- [Payment Flow](#payment-flow)
- [Device Management](#device-management)
- [Usage and Quota Management](#usage-and-quota-management)
- [API Documentation](#api-documentation)
- [Production Configuration](#production-configuration)
- [Production Deployment Checklist](#production-deployment-checklist)
- [Known Production-Pending Items](#known-production-pending-items)
- [Git Workflow](#git-workflow)

---

# Features

## Authentication

- User registration
- User login
- JWT access tokens
- JWT refresh tokens
- Refresh-token rotation
- Refresh-session persistence
- Logout and refresh-token revocation
- Access-token type enforcement
- Refresh-token replay protection
- Protected routes
- Inactive-user protection
- Password hashing using `pwdlib`
- Strong registration password validation

---

## Subscription Management

- Subscription plan listing
- Active subscription tracking
- Subscription start and expiry dates
- Data quota per subscription
- Maximum device count per subscription
- Subscription renewal flow
- Expired-subscription handling
- Active-subscription duplicate-payment protection

---

## Payment Management

- Payment-order creation
- Payment history
- Pending/success payment states
- User ownership validation
- Atomic payment-success + subscription activation
- Payment callback retry idempotency
- Provider transaction ID uniqueness
- Concurrent duplicate payment-order protection
- Mock payment activation for development only

> The current payment-success flow is a development/mock implementation.
> Real Alipay and WeChat Pay provider verification is not yet implemented.

---

## Device Management

- Register devices
- List user devices
- Revoke devices
- Maximum active-device enforcement
- Active-subscription requirement
- Duplicate device protection
- Concurrent registration serialization
- Device ownership protection

---

## Usage Management

- Record data usage
- Current-subscription usage isolation
- Data quota enforcement
- Usage summary
- Remaining-data calculation
- Concurrent quota update serialization

---

## Dashboard

The dashboard provides:

- Current subscription
- Subscription status
- Active device count
- Maximum allowed devices
- Current data usage
- Remaining data
- Latest payment status
- Available plans
- Account status

---

# Technology Stack

## Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Pydantic 2
- Pydantic Settings
- PyJWT
- pwdlib / Argon2
- psycopg
- pytest
- Uvicorn

## Frontend

- React
- TypeScript
- Vite
- React Router
- ESLint

## Database

- PostgreSQL

---

# Project Structure

```text
ZELVION/
│
├── backend/
│   ├── alembic.ini
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── dashboard.py
│   │   │       ├── data_usage.py
│   │   │       ├── devices.py
│   │   │       ├── health.py
│   │   │       ├── payments.py
│   │   │       ├── subscriptions.py
│   │   │       └── router.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   │
│   │   ├── db/
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── services/
│   │   │
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── pages/
│   │   ├── App.tsx
│   │   └── ...
│   │
│   ├── .env.example
│   ├── package.json
│   └── vite.config.*
│
├── .env.example
├── .gitignore
├── pytest.ini
├── start-dev.ps1
└── README.md