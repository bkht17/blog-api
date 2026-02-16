#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv
from django.core.management import execute_from_command_line


def main():
    """Run administrative tasks."""
    base_dir = Path(__file__).resolve().parent
    env_path = base_dir / 'settings' / '.env'
    
    env_config = Config(RepositoryEnv(env_path))
    env_id = env_config('BLOG_ENV_ID', default='local')
    
    os.environ["DJANGO_SETTINGS_MODULE"] = f'settings.env.{env_id}'
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
