const monthNames = [
  'يناير',
  'فبراير',
  'مارس',
  'أبريل',
  'مايو',
  'يونيو',
  'يوليو',
  'أغسطس',
  'سبتمبر',
  'أكتوبر',
  'نوفمبر',
  'ديسمبر',
];

export const generateMockSalesData = (months = 6) => {
  const currentDate = new Date();
  const data = [];
  
  for (let i = months - 1; i >= 0; i--) {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
    const baseAmount = 15000; // Base sales amount
    const randomVariation = Math.random() * 10000 - 5000; // Random variation between -5000 and +5000
    
    data.push({
      month: monthNames[date.getMonth()],
      amount: Math.max(0, Math.round(baseAmount + randomVariation + (i * 1000))), // Slight upward trend
    });
  }
  
  return data;
};

export const generateMockOrderDistribution = () => {
  return [
    { name: 'ستائر', value: Math.round(30 + Math.random() * 20) }, // 30-50%
    { name: 'أقمشة', value: Math.round(20 + Math.random() * 15) }, // 20-35%
    { name: 'تركيبات', value: Math.round(15 + Math.random() * 10) }, // 15-25%
    { name: 'ديكورات', value: Math.round(10 + Math.random() * 10) }, // 10-20%
  ];
};

// Function to generate random activity data
interface Activity {
  id: number;
  type: 'create' | 'update' | 'complete' | 'schedule';
  title: string;
  description: string;
  timestamp: string;
  user: string;
}

const users = [
  'أحمد محمد',
  'سارة أحمد',
  'علي حسن',
  'ليلى عمر',
  'عمر خالد',
];

const activityTypes: Array<{
  type: Activity['type'];
  titles: string[];
  descriptions: string[];
}> = [
  {
    type: 'create',
    titles: ['طلب جديد', 'عميل جديد'],
    descriptions: [
      'تم إنشاء طلب جديد رقم #%n',
      'تم إضافة عميل جديد: شركة %s للمقاولات',
    ],
  },
  {
    type: 'update',
    titles: ['تحديث طلب', 'تعديل بيانات'],
    descriptions: [
      'تم تحديث تفاصيل الطلب #%n',
      'تم تعديل بيانات العميل %s',
    ],
  },
  {
    type: 'complete',
    titles: ['تركيب منتهي', 'طلب مكتمل'],
    descriptions: [
      'تم الانتهاء من تركيب الطلب #%n',
      'تم اكتمال الطلب #%n بنجاح',
    ],
  },
  {
    type: 'schedule',
    titles: ['موعد معاينة', 'موعد تركيب'],
    descriptions: [
      'تم جدولة معاينة للعميل %s',
      'تم تحديد موعد تركيب للطلب #%n',
    ],
  },
];

const companyNames = [
  'النور',
  'الفجر',
  'المستقبل',
  'الأمل',
  'التقدم',
  'الريادة',
  'النهضة',
  'الإعمار',
];

export const generateMockActivities = (count = 5): Activity[] => {
  return Array.from({ length: count }, (_, index) => {
    const type = activityTypes[Math.floor(Math.random() * activityTypes.length)];
    const titleIndex = Math.floor(Math.random() * type.titles.length);
    const descIndex = Math.floor(Math.random() * type.descriptions.length);
    const orderNum = Math.floor(10000 + Math.random() * 90000);
    const companyName = companyNames[Math.floor(Math.random() * companyNames.length)];
    
    const description = type.descriptions[descIndex]
      .replace('%n', orderNum.toString())
      .replace('%s', companyName);

    return {
      id: index + 1,
      type: type.type,
      title: type.titles[titleIndex],
      description,
      timestamp: new Date(Date.now() - Math.floor(Math.random() * 24 * 60 * 60 * 1000)).toISOString(),
      user: users[Math.floor(Math.random() * users.length)],
    };
  }).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
};
