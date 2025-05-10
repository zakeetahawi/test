export const formatDate = (date: Date | string | null): string => {
  if (!date) return '';
  
  if (typeof date === 'string') {
    // إذا كان التاريخ سلسلة نصية، نقوم بتقسيمها عند T ونأخذ الجزء الأول (التاريخ فقط)
    return date.split('T')[0];
  }
  
  // إذا كان التاريخ كائن Date، نستخدم toISOString
  return date.toISOString().split('T')[0];
};