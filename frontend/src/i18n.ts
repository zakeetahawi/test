import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import rtlPlugin from 'stylis-plugin-rtl';
import { prefixer } from 'stylis';
import createCache from '@emotion/cache';

// تهيئة التخزين المؤقت للـ RTL
export const cacheRtl = createCache({
  key: 'muirtl',
  stylisPlugins: [prefixer, rtlPlugin],
});

// ترجمات اللغة العربية
const resources = {
  ar: {
    translation: {
      // العامة
      loading: 'جاري التحميل...',
      error: 'حدث خطأ',
      save: 'حفظ',
      cancel: 'إلغاء',
      delete: 'حذف',
      edit: 'تعديل',
      add: 'إضافة',
      search: 'بحث',
      
      // المصادقة
      login: 'تسجيل الدخول',
      logout: 'تسجيل الخروج',
      username: 'اسم المستخدم',
      password: 'كلمة المرور',
      
      // القائمة الجانبية
      dashboard: 'لوحة التحكم',
      customers: 'العملاء',
      inventory: 'المخزون',
      orders: 'الطلبات',
      factory: 'المصنع',
      inspections: 'التفتيش',
      installations: 'التركيبات',
      reports: 'التقارير',
      settings: 'الإعدادات',
      
      // المخزون
      products: 'المنتجات',
      categories: 'الفئات',
      stock: 'المخزون',
      transactions: 'المعاملات',
      low_stock: 'مخزون منخفض',
      out_of_stock: 'نفذ من المخزون',
      total_value: 'القيمة الإجمالية',
      inventory: {
        utilized: 'مستخدم',
        low_stock_warning: 'تحذير: المخزون منخفض',
        items_count: 'عدد العناصر',
        total_value: 'القيمة الإجمالية',
        title: 'نظام المخزون',
        search: 'بحث عن منتج...',
        add_product: 'إضافة منتج جديد',
        edit_product: 'تعديل منتج',
        delete_product: 'حذف المنتج',
        delete_product_confirm: 'هل أنت متأكد من حذف هذا المنتج؟ لا يمكن التراجع عن هذا الإجراء.',
        
        // حقول المنتج
        code: 'رمز المنتج',
        name: 'اسم المنتج',
        description: 'وصف المنتج',
        category: 'الفئة',
        unit: 'وحدة القياس',
        price: 'السعر',
        stock: 'المخزون',
        min_stock: 'الحد الأدنى للمخزون',
        max_stock: 'الحد الأقصى للمخزون',
        current_stock: 'المخزون الحالي',
        status: 'الحالة',
        
        // القوائم المنسدلة
        all_categories: 'جميع الفئات',
        all_stock: 'جميع المنتجات',
        low_stock: 'مخزون منخفض',
        out_of_stock: 'نفذ من المخزون',
        
        // حالة المنتج
        status: {
          active: 'نشط',
          inactive: 'غير نشط'
        },
        
        // المعاملات
        transactions_title: 'معاملات المنتج: {product}',
        add_transaction: 'إضافة معاملة',
        transaction_type: 'نوع المعاملة',
        transaction_date: 'تاريخ المعاملة',
        reference: 'المرجع',
        quantity: 'الكمية',
        notes: 'ملاحظات',
        created_by: 'تم بواسطة',
        
        transaction_type: {
          in: 'إضافة للمخزون',
          out: 'سحب من المخزون'
        },
        
        // الإحصائيات
        total_products: 'إجمالي المنتجات',
        low_stock_products: 'منتجات منخفضة المخزون',
        out_of_stock_products: 'منتجات نفذت من المخزون',
        total_value: 'القيمة الإجمالية',
        
        // الفئات
        categories: 'فئات المخزون',
        category_name: 'اسم الفئة',
        category_description: 'وصف الفئة',
        add_category: 'إضافة فئة جديدة',
        edit_category: 'تعديل الفئة',
        delete_category: 'حذف الفئة',
        delete_category_confirm: 'هل أنت متأكد من حذف هذه الفئة؟ لا يمكنك حذف فئة تحتوي على منتجات.',
        no_description: 'لا يوجد وصف',
        products_count: '{{count}} منتج',
        
        // تفاصيل المنتج
        product_details: 'تفاصيل المنتج',
        view_transactions: 'عرض المعاملات',
        stock_limits: 'حدود المخزون',
        reorder_point: 'نقطة إعادة الطلب',
        stock_value: 'قيمة المخزون',
        
        // سجل المعاملات
        transactions: 'سجل المعاملات',
        search_transactions: 'بحث في المعاملات...',
        export_transactions: 'تصدير المعاملات',
        all_products: 'جميع المنتجات',
        all_transactions: 'جميع المعاملات',
        
        // رسائل النجاح
        success: {
          product_created: 'تم إضافة المنتج بنجاح',
          product_updated: 'تم تحديث المنتج بنجاح',
          product_deleted: 'تم حذف المنتج بنجاح',
          transaction_added: 'تم إضافة المعاملة بنجاح',
          category_created: 'تم إضافة الفئة بنجاح',
          category_updated: 'تم تحديث الفئة بنجاح',
          category_deleted: 'تم حذف الفئة بنجاح',
          export_complete: 'تم تصدير المعاملات بنجاح'
        },
        
        // رسائل الخطأ
        error: {
          create_product: 'حدث خطأ أثناء إضافة المنتج',
          update_product: 'حدث خطأ أثناء تحديث المنتج',
          delete_product: 'حدث خطأ أثناء حذف المنتج',
          add_transaction: 'حدث خطأ أثناء إضافة المعاملة',
          create_category: 'حدث خطأ أثناء إضافة الفئة',
          update_category: 'حدث خطأ أثناء تحديث الفئة',
          delete_category: 'حدث خطأ أثناء حذف الفئة',
          export_failed: 'حدث خطأ أثناء تصدير المعاملات',
          product_not_found: 'لم يتم العثور على المنتج'
        }
      },
      
      // لوحة التحكم
      dashboard: {
        title: 'لوحة التحكم',
        total_customers: 'إجمالي العملاء',
        total_orders: 'إجمالي الطلبات',
        inventory_value: 'قيمة المخزون',
        monthly_revenue: 'الإيرادات الشهرية',
        recent_orders: 'آخر الطلبات',
        recent_activities: 'النشاطات الأخيرة',
        inventory_status: 'حالة المخزون',
        tasks: 'المهام',
        activity: {
          new_customer: 'تم إضافة عميل جديد',
          new_order: 'طلب جديد تم استلامه',
          low_stock: 'تحذير: مخزون منخفض',
          production_complete: 'اكتملت عملية الإنتاج'
        }
      },
      
      // الطلبات
      orders: {
        id: 'رقم الطلب',
        customer: 'العميل',
        amount: 'المبلغ',
        status: {
          pending: 'قيد الانتظار',
          processing: 'قيد التنفيذ',
          completed: 'مكتمل',
          cancelled: 'ملغي'
        },
        date: 'التاريخ'
      },

      // المهام
      tasks: {
        priority: {
          high: 'عالية',
          medium: 'متوسطة',
          low: 'منخفضة'
        },
        due_date: 'تاريخ الاستحقاق',
        completed: 'مكتملة',
        add_task: 'إضافة مهمة'
      },

      // نظام إدارة العملاء
      customers: {
        title: 'إدارة العملاء',
        search: 'بحث عن عميل...',
        add: 'إضافة عميل جديد',
        add_title: 'إضافة عميل جديد',
        edit_title: 'تعديل بيانات العميل',
        delete_title: 'حذف العميل',
        delete_message: 'هل أنت متأكد من حذف هذا العميل؟ لا يمكن التراجع عن هذا الإجراء.',
        
        // حقول العميل
        firstName: 'الاسم الأول',
        lastName: 'الاسم الأخير',
        email: 'البريد الإلكتروني',
        phone: 'رقم الهاتف',
        address: 'العنوان',
        city: 'المدينة',
        country: 'البلد',
        company: 'اسم الشركة',
        notes: 'ملاحظات',
        type: 'نوع العميل',
        status: 'الحالة',
        created_at: 'تاريخ الإنشاء',
        updated_at: 'تاريخ التحديث',
        
        // أنواع العميل
        type: {
          individual: 'فرد',
          company: 'شركة'
        },
        
        // حالات العميل
        status: {
          active: 'نشط',
          inactive: 'غير نشط'
        },
        
        // أقسام التفاصيل
        contact_info: 'معلومات الاتصال',
        address_info: 'معلومات العنوان',
        company_info: 'معلومات الشركة',
        system_info: 'معلومات النظام',
        
        // رسائل النجاح
        success: {
          created: 'تم إضافة العميل بنجاح',
          updated: 'تم تحديث بيانات العميل بنجاح',
          deleted: 'تم حذف العميل بنجاح'
        },
        
        // رسائل الخطأ
        error: {
          loading: 'حدث خطأ أثناء تحميل بيانات العملاء',
          create: 'حدث خطأ أثناء إضافة العميل',
          update: 'حدث خطأ أثناء تحديث بيانات العميل',
          delete: 'حدث خطأ أثناء حذف العميل'
        }
      },

      // رسائل
      invalid_credentials: 'اسم المستخدم أو كلمة المرور غير صحيحة',
      logout_success: 'تم تسجيل الخروج بنجاح',
      save_success: 'تم الحفظ بنجاح',
      delete_success: 'تم الحذف بنجاح',
      delete_confirm: 'هل أنت متأكد من الحذف؟',
      
      // رسائل الخطأ
      error: {
        loading_dashboard: 'حدث خطأ أثناء تحميل لوحة التحكم',
        loading_orders: 'حدث خطأ أثناء تحميل الطلبات',
        loading_inventory: 'حدث خطأ أثناء تحميل بيانات المخزون',
        loading_tasks: 'حدث خطأ أثناء تحميل المهام'
      },

      // ترجمات الجدول
      table: {
        rows_per_page: 'عدد الصفوف في الصفحة'
      }
    },
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'ar', // اللغة الافتراضية
    fallbackLng: 'ar',
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
  });

export default i18n;