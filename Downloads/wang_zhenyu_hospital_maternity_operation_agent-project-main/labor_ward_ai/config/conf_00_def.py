# -*- coding: utf-8 -*-

"""
Centralized Configuration Management
====================================

This module implements the **Config Pattern** — a common approach for managing
application configuration across different runtime environments.

Why this pattern?
-----------------

Applications need different configurations in different environments:

- **Local development:** Use ``~/.aws/credentials``, connect to dev databases
- **Vercel/Cloud:** Read secrets from environment variables, connect to prod services

The naive approach scatters ``if runtime.is_vercel()`` checks throughout the codebase.
This leads to:

- Duplicated logic in multiple files
- Hard to track what configuration differs between environments
- Easy to miss a check and introduce bugs

The Config Pattern solves this by **centralizing all environment-specific logic
in one place**.

How it works
------------

1. **Define a Config dataclass** with all configurable values as fields
2. **Create factory methods** for each runtime environment (``new_in_local_runtime``,
   ``new_in_vercel_runtime``)
3. **Expose a singleton** ``config`` instance at module level
4. **Import and use** ``config.xxx`` anywhere in the codebase

Example usage::

    from labor_ward_ai.config import config

    # Anywhere in your code - no environment checks needed
    session = boto3.Session(
        region_name=config.aws_region,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
    )

Benefits
--------

- **One place complex, everywhere else simple** — Environment detection happens
  once in ``Config.new()``. All other code just reads ``config.xxx``.
- **Easy to extend** — Need a new config value? Add a field and set it in the
  factory methods. All existing code continues to work.
- **Testable** — Tests can create ``Config`` instances directly with test values,
  bypassing the runtime detection entirely.
- **Self-documenting** — The dataclass fields serve as documentation of what
  can be configured.

Adding new configuration
------------------------

To add a new configurable value:

1. Add a field to the ``Config`` dataclass
2. Set appropriate values in ``new_in_local_runtime()`` and ``new_in_vercel_runtime()``
3. Use ``config.your_new_field`` anywhere in the codebase

That's it. No need to add ``if runtime.is_xxx()`` checks anywhere else.
"""

import os
import dataclasses

from ..runtime import runtime


@dataclasses.dataclass
class Config:
    """
    Application configuration container.

    This dataclass holds all environment-specific configuration values.
    Use the factory methods to create instances, or use the module-level
    ``config`` singleton for normal application code.

    Attributes:
        aws_region: AWS region for all AWS services (e.g., "us-east-1")
        aws_access_key_id: AWS access key. None means use default credential chain.
        aws_secret_access_key: AWS secret key. None means use default credential chain.
        model_id: Bedrock model ID
        max_message_length: Maximum allowed characters in user message. Prevents abuse.
    """

    aws_region: str | None = dataclasses.field(default=None)
    aws_access_key_id: str | None = dataclasses.field(default=None)
    aws_secret_access_key: str | None = dataclasses.field(default=None)
    model_id: str | None = dataclasses.field(default="us.amazon.nova-micro-v1:0")
    # max_message_length: int = dataclasses.field(default=1000)
    db_host: str | None = dataclasses.field(default=None)
    db_port: int | None = dataclasses.field(default=None)
    db_user: str | None = dataclasses.field(default=None)
    db_pass: str | None = dataclasses.field(default=None)
    db_name: str | None = dataclasses.field(default=None)
    dynamodb_table_name_quota: str | None = dataclasses.field(default=None)
    quota_max_invoke_per_month: int = dataclasses.field(default=1000)
    quota_max_input_token_per_month: int = dataclasses.field(default=50_000_000)
    quota_max_output_token_per_month: int = dataclasses.field(default=10_000_000)

    @classmethod
    def new_in_local_runtime(cls):
        """
        use default credential chain (~/.aws/credentials or IAM role)
        """
        from dotenv import load_dotenv

        load_dotenv()

        return cls(
            aws_region="us-east-1",
            db_host=os.environ["DB_HOST"],
            db_port=int(os.environ["DB_PORT"]),
            db_user=os.environ["DB_USER"],
            db_pass=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"],
            dynamodb_table_name_quota=os.environ["DYNAMODB_TABLE_NAME_QUOTA"],
        )

    @classmethod
    def new_in_vercel_runtime(cls):
        """
        explicit credentials from environment variables (serverless has no ~/.aws)
        """
        return cls(
            aws_region="us-east-1",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            db_host=os.environ["DB_HOST"],
            db_port=int(os.environ["DB_PORT"]),
            db_user=os.environ["DB_USER"],
            db_pass=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"],
            dynamodb_table_name_quota=os.environ["DYNAMODB_TABLE_NAME_QUOTA"],
        )

    @classmethod
    def new(cls):
        """
        Factory method that creates the appropriate Config for the current runtime.

        This is the main entry point for creating Config instances. It automatically
        detects the runtime environment and returns a properly configured instance.

        Returns:
            Config: A Config instance configured for the detected runtime.

        Raises:
            RuntimeError: If the runtime environment is not recognized.
        """
        if runtime.is_local():
            return cls.new_in_local_runtime()
        elif runtime.is_vercel():
            return cls.new_in_vercel_runtime()
        else:  # pragma: no cover
            raise RuntimeError
