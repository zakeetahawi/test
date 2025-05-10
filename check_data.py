import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from customers.models import Customer
from inventory.models import Product, Category

User = get_user_model()

def check_data():
    print("Checking transferred data:")
    print("-" * 50)
    
    # Check Users
    users = User.objects.all()
    print(f"\nUsers found: {users.count()}")
    for user in users:
        print(f"- {user.username} (Staff: {user.is_staff})")
    
    # Check Customers
    customers = Customer.objects.all()
    print(f"\nCustomers found: {customers.count()}")
    for customer in customers:
        print(f"- {customer.name} (Code: {customer.code})")
    
    # Check Categories
    categories = Category.objects.all()
    print(f"\nProduct Categories found: {categories.count()}")
    for category in categories:
        print(f"- {category.name}")
    
    # Check Products
    products = Product.objects.all()
    print(f"\nProducts found: {products.count()}")
    for product in products:
        print(f"- {product.name} (Code: {product.code}, Category: {product.category.name})")

if __name__ == '__main__':
    check_data()