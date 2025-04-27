from inventory.models import StockTransaction, StockTransactionReason, InventoryAdjustment, ProductBatch, StockAlert

StockTransaction.objects.all().delete()
StockTransactionReason.objects.all().delete()
InventoryAdjustment.objects.all().delete()
ProductBatch.objects.all().delete()
StockAlert.objects.all().delete()

print("تم مسح بيانات المخزون بالكامل.")
