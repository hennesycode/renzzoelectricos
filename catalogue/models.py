"""
Modelos de catálogo personalizados.
Fix para error MySQL: "You can't specify target table for update in FROM clause"
"""
from django.db import models
from oscar.apps.catalogue.abstract_models import AbstractCategory


class Category(AbstractCategory):
    """
    Override del modelo Category para fix de MySQL.
    
    El problema original es que MySQL no permite:
    UPDATE table SET field = (SELECT MAX(field) FROM table WHERE ...)
    
    Este override cambia la forma en que se calcula el depth evitando la subconsulta.
    """
    
    def save(self, *args, **kwargs):
        """
        Override del save para calcular depth sin subconsulta problemática.
        """
        # Calcular depth basándose en los padres
        if self.is_root():
            self.depth = 1
        else:
            # En lugar de hacer subconsulta, obtener el parent primero
            if self.move_to_id:
                try:
                    parent = Category.objects.get(pk=self.move_to_id)
                    # Establecer depth basado en el padre
                    self.depth = parent.depth + 1
                except Category.DoesNotExist:
                    self.depth = 1
            elif hasattr(self, '_mptt_cached_fields') and 'parent' in self._mptt_cached_fields:
                parent = self._mptt_cached_fields['parent']
                if parent:
                    self.depth = parent.depth + 1
                else:
                    self.depth = 1
            else:
                self.depth = 1
        
        super().save(*args, **kwargs)


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
