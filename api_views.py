from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model

from customers.models import Customer, CustomerCategory
from orders.models import Order
from inventory.models import Product, Category as ProductCategory, StockTransaction as StockMovement, Supplier, WarehouseLocation as Location
from inspections.models import Inspection
from installations.models import Installation
from accounts.models import Branch

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    API endpoint for dashboard stats in the format expected by the React frontend
    """
    try:
        # Get basic stats
        total_customers = Customer.objects.count()
        total_orders = Order.objects.count()

        # Calculate total revenue
        total_revenue = Order.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # Get pending installations
        pending_installations = Installation.objects.filter(
            status='pending'
        ).count()

        # Get inventory value - using a fixed value since current_stock field doesn't exist
        inventory_value = 0  # Fixed value since we can't calculate it without current_stock field

        # Count products with stock below minimum level - using a fixed value since current_stock field doesn't exist
        low_stock_items = 0  # Fixed value since we can't filter without current_stock field

        # Get pending inspections
        pending_inspections = Inspection.objects.filter(
            status='pending'
        ).count()

        # Generate monthly revenue data for the chart
        months_ar = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

        current_year = timezone.now().year
        previous_year = current_year - 1

        # Initialize revenue trends data
        revenue_trends = {
            'labels': months_ar,
            'data': [0] * 12,  # Current year data
            'previousPeriodData': [0] * 12  # Previous year data
        }

        # Initialize customer trends data
        customer_trends = {
            'labels': months_ar,
            'data': [0] * 12,  # Current year data
            'previousPeriodData': [0] * 12  # Previous year data
        }

        # Initialize order status distribution
        order_status_distribution = {
            'labels': ['قيد المعالجة', 'مكتملة', 'ملغاة', 'قيد التسليم'],
            'data': [0, 0, 0, 0]
        }

        # Get order status counts
        status_counts = Order.objects.values('status').annotate(count=Count('id'))
        status_map = {
            'pending': 0,  # قيد المعالجة
            'completed': 1,  # مكتملة
            'cancelled': 2,  # ملغاة
            'shipping': 3   # قيد التسليم
        }

        for status_item in status_counts:
            status = status_item['status']
            if status in status_map:
                order_status_distribution['data'][status_map[status]] = status_item['count']

        # Fill in revenue data for current and previous year
        for month in range(1, 13):
            # Current year revenue
            current_month_revenue = Order.objects.filter(
                created_at__year=current_year,
                created_at__month=month
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            revenue_trends['data'][month-1] = float(current_month_revenue)

            # Previous year revenue
            previous_month_revenue = Order.objects.filter(
                created_at__year=previous_year,
                created_at__month=month
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            revenue_trends['previousPeriodData'][month-1] = float(previous_month_revenue)

            # Current year new customers
            current_month_customers = Customer.objects.filter(
                created_at__year=current_year,
                created_at__month=month
            ).count()

            customer_trends['data'][month-1] = current_month_customers

            # Previous year new customers
            previous_month_customers = Customer.objects.filter(
                created_at__year=previous_year,
                created_at__month=month
            ).count()

            customer_trends['previousPeriodData'][month-1] = previous_month_customers

        # Get recent activities (last 10)
        recent_activities = []

        # Add recent orders to activities
        recent_orders = Order.objects.order_by('-created_at')[:5]
        for order in recent_orders:
            recent_activities.append({
                'id': len(recent_activities) + 1,
                'type': 'order',
                'description': f'تم إنشاء طلب جديد #{order.id}',
                'timestamp': order.created_at.isoformat(),
                'user': order.created_by.get_full_name() if order.created_by else 'النظام',
                'entityId': order.id
            })

        # Add recent customers to activities
        recent_customers = Customer.objects.order_by('-created_at')[:3]
        for customer in recent_customers:
            recent_activities.append({
                'id': len(recent_activities) + 1,
                'type': 'customer',
                'description': f'تم إضافة عميل جديد: {customer.name}',
                'timestamp': customer.created_at.isoformat(),
                'user': customer.created_by.get_full_name() if hasattr(customer, 'created_by') and customer.created_by else 'النظام',
                'entityId': customer.id
            })

        # Add recent inspections to activities
        recent_inspections = Inspection.objects.order_by('-created_at')[:2]
        for inspection in recent_inspections:
            recent_activities.append({
                'id': len(recent_activities) + 1,
                'type': 'inspection',
                'description': f'تم جدولة معاينة جديدة #{inspection.id}',
                'timestamp': inspection.created_at.isoformat(),
                'user': inspection.created_by.get_full_name() if hasattr(inspection, 'created_by') and inspection.created_by else 'النظام',
                'entityId': inspection.id
            })

        # Sort activities by timestamp
        recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:10]

        # Get recent orders for display
        recent_orders_data = []
        for order in Order.objects.order_by('-created_at')[:5]:
            recent_orders_data.append({
                'id': order.id,
                'customer': order.customer.name if order.customer else 'عميل غير معروف',
                'amount': float(order.total_amount),
                'status': order.status,
                'date': order.created_at.isoformat()
            })

        # Get active tasks
        active_tasks = []
        # Use default tasks as there's no Task model
        print("Using default tasks as Task model doesn't exist")
        # Add some default tasks as fallback
        active_tasks = [
            {
                'id': 1,
                'title': 'متابعة طلب العميل رقم 123',
                'dueDate': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
                'priority': 'high',
                'status': 'pending',
                'assignedTo': 'أحمد محمد'
            },
            {
                'id': 2,
                'title': 'تحديث قائمة المنتجات',
                'dueDate': (timezone.now() + timezone.timedelta(days=2)).isoformat(),
                'priority': 'medium',
                'status': 'in_progress',
                'assignedTo': 'محمد علي'
            }
        ]

        # Prepare complete response data
        response_data = {
            'totalCustomers': total_customers,
            'totalOrders': total_orders,
            'totalRevenue': float(total_revenue),
            'pendingInstallations': pending_installations,
            'lowStockItems': low_stock_items,
            'pendingInspections': pending_inspections,
            'revenueTrends': revenue_trends,
            'customerTrends': customer_trends,
            'orderStatusDistribution': order_status_distribution,
            'recentActivities': recent_activities,
            'recentOrders': recent_orders_data,
            'activeTasks': active_tasks
        }

        return Response(response_data)

    except Exception as e:
        import traceback
        print(f"Error in dashboard_stats: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inspection_list(request):
    """
    API endpoint for listing inspections with filtering and pagination
    """
    try:
        # Get query parameters
        search = request.query_params.get('search', '')
        status = request.query_params.get('status', '')
        branch_id = request.query_params.get('branch', '')
        from_orders = request.query_params.get('from_orders', None)

        # Start with all inspections
        inspections = Inspection.objects.all().order_by('-request_date')

        # Apply filters
        if search:
            inspections = inspections.filter(
                Q(contract_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(notes__icontains=search)
            )

        if status:
            inspections = inspections.filter(status=status)

        if branch_id and branch_id.isdigit():
            inspections = inspections.filter(branch_id=int(branch_id))

        if from_orders is not None:
            is_from_orders = from_orders.lower() == 'true'
            inspections = inspections.filter(is_from_orders=is_from_orders)

        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 10))
        paginated_inspections = paginator.paginate_queryset(inspections, request)

        # Prepare response data
        results = []
        for inspection in paginated_inspections:
            # Get customer data
            customer_data = {
                'id': inspection.customer.id,
                'name': inspection.customer.name
            } if inspection.customer else None

            # Get branch data
            branch_data = {
                'id': inspection.branch.id,
                'name': inspection.branch.name
            } if inspection.branch else None

            # Get inspector data
            inspector_data = {
                'id': inspection.inspector.id,
                'name': inspection.inspector.get_full_name()
            } if inspection.inspector else None

            # Get responsible employee data
            responsible_employee_data = {
                'id': inspection.responsible_employee.id,
                'name': inspection.responsible_employee.name if hasattr(inspection.responsible_employee, 'name') else str(inspection.responsible_employee)
            } if inspection.responsible_employee else None

            # Get created by data
            created_by_data = {
                'id': inspection.created_by.id,
                'name': inspection.created_by.get_full_name()
            } if inspection.created_by else None

            # Get order data
            order_data = {
                'id': inspection.order.id,
                'code': inspection.order.code
            } if inspection.order else None

            # Format inspection data
            inspection_data = {
                'id': inspection.id,
                'contract_number': inspection.contract_number,
                'customer': customer_data,
                'branch': branch_data,
                'inspector': inspector_data,
                'responsible_employee': responsible_employee_data,
                'is_from_orders': inspection.is_from_orders,
                'windows_count': inspection.windows_count,
                'inspection_file': request.build_absolute_uri(inspection.inspection_file.url) if inspection.inspection_file else None,
                'request_date': inspection.request_date.isoformat() if inspection.request_date else None,
                'scheduled_date': inspection.scheduled_date.isoformat() if inspection.scheduled_date else None,
                'status': inspection.status,
                'result': inspection.result,
                'notes': inspection.notes,
                'order_notes': inspection.order_notes,
                'created_by': created_by_data,
                'order': order_data,
                'created_at': inspection.created_at.isoformat() if inspection.created_at else None,
                'updated_at': inspection.updated_at.isoformat() if inspection.updated_at else None,
                'completed_at': inspection.completed_at.isoformat() if inspection.completed_at else None
            }
            results.append(inspection_data)

        # Return paginated response
        return paginator.get_paginated_response(results)

    except Exception as e:
        import traceback
        print(f"Error in inspection_list: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inspection_detail(request, pk):
    """
    API endpoint for retrieving a single inspection
    """
    try:
        inspection = Inspection.objects.get(pk=pk)

        # Get customer data
        customer_data = {
            'id': inspection.customer.id,
            'name': inspection.customer.name
        } if inspection.customer else None

        # Get branch data
        branch_data = {
            'id': inspection.branch.id,
            'name': inspection.branch.name
        } if inspection.branch else None

        # Get inspector data
        inspector_data = {
            'id': inspection.inspector.id,
            'name': inspection.inspector.get_full_name()
        } if inspection.inspector else None

        # Get responsible employee data
        responsible_employee_data = {
            'id': inspection.responsible_employee.id,
            'name': inspection.responsible_employee.name if hasattr(inspection.responsible_employee, 'name') else str(inspection.responsible_employee)
        } if inspection.responsible_employee else None

        # Get created by data
        created_by_data = {
            'id': inspection.created_by.id,
            'name': inspection.created_by.get_full_name()
        } if inspection.created_by else None

        # Get order data
        order_data = {
            'id': inspection.order.id,
            'code': inspection.order.code
        } if inspection.order else None

        # Format inspection data
        inspection_data = {
            'id': inspection.id,
            'contract_number': inspection.contract_number,
            'customer': customer_data,
            'branch': branch_data,
            'inspector': inspector_data,
            'responsible_employee': responsible_employee_data,
            'is_from_orders': inspection.is_from_orders,
            'windows_count': inspection.windows_count,
            'inspection_file': request.build_absolute_uri(inspection.inspection_file.url) if inspection.inspection_file else None,
            'request_date': inspection.request_date.isoformat() if inspection.request_date else None,
            'scheduled_date': inspection.scheduled_date.isoformat() if inspection.scheduled_date else None,
            'status': inspection.status,
            'result': inspection.result,
            'notes': inspection.notes,
            'order_notes': inspection.order_notes,
            'created_by': created_by_data,
            'order': order_data,
            'created_at': inspection.created_at.isoformat() if inspection.created_at else None,
            'updated_at': inspection.updated_at.isoformat() if inspection.updated_at else None,
            'completed_at': inspection.completed_at.isoformat() if inspection.completed_at else None
        }

        return Response(inspection_data)

    except Inspection.DoesNotExist:
        return Response({'error': 'المعاينة غير موجودة'}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in inspection_detail: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inspection_stats(request):
    """
    API endpoint for retrieving inspection statistics
    """
    try:
        today = timezone.now().date()

        # Get basic stats
        total = Inspection.objects.count()
        pending = Inspection.objects.filter(status='pending').count()
        scheduled = Inspection.objects.filter(status='scheduled').count()
        completed = Inspection.objects.filter(status='completed').count()
        cancelled = Inspection.objects.filter(status='cancelled').count()

        # Get today's inspections
        today_count = Inspection.objects.filter(scheduled_date=today).count()

        # Get this week's inspections
        week_start = today - timezone.timedelta(days=today.weekday())
        week_end = week_start + timezone.timedelta(days=6)
        this_week = Inspection.objects.filter(scheduled_date__range=[week_start, week_end]).count()

        # Get this month's inspections
        month_start = today.replace(day=1)
        next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
        month_end = next_month - timezone.timedelta(days=1)
        this_month = Inspection.objects.filter(scheduled_date__range=[month_start, month_end]).count()

        # Prepare response data
        stats = {
            'total': total,
            'pending': pending,
            'scheduled': scheduled,
            'completed': completed,
            'cancelled': cancelled,
            'today': today_count,
            'this_week': this_week,
            'this_month': this_month
        }

        return Response(stats)

    except Exception as e:
        import traceback
        print(f"Error in inspection_stats: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

class CustomerPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_list(request):
    """
    API endpoint for listing customers with filtering and pagination
    """
    try:
        # Get query parameters
        search = request.query_params.get('search', '')
        customer_type = request.query_params.get('customer_type', '')
        status = request.query_params.get('status', '')
        category_id = request.query_params.get('category_id', '')

        # Start with all customers
        customers = Customer.objects.all().order_by('-created_at')

        # Apply filters
        if search:
            customers = customers.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(code__icontains=search)
            )

        if customer_type:
            customers = customers.filter(customer_type=customer_type)

        if status:
            customers = customers.filter(status=status)

        if category_id and category_id.isdigit():
            customers = customers.filter(category_id=int(category_id))

        # Apply pagination
        paginator = CustomerPagination()
        paginated_customers = paginator.paginate_queryset(customers, request)

        # Prepare response data
        results = []
        for customer in paginated_customers:
            # Get branch name if available
            branch_name = customer.branch.name if hasattr(customer, 'branch') and customer.branch else 'غير محدد'

            # Get category name if available
            category_name = customer.category.name if hasattr(customer, 'category') and customer.category else 'غير محدد'

            # Format customer data
            customer_data = {
                'id': customer.id,
                'code': customer.code,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email,
                'address': customer.address,
                'customer_type': customer.customer_type,
                'status': customer.status,
                'notes': customer.notes,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'branch': {
                    'id': customer.branch.id if hasattr(customer, 'branch') and customer.branch else None,
                    'name': branch_name
                },
                'category': {
                    'id': customer.category.id if hasattr(customer, 'category') and customer.category else None,
                    'name': category_name
                },
                'image': request.build_absolute_uri(customer.image.url) if customer.image else None
            }
            results.append(customer_data)

        # Return paginated response
        return paginator.get_paginated_response(results)

    except Exception as e:
        import traceback
        print(f"Error in customer_list: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_detail(request, pk):
    """
    API endpoint for retrieving a single customer
    """
    try:
        customer = Customer.objects.get(pk=pk)

        # Get branch name if available
        branch_name = customer.branch.name if hasattr(customer, 'branch') and customer.branch else 'غير محدد'

        # Get category name if available
        category_name = customer.category.name if hasattr(customer, 'category') and customer.category else 'غير محدد'

        # Format customer data
        customer_data = {
            'id': customer.id,
            'code': customer.code,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'address': customer.address,
            'customer_type': customer.customer_type,
            'status': customer.status,
            'notes': customer.notes,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'branch': {
                'id': customer.branch.id if hasattr(customer, 'branch') and customer.branch else None,
                'name': branch_name
            },
            'category': {
                'id': customer.category.id if hasattr(customer, 'category') and customer.category else None,
                'name': category_name
            },
            'image': request.build_absolute_uri(customer.image.url) if customer.image else None
        }

        return Response(customer_data)

    except Customer.DoesNotExist:
        return Response({'error': 'العميل غير موجود'}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in customer_detail: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_categories(request):
    """
    API endpoint for retrieving customer categories
    """
    try:
        categories = CustomerCategory.objects.all()

        # Format category data
        results = []
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description if hasattr(category, 'description') else ''
            }
            results.append(category_data)

        return Response(results)

    except Exception as e:
        import traceback
        print(f"Error in customer_categories: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_products(request):
    """
    API endpoint for listing products with filtering and pagination
    """
    try:
        # Get query parameters
        search = request.query_params.get('search', '')
        category_id = request.query_params.get('category_id', '')
        status = request.query_params.get('status', '')
        min_price = request.query_params.get('min_price', '')
        max_price = request.query_params.get('max_price', '')
        in_stock = request.query_params.get('in_stock', None)
        is_featured = request.query_params.get('is_featured', None)
        supplier_id = request.query_params.get('supplier_id', '')
        location_id = request.query_params.get('location_id', '')
        sort_by = request.query_params.get('sort_by', 'id')
        sort_order = request.query_params.get('sort_order', 'desc')

        # Start with all products
        products = Product.objects.all()

        # Apply filters
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search) |
                Q(barcode__icontains=search)
            )

        if category_id and category_id.isdigit():
            products = products.filter(category_id=int(category_id))

        if status:
            products = products.filter(status=status)

        if min_price and min_price.isdigit():
            products = products.filter(price__gte=float(min_price))

        if max_price and max_price.isdigit():
            products = products.filter(price__lte=float(max_price))

        if in_stock is not None:
            is_in_stock = in_stock.lower() == 'true'
            if is_in_stock:
                products = products.filter(current_stock__gt=0)

        if is_featured is not None:
            is_featured_bool = is_featured.lower() == 'true'
            products = products.filter(is_featured=is_featured_bool)

        if supplier_id and supplier_id.isdigit():
            products = products.filter(supplier_id=int(supplier_id))

        if location_id and location_id.isdigit():
            products = products.filter(location_id=int(location_id))

        # Apply sorting
        order_by = f"{'-' if sort_order == 'desc' else ''}{sort_by}"
        products = products.order_by(order_by)

        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 10))
        paginated_products = paginator.paginate_queryset(products, request)

        # Prepare response data
        results = []
        for product in paginated_products:
            # Get category data
            category_data = {
                'id': product.category.id,
                'name': product.category.name
            } if product.category else None

            # Get supplier data
            supplier_data = {
                'id': product.supplier.id,
                'name': product.supplier.name
            } if hasattr(product, 'supplier') and product.supplier else None

            # Get location data
            location_data = {
                'id': product.location.id,
                'name': product.location.name
            } if hasattr(product, 'location') and product.location else None

            # Get created by data
            created_by_data = {
                'id': product.created_by.id,
                'name': product.created_by.get_full_name()
            } if hasattr(product, 'created_by') and product.created_by else None

            # Format product data
            product_data = {
                'id': product.id,
                'code': product.code,
                'name': product.name,
                'description': product.description,
                'category': category_data,
                'price': float(product.price),
                'cost_price': float(product.cost_price) if hasattr(product, 'cost_price') else None,
                'current_stock': product.current_stock,
                'min_stock': product.min_stock,
                'max_stock': product.max_stock if hasattr(product, 'max_stock') else None,
                'unit': product.unit,
                'status': product.status,
                'image': request.build_absolute_uri(product.image.url) if product.image else None,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None,
                'created_by': created_by_data,
                'supplier': supplier_data,
                'location': location_data,
                'barcode': product.barcode if hasattr(product, 'barcode') else None,
                'weight': float(product.weight) if hasattr(product, 'weight') and product.weight else None,
                'dimensions': product.dimensions if hasattr(product, 'dimensions') else None,
                'is_featured': product.is_featured if hasattr(product, 'is_featured') else False,
                'tags': product.tags if hasattr(product, 'tags') else []
            }
            results.append(product_data)

        # Return paginated response
        return paginator.get_paginated_response(results)

    except Exception as e:
        import traceback
        print(f"Error in inventory_products: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_product_detail(request, pk):
    """
    API endpoint for retrieving a single product
    """
    try:
        product = Product.objects.get(pk=pk)

        # Get category data
        category_data = {
            'id': product.category.id,
            'name': product.category.name
        } if product.category else None

        # Get supplier data
        supplier_data = {
            'id': product.supplier.id,
            'name': product.supplier.name
        } if hasattr(product, 'supplier') and product.supplier else None

        # Get location data
        location_data = {
            'id': product.location.id,
            'name': product.location.name
        } if hasattr(product, 'location') and product.location else None

        # Get created by data
        created_by_data = {
            'id': product.created_by.id,
            'name': product.created_by.get_full_name()
        } if hasattr(product, 'created_by') and product.created_by else None

        # Format product data
        product_data = {
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'description': product.description,
            'category': category_data,
            'price': float(product.price),
            'cost_price': float(product.cost_price) if hasattr(product, 'cost_price') else None,
            'current_stock': product.current_stock,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock if hasattr(product, 'max_stock') else None,
            'unit': product.unit,
            'status': product.status,
            'image': request.build_absolute_uri(product.image.url) if product.image else None,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None,
            'created_by': created_by_data,
            'supplier': supplier_data,
            'location': location_data,
            'barcode': product.barcode if hasattr(product, 'barcode') else None,
            'weight': float(product.weight) if hasattr(product, 'weight') and product.weight else None,
            'dimensions': product.dimensions if hasattr(product, 'dimensions') else None,
            'is_featured': product.is_featured if hasattr(product, 'is_featured') else False,
            'tags': product.tags if hasattr(product, 'tags') else []
        }

        return Response(product_data)

    except Product.DoesNotExist:
        return Response({'error': 'المنتج غير موجود'}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in inventory_product_detail: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_categories(request):
    """
    API endpoint for retrieving product categories
    """
    try:
        categories = ProductCategory.objects.all()

        # Format category data
        results = []
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description if hasattr(category, 'description') else '',
                'parent_id': category.parent_id if hasattr(category, 'parent_id') else None,
                'image': request.build_absolute_uri(category.image.url) if hasattr(category, 'image') and category.image else None
            }
            results.append(category_data)

        return Response(results)

    except Exception as e:
        import traceback
        print(f"Error in inventory_categories: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_stats(request):
    """
    API endpoint for retrieving inventory statistics
    """
    try:
        # Get basic stats
        total_products = Product.objects.count()
        active_products = Product.objects.filter(status='active').count()

        # Get low stock products
        low_stock_products = Product.objects.filter(
            current_stock__lt=F('min_stock')
        ).count()

        # Get out of stock products
        out_of_stock_products = Product.objects.filter(
            current_stock=0
        ).count()

        # Get total inventory value
        total_value = Product.objects.aggregate(
            total=Sum(F('price') * F('current_stock'), default=0)
        )['total'] or 0

        # Get categories count
        categories_count = ProductCategory.objects.count()

        # Prepare response data
        stats = {
            'total_products': total_products,
            'active_products': active_products,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'total_value': float(total_value),
            'categories_count': categories_count
        }

        return Response(stats)

    except Exception as e:
        import traceback
        print(f"Error in inventory_stats: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_stock_movements(request):
    """
    API endpoint for retrieving all stock movements
    """
    try:
        # Get query parameters
        product_id = request.query_params.get('product_id')

        # Filter by product if provided
        if product_id and product_id.isdigit():
            movements = StockMovement.objects.filter(product_id=int(product_id))
        else:
            movements = StockMovement.objects.all()

        # Order by created_at descending
        movements = movements.order_by('-created_at')

        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 10))
        paginated_movements = paginator.paginate_queryset(movements, request)

        # Prepare response data
        results = []
        for movement in paginated_movements:
            # Format movement data
            movement_data = {
                'id': movement.id,
                'product': {
                    'id': movement.product.id,
                    'name': movement.product.name,
                    'code': movement.product.code
                },
                'quantity': movement.quantity,
                'type': movement.type,
                'reference': movement.reference,
                'notes': movement.notes,
                'created_at': movement.created_at.isoformat() if movement.created_at else None,
                'created_by': {
                    'id': movement.created_by.id,
                    'name': movement.created_by.get_full_name()
                } if movement.created_by else None
            }
            results.append(movement_data)

        # Return paginated response
        return paginator.get_paginated_response(results)

    except Exception as e:
        import traceback
        print(f"Error in inventory_stock_movements: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_product_stock_movements(request, product_id):
    """
    API endpoint for retrieving stock movements for a specific product
    """
    try:
        # Check if product exists
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'المنتج غير موجود'}, status=404)

        # Get stock movements for this product
        movements = StockMovement.objects.filter(product=product).order_by('-created_at')

        # Prepare response data
        results = []
        for movement in movements:
            # Format movement data
            movement_data = {
                'id': movement.id,
                'product': {
                    'id': movement.product.id,
                    'name': movement.product.name,
                    'code': movement.product.code
                },
                'quantity': movement.quantity,
                'type': movement.type,
                'reference': movement.reference,
                'notes': movement.notes,
                'created_at': movement.created_at.isoformat() if movement.created_at else None,
                'created_by': {
                    'id': movement.created_by.id,
                    'name': movement.created_by.get_full_name()
                } if movement.created_by else None
            }
            results.append(movement_data)

        return Response(results)

    except Exception as e:
        import traceback
        print(f"Error in inventory_product_stock_movements: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inventory_add_stock_movement(request):
    """
    API endpoint for adding a new stock movement
    """
    try:
        # Get request data
        data = request.data

        # Validate required fields
        if not data.get('product') or not isinstance(data.get('product'), dict) or not data['product'].get('id'):
            return Response({'error': 'معرف المنتج مطلوب'}, status=400)

        if not data.get('quantity') or not isinstance(data.get('quantity'), (int, float)) or data['quantity'] <= 0:
            return Response({'error': 'الكمية يجب أن تكون أكبر من صفر'}, status=400)

        if not data.get('type') or data['type'] not in ['in', 'out', 'adjustment']:
            return Response({'error': 'نوع الحركة غير صالح'}, status=400)

        if not data.get('reference'):
            return Response({'error': 'المرجع مطلوب'}, status=400)

        # Get product
        try:
            product = Product.objects.get(pk=data['product']['id'])
        except Product.DoesNotExist:
            return Response({'error': 'المنتج غير موجود'}, status=404)

        # Check if there's enough stock for 'out' movements
        if data['type'] == 'out' and product.current_stock < data['quantity']:
            return Response({'error': f'الكمية المتاحة في المخزون هي {product.current_stock} فقط'}, status=400)

        # Create stock movement
        movement = StockMovement.objects.create(
            product=product,
            quantity=data['quantity'],
            type=data['type'],
            reference=data['reference'],
            notes=data.get('notes', ''),
            created_by=request.user
        )

        # Update product stock
        if data['type'] == 'in':
            product.current_stock += data['quantity']
        elif data['type'] == 'out':
            product.current_stock -= data['quantity']
        elif data['type'] == 'adjustment':
            product.current_stock = data['quantity']

        product.save()

        # Format response data
        response_data = {
            'id': movement.id,
            'product': {
                'id': product.id,
                'name': product.name,
                'code': product.code
            },
            'quantity': movement.quantity,
            'type': movement.type,
            'reference': movement.reference,
            'notes': movement.notes,
            'created_at': movement.created_at.isoformat() if movement.created_at else None,
            'created_by': {
                'id': request.user.id,
                'name': request.user.get_full_name()
            }
        }

        return Response(response_data, status=201)

    except Exception as e:
        import traceback
        print(f"Error in inventory_add_stock_movement: {e}")
        print(traceback.format_exc())
        return Response(
            {'error': str(e)},
            status=500
        )