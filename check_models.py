#!/usr/bin/env python
"""
سكريبت لفحص النماذج التي ليس لها ارتباطات
"""
import os
import sys
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.apps import apps
from django.db.models import ForeignKey, ManyToManyField, OneToOneField
from django.db.models.fields.related import RelatedField

def check_models():
    """فحص النماذج التي ليس لها ارتباطات"""
    print("فحص النماذج التي ليس لها ارتباطات...")
    print("=" * 80)
    
    # الحصول على جميع النماذج
    all_models = apps.get_models()
    
    # قائمة بالنماذج التي ليس لها ارتباطات
    models_without_relations = []
    
    # قائمة بالنماذج التي ليس لها ارتباطات واردة
    models_without_incoming_relations = []
    
    # قائمة بالنماذج التي ليس لها ارتباطات صادرة
    models_without_outgoing_relations = []
    
    # قاموس لتخزين جميع الارتباطات
    all_relations = {}
    
    # جمع جميع الارتباطات
    for model in all_models:
        model_name = f"{model._meta.app_label}.{model.__name__}"
        all_relations[model_name] = {
            'outgoing': [],  # الارتباطات الصادرة
            'incoming': [],  # الارتباطات الواردة
        }
        
        # الارتباطات الصادرة
        for field in model._meta.get_fields():
            if isinstance(field, (ForeignKey, ManyToManyField, OneToOneField)):
                related_model = field.related_model
                if related_model:
                    related_model_name = f"{related_model._meta.app_label}.{related_model.__name__}"
                    all_relations[model_name]['outgoing'].append({
                        'field_name': field.name,
                        'related_model': related_model_name,
                        'field_type': field.__class__.__name__,
                    })
    
    # جمع الارتباطات الواردة
    for model in all_models:
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        for field in model._meta.get_fields():
            if isinstance(field, RelatedField) and not field.concrete:
                related_model = field.related_model
                if related_model:
                    related_model_name = f"{related_model._meta.app_label}.{related_model.__name__}"
                    if related_model_name in all_relations:
                        all_relations[related_model_name]['incoming'].append({
                            'field_name': field.name,
                            'related_model': model_name,
                            'field_type': field.__class__.__name__,
                        })
    
    # تحليل الارتباطات
    for model_name, relations in all_relations.items():
        if not relations['outgoing'] and not relations['incoming']:
            models_without_relations.append(model_name)
        
        if not relations['incoming']:
            models_without_incoming_relations.append(model_name)
        
        if not relations['outgoing']:
            models_without_outgoing_relations.append(model_name)
    
    # طباعة النتائج
    print(f"عدد النماذج الكلي: {len(all_models)}")
    print(f"عدد النماذج التي ليس لها أي ارتباطات: {len(models_without_relations)}")
    print(f"عدد النماذج التي ليس لها ارتباطات واردة: {len(models_without_incoming_relations)}")
    print(f"عدد النماذج التي ليس لها ارتباطات صادرة: {len(models_without_outgoing_relations)}")
    
    print("\nالنماذج التي ليس لها أي ارتباطات:")
    for model_name in sorted(models_without_relations):
        print(f"- {model_name}")
    
    print("\nالنماذج التي ليس لها ارتباطات واردة:")
    for model_name in sorted(models_without_incoming_relations):
        if model_name not in models_without_relations:
            print(f"- {model_name}")
    
    print("\nالنماذج التي ليس لها ارتباطات صادرة:")
    for model_name in sorted(models_without_outgoing_relations):
        if model_name not in models_without_relations:
            print(f"- {model_name}")
    
    # تفاصيل الارتباطات لكل نموذج
    print("\nتفاصيل الارتباطات لكل نموذج:")
    for model_name, relations in sorted(all_relations.items()):
        print(f"\n{model_name}:")
        
        print("  الارتباطات الصادرة:")
        if relations['outgoing']:
            for relation in relations['outgoing']:
                print(f"    - {relation['field_name']} -> {relation['related_model']} ({relation['field_type']})")
        else:
            print("    - لا يوجد")
        
        print("  الارتباطات الواردة:")
        if relations['incoming']:
            for relation in relations['incoming']:
                print(f"    - {relation['field_name']} <- {relation['related_model']} ({relation['field_type']})")
        else:
            print("    - لا يوجد")

if __name__ == "__main__":
    check_models()
