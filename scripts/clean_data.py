#!/usr/bin/env python3
"""
Data cleaning script for Raspberry Pi temperature monitoring system.
This script allows you to wipe out all stored data in the database.
"""

import os
import sqlite3
import argparse
import logging
from datetime import datetime

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_database_info(db_path):
    """Get information about the database."""
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    info = {}
    
    # Get table information
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    info['tables'] = {}
    total_records = 0
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        info['tables'][table] = count
        total_records += count
    
    info['total_records'] = total_records
    
    # Get database size
    info['size_bytes'] = os.path.getsize(db_path)
    info['size_mb'] = round(info['size_bytes'] / (1024 * 1024), 2)
    
    # Get date range
    try:
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM temperature_readings")
        date_range = cursor.fetchone()
        if date_range[0] and date_range[1]:
            info['date_range'] = {
                'start': date_range[0],
                'end': date_range[1]
            }
    except:
        pass
    
    conn.close()
    return info

def clean_all_data(db_path, confirm=False):
    """Clean all data from all tables."""
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    if not confirm:
        info = get_database_info(db_path)
        if info and info['total_records'] > 0:
            print(f"\n⚠️  Warning: This will delete ALL temperature data!")
            print(f"Database: {db_path}")
            print(f"Total records: {info['total_records']}")
            print(f"Database size: {info['size_mb']} MB")
            
            if 'date_range' in info:
                print(f"Data range: {info['date_range']['start']} to {info['date_range']['end']}")
            
            response = input("\nAre you sure you want to delete all data? Type 'YES' to confirm: ")
            if response != 'YES':
                print("Operation cancelled.")
                return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        total_deleted = 0
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count_before = cursor.fetchone()[0]
            
            cursor.execute(f"DELETE FROM {table}")
            deleted = cursor.rowcount
            total_deleted += deleted
            
            if deleted > 0:
                logging.info(f"Deleted {deleted} records from {table}")
        
        # Reset auto-increment counters
        for table in tables:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Successfully deleted {total_deleted} total records")
        
        # Vacuum database to reclaim space
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        
        logging.info("✅ Database vacuumed to reclaim space")
        
        return True
        
    except Exception as e:
        logging.error(f"Error cleaning database: {e}")
        return False

def clean_old_data(db_path, days, confirm=False):
    """Clean data older than specified days."""
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count records to be deleted
        tables = ['temperature_readings', 'storage_temperatures', 'external_temperatures']
        total_to_delete = 0
        
        for table in tables:
            try:
                cursor.execute(f'''
                    SELECT COUNT(*) FROM {table} 
                    WHERE timestamp < datetime('now', '-{days} days')
                ''')
                count = cursor.fetchone()[0]
                total_to_delete += count
            except:
                continue
        
        if total_to_delete == 0:
            logging.info(f"No records older than {days} days found")
            conn.close()
            return True
        
        if not confirm:
            print(f"\n⚠️  This will delete {total_to_delete} records older than {days} days")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                conn.close()
                return False
        
        # Delete old data
        total_deleted = 0
        for table in tables:
            try:
                cursor.execute(f'''
                    DELETE FROM {table} 
                    WHERE timestamp < datetime('now', '-{days} days')
                ''')
                deleted = cursor.rowcount
                total_deleted += deleted
                if deleted > 0:
                    logging.info(f"Deleted {deleted} old records from {table}")
            except Exception as e:
                logging.warning(f"Error cleaning {table}: {e}")
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Successfully deleted {total_deleted} old records")
        
        return True
        
    except Exception as e:
        logging.error(f"Error cleaning old data: {e}")
        return False

def show_database_status(db_path):
    """Show database status information."""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    info = get_database_info(db_path)
    if not info:
        print(f"❌ Could not read database: {db_path}")
        return
    
    print(f"\n📊 Database Status: {db_path}")
    print("=" * 50)
    print(f"Size: {info['size_mb']} MB ({info['size_bytes']} bytes)")
    print(f"Total records: {info['total_records']}")
    
    if 'date_range' in info:
        print(f"Date range: {info['date_range']['start']} to {info['date_range']['end']}")
    
    print("\nTables:")
    for table, count in info['tables'].items():
        print(f"  {table}: {count} records")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Clean temperature monitoring database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show database status
  python3 scripts/clean_data.py --status
  
  # Delete all data (with confirmation)
  python3 scripts/clean_data.py --clean-all
  
  # Delete all data without confirmation (dangerous!)
  python3 scripts/clean_data.py --clean-all --force
  
  # Delete data older than 30 days
  python3 scripts/clean_data.py --clean-old 30
  
  # Delete data older than 7 days without confirmation
  python3 scripts/clean_data.py --clean-old 7 --force
        """
    )
    
    parser.add_argument(
        '--database', '-d',
        default='data/temperature_data.db',
        help='Path to database file (default: data/temperature_data.db)'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show database status information'
    )
    
    parser.add_argument(
        '--clean-all', '-a',
        action='store_true',
        help='Delete ALL temperature data (requires confirmation)'
    )
    
    parser.add_argument(
        '--clean-old', '-o',
        type=int,
        metavar='DAYS',
        help='Delete data older than specified days'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation prompts (dangerous!)'
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Default to showing status if no action specified
    if not any([args.status, args.clean_all, args.clean_old]):
        args.status = True
    
    if args.status:
        show_database_status(args.database)
    
    if args.clean_all:
        success = clean_all_data(args.database, confirm=args.force)
        if success:
            print("✅ All data cleaned successfully")
        else:
            print("❌ Failed to clean data")
            return 1
    
    if args.clean_old:
        success = clean_old_data(args.database, args.clean_old, confirm=args.force)
        if success:
            print(f"✅ Old data (>{args.clean_old} days) cleaned successfully")
        else:
            print("❌ Failed to clean old data")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
