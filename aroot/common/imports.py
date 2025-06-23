# Standard library imports commonly used across the application
import os
import json
import datetime
from typing import Any, Dict, List, Optional, Union

# External libraries
import requests

# Flask framework
from flask import Blueprint, request, flash, render_template, jsonify, redirect, url_for, session

# SQLAlchemy imports
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text, and_

# Internal service imports
from service.redis_client import get_redis

# Repository imports
from repository.unit_of_work import UnitOfWork
from repository.customers_repository import CustomersRepository

# Service imports
from service.customers_service import CustomersService