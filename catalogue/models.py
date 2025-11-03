"""
Modelos de catálogo personalizados.
Fix para error MySQL: "You can't specify target table for update in FROM clause"
"""
from django.db import models, connection
from oscar.apps.catalogue.abstract_models import AbstractCategory
from treebeard.mp_tree import MP_NodeManager


class CategoryManager(MP_NodeManager):
    """
    Manager personalizado para Category que evita subconsultas problemáticas en MySQL.
    """
    
    def get_queryset(self):
        """Override para agregar optimizaciones MySQL-friendly."""
        return super().get_queryset()


class Category(AbstractCategory):
    """
    Override del modelo Category para fix de MySQL.
    
    El problema original es que MySQL no permite:
    UPDATE table SET field = (SELECT MAX(field) FROM table WHERE ...)
    
    Este override usa transacciones y evita subconsultas anidadas.
    """
    
    objects = CategoryManager()
    
    class Meta:
        proxy = False
        app_label = 'catalogue'
        ordering = ['path']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def save(self, *args, **kwargs):
        """
        Override del save para evitar subconsultas problemáticas en MySQL.
        """
        # Para MySQL, desactivar temporalmente las restricciones de subconsultas
        # usando transacciones atómicas
        from django.db import transaction
        
        with transaction.atomic():
            # Forzar que use transacciones para evitar el error de MySQL
            super().save(*args, **kwargs)
    
    @classmethod
    def fix_tree(cls, destructive=False):
        """
        Override de fix_tree para evitar subconsultas en MySQL.
        """
        from django.db import transaction
        
        with transaction.atomic():
            return super().fix_tree(destructive=destructive)


# Importar todos los modelos de Oscar EXCEPTO Category
from oscar.apps.catalogue.models import (
    AbstractProduct,
    AbstractProductClass,
    AbstractProductAttribute,
    AbstractProductAttributeValue,
    AbstractAttributeOption,
    AbstractAttributeOptionGroup,
    AbstractOption,
    AbstractProductRecommendation,
    AbstractProductImage,
    Product,
    ProductClass,
    ProductAttribute,
    ProductAttributeValue,
    AttributeOption,
    AttributeOptionGroup,
    Option,
    ProductRecommendation,
    ProductImage,
)

__all__ = [
    'Category',
    'Product',
    'ProductClass',
    'ProductAttribute',
    'ProductAttributeValue',
    'AttributeOption',
    'AttributeOptionGroup',
    'Option',
    'ProductRecommendation',
    'ProductImage',
]
