import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from ..models import BackupMetrics, BackupHistory
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

class BackupAnalyticsService:
    """خدمة تحليلات النسخ الاحتياطي"""

    @staticmethod
    def generate_daily_report(days=30):
        """توليد التقرير اليومي"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = BackupMetrics.objects.filter(
            backup_date__range=(start_date, end_date)
        )
        
        # إحصائيات النجاح والفشل
        success_fail_data = metrics.values('backup_date__date').annotate(
            success=Count('id', filter=Q(successful=True)),
            failed=Count('id', filter=Q(successful=False))
        ).order_by('backup_date__date')
        
        # حجم البيانات اليومي
        size_data = metrics.values('backup_date__date').annotate(
            total_size=Sum('backup_size')
        ).order_by('backup_date__date')
        
        # إنشاء الرسوم البيانية
        x_dates = [str(d['backup_date__date']) for d in success_fail_data] if success_fail_data else []
        success_values = [d['success'] for d in success_fail_data] if success_fail_data else []
        failed_values = [d['failed'] for d in success_fail_data] if success_fail_data else []
        
        # Crear figura completa de éxito/fracaso
        success_fail_fig = go.Figure()
        success_fail_fig.add_trace(go.Bar(
            name='نجاح',
            x=x_dates,
            y=success_values,
            marker_color='green'
        ))
        success_fail_fig.add_trace(go.Bar(
            name='فشل',
            x=x_dates,
            y=failed_values,
            marker_color='red'
        ))
        success_fail_fig.update_layout(
            title='نجاح وفشل النسخ الاحتياطي',
            barmode='stack',
            xaxis_title='التاريخ',
            yaxis_title='عدد النسخ'
        )
        
        # Crear figura completa para el tamaño
        size_x_dates = [str(d['backup_date__date']) for d in size_data] if size_data else []
        size_values = [d['total_size'] / (1024 * 1024) for d in size_data] if size_data else []
        
        size_fig = go.Figure()
        size_fig.add_trace(go.Scatter(
            x=size_x_dates,
            y=size_values,
            mode='lines+markers'
        ))
        size_fig.update_layout(
            title='حجم النسخ الاحتياطي (ميجابايت)',
            xaxis_title='التاريخ',
            yaxis_title='الحجم (ميجابايت)'
        )
        
        return {
            'charts': {
                'success_failure': json.dumps(success_fail_fig.to_dict(), cls=PlotlyJSONEncoder),
                'size': json.dumps(size_fig.to_dict(), cls=PlotlyJSONEncoder)
            },
            'metrics': {
                'total_backups': metrics.count(),
                'success_rate': (metrics.filter(successful=True).count() / metrics.count() * 100) if metrics.exists() else 0,
                'average_duration': metrics.filter(successful=True).aggregate(avg=Avg('duration'))['avg'] or 0,
                'total_size_gb': metrics.aggregate(total=Sum('backup_size'))['total'] / (1024 * 1024 * 1024) if metrics.exists() else 0
            }
        }

    @staticmethod
    def generate_storage_report():
        """توليد تقرير التخزين"""
        last_backup = BackupHistory.objects.order_by('-timestamp').first()
        total_backups = BackupHistory.objects.count()
        total_size = BackupMetrics.objects.aggregate(total=Sum('backup_size'))['total'] or 0
        
        # تحليل حسب نوع التخزين
        storage_distribution = BackupMetrics.objects.values('storage_type').annotate(
            count=Count('id'),
            total_size=Sum('backup_size')
        )
        
        # إنشاء مخطط دائري لتوزيع التخزين
        labels = [d['storage_type'] for d in storage_distribution] if storage_distribution else []
        values = [d['count'] for d in storage_distribution] if storage_distribution else []
        
        storage_fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        storage_fig.update_layout(title='توزيع النسخ حسب نوع التخزين')
        
        return {
            'last_backup': last_backup,
            'total_backups': total_backups,
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'storage_distribution': storage_distribution,
            'charts': {
                'storage_pie': json.dumps(storage_fig.to_dict(), cls=PlotlyJSONEncoder)
            }
        }
        
    @staticmethod
    def generate_performance_metrics(days=7):
        """توليد مقاييس الأداء"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = BackupMetrics.objects.filter(
            backup_date__range=(start_date, end_date)
        )
        
        success_rate = (metrics.filter(successful=True).count() / metrics.count() * 100) if metrics.exists() else 0
        avg_backup_time = metrics.filter(successful=True).aggregate(avg=Avg('duration'))['avg'] or 0
        
        return {
            'success_rate': success_rate,
            'avg_backup_time': avg_backup_time,
            'total_backups': metrics.count(),
            'period_days': days
        }