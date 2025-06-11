import pandas as pd
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import os
import csv
from email_manager.models import CustomUser

class Command(BaseCommand):
    help = 'Merges email, proxy, and status CSVs into a master file for bulk import'




    def add_arguments(self, parser):
        parser.add_argument(
            '--emails',
            type=str,
            required=True,
            help='Path to emails CSV (required columns: username, email)'
        )
        parser.add_argument(
            '--proxies',
            type=str,
            required=True,
            help='Path to proxies CSV (required columns: username, proxy_address)'
        )
        parser.add_argument(
            '--statuses',
            type=str,
            required=True,
            help='Path to statuses CSV (required columns: username, is_connected, is_active_profile)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='merged_users.csv',
            help='Output file path (default: merged_users.csv)'
        )
        parser.add_argument(
            '--fill-missing',
            action='store_true',
            help='Fill missing values with defaults instead of failing'
        )

    def handle(self, *args, **options):
        try:
            # Read all input files
            emails_df = self.read_csv_safe(options['emails'], 'emails')
            proxies_df = self.read_csv_safe(options['proxies'], 'proxies')
            statuses_df = self.read_csv_safe(options['statuses'], 'statuses')

            # Validate required columns
            self.validate_columns(emails_df, 'emails', ['username', 'email'])
            self.validate_columns(proxies_df, 'proxies', ['username', 'proxy_address'])
            self.validate_columns(statuses_df, 'statuses', ['username', 'is_connected', 'is_active_profile'])

            # Merge strategy
            merged_df = self.merge_dataframes(
                emails_df,
                proxies_df,
                statuses_df,
                fill_missing=options['fill_missing']
            )

            # Generate passwords for new users
            merged_df['temp_password'] = [
                get_random_secret_key()[:12] for _ in range(len(merged_df))
            ]

            # Save output
            self.save_output(merged_df, options['output'])
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully merged {len(merged_df)} users to {options["output"]}')
            )
            self.stdout.write(
                self.style.NOTICE('Note: temp_password column contains generated passwords for new users')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Merge failed: {str(e)}')
            )

    def read_csv_safe(self, path, name):
        """Read CSV with error handling"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} CSV not found at {path}")
        try:
            return pd.read_csv(path)
        except Exception as e:
            raise ValueError(f"Invalid {name} CSV format: {str(e)}")

    def validate_columns(self, df, name, required_columns):
        """Validate required columns exist"""
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(
                f"{name} CSV missing required columns: {', '.join(missing)}"
            )

    def merge_dataframes(self, emails, proxies, statuses, fill_missing=False):
        """Merge data with different join strategies"""
        # First merge emails and proxies
        merged = pd.merge(
            emails,
            proxies,
            on='username',
            how='outer' if fill_missing else 'inner'
        )
        
        # Then merge with statuses
        merged = pd.merge(
            merged,
            statuses,
            on='username',
            how='outer' if fill_missing else 'inner'
        )
        
        # Fill missing values if requested
        if fill_missing:
            defaults = {
                'proxy_address': 'none',
                'is_connected': False,
                'is_active_profile': True
            }
            merged.fillna(defaults, inplace=True)
        
        return merged

    def save_output(self, df, output_path):
        """Save output with error handling"""
        try:
            df.to_csv(output_path, index=False)
        except Exception as e:
            raise IOError(f"Could not write output file: {str(e)}")
    
    