import os
import sys
import django
import sqlite3
from datetime import datetime
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
from accounts.models import *
from customers.models import *
from inventory.models import *
from orders.models import *
from inspections.models import *
from installations.models import *

User = get_user_model()

def transfer_data():
    try:
        print("Starting data transfer process...")
        print("Connecting to SQLite database...")
        
        # Connect to SQLite database
        sqlite_conn = sqlite3.connect('db.sqlite3')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Test PostgreSQL connection
        print("Testing PostgreSQL connection...")
        try:
            User.objects.count()
            print("PostgreSQL connection successful!")
        except OperationalError as e:
            print(f"Error connecting to PostgreSQL: {str(e)}")
            return
        
        with transaction.atomic():
            # Transfer Branches first (since they are referenced by other models)
            print("\nTransferring Branches...")
            sqlite_cursor.execute('SELECT * FROM accounts_branch')
            branches = sqlite_cursor.fetchall()
            
            sqlite_cursor.execute('PRAGMA table_info(accounts_branch)')
            column_names = [column[1] for column in sqlite_cursor.fetchall()]
            
            for branch in branches:
                branch_dict = dict(zip(column_names, branch))
                try:
                    if not Branch.objects.filter(code=branch_dict['code']).exists():
                        new_branch = Branch(
                            id=branch_dict['id'],
                            code=branch_dict['code'],
                            name=branch_dict['name'],
                            address=branch_dict['address'] or '',
                            phone=branch_dict['phone'] or '',
                            email=branch_dict['email'] or '',
                            is_main_branch=branch_dict['is_main_branch'],
                            is_active=branch_dict['is_active']
                        )
                        new_branch.save()
                        print(f"✓ Created branch: {branch_dict['name']}")
                except Exception as e:
                    print(f"✗ Error creating branch {branch_dict['name']}: {str(e)}")

            # Transfer Users
            print("\nTransferring Users...")
            sqlite_cursor.execute('SELECT * FROM accounts_user')
            users = sqlite_cursor.fetchall()
            
            sqlite_cursor.execute('PRAGMA table_info(accounts_user)')
            columns = sqlite_cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            for user in users:
                user_dict = dict(zip(column_names, user))
                try:
                    if not User.objects.filter(username=user_dict['username']).exists():
                        new_user = User(
                            id=user_dict['id'],
                            password=user_dict['password'],
                            username=user_dict['username'],
                            first_name=user_dict['first_name'],
                            last_name=user_dict['last_name'],
                            email=user_dict['email'],
                            is_staff=user_dict['is_staff'],
                            is_active=user_dict['is_active'],
                            date_joined=user_dict['date_joined'],
                            is_superuser=user_dict['is_superuser'],
                            image=user_dict['image'] or '',
                            phone=user_dict['phone'] or '',
                            is_inspection_technician=user_dict['is_inspection_technician']
                        )
                        # Add branch if exists
                        if user_dict['branch_id']:
                            try:
                                branch = Branch.objects.get(id=user_dict['branch_id'])
                                new_user.branch = branch
                            except Branch.DoesNotExist:
                                print(f"⚠ Branch not found for user {user_dict['username']}")
                        
                        new_user.save()
                        print(f"✓ Created user: {user_dict['username']}")
                except Exception as e:
                    print(f"✗ Error creating user {user_dict['username']}: {str(e)}")
            
            # Transfer Customers
            print("\nTransferring Customers...")
            sqlite_cursor.execute('SELECT * FROM customers_customer')
            customers = sqlite_cursor.fetchall()
            
            sqlite_cursor.execute('PRAGMA table_info(customers_customer)')
            column_names = [column[1] for column in sqlite_cursor.fetchall()]
            
            for customer in customers:
                customer_dict = dict(zip(column_names, customer))
                try:
                    if not Customer.objects.filter(code=customer_dict['code']).exists():
                        new_customer = Customer(
                            id=customer_dict['id'],
                            code=customer_dict['code'],
                            name=customer_dict['name'],
                            phone=customer_dict['phone'] or '',
                            email=customer_dict['email'] or '',
                            address=customer_dict['address'] or '',
                            customer_type=customer_dict['customer_type'],
                            status=customer_dict.get('status', 'active'),
                            created_at=customer_dict['created_at'],
                            updated_at=customer_dict['updated_at']
                        )
                        if 'branch_id' in customer_dict and customer_dict['branch_id']:
                            try:
                                branch = Branch.objects.get(id=customer_dict['branch_id'])
                                new_customer.branch = branch
                            except Branch.DoesNotExist:
                                print(f"⚠ Branch not found for customer {customer_dict['name']}")
                        
                        new_customer.save()
                        print(f"✓ Created customer: {customer_dict['name']}")
                except Exception as e:
                    print(f"✗ Error creating customer {customer_dict['name']}: {str(e)}")

            # Transfer Categories
            print("\nTransferring Product Categories...")
            sqlite_cursor.execute('SELECT * FROM inventory_category')
            categories = sqlite_cursor.fetchall()
            
            sqlite_cursor.execute('PRAGMA table_info(inventory_category)')
            column_names = [column[1] for column in sqlite_cursor.fetchall()]
            
            for category in categories:
                category_dict = dict(zip(column_names, category))
                try:
                    if not Category.objects.filter(name=category_dict['name']).exists():
                        new_category = Category(
                            id=category_dict['id'],
                            name=category_dict['name'],
                            description=category_dict['description'] or ''
                        )
                        new_category.save()
                        print(f"✓ Created category: {category_dict['name']}")
                except Exception as e:
                    print(f"✗ Error creating category {category_dict['name']}: {str(e)}")

            # Transfer Products
            print("\nTransferring Products...")
            sqlite_cursor.execute('SELECT * FROM inventory_product')
            products = sqlite_cursor.fetchall()
            
            sqlite_cursor.execute('PRAGMA table_info(inventory_product)')
            column_names = [column[1] for column in sqlite_cursor.fetchall()]
            
            for product in products:
                product_dict = dict(zip(column_names, product))
                try:
                    if not Product.objects.filter(code=product_dict['code']).exists():
                        category = Category.objects.get(id=product_dict['category_id'])
                        new_product = Product(
                            id=product_dict['id'],
                            name=product_dict['name'],
                            code=product_dict['code'],
                            category=category,
                            unit=product_dict.get('unit', 'piece'),
                            description=product_dict['description'] or '',
                            price=product_dict['price'],
                            minimum_stock=product_dict['minimum_stock'],
                            created_at=product_dict['created_at'],
                            updated_at=product_dict['updated_at']
                        )
                        new_product.save()
                        print(f"✓ Created product: {product_dict['name']}")
                except Exception as e:
                    print(f"✗ Error creating product {product_dict['name']}: {str(e)}")

        sqlite_conn.close()
        print("\n✓ Data transfer completed successfully!")
        
    except Exception as e:
        print(f"\n✗ An error occurred during data transfer: {str(e)}")
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        raise

if __name__ == '__main__':
    transfer_data()