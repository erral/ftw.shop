from zope.interface import implements
from zope.component import adapts
from zope.annotation.interfaces import IAnnotations

from decimal import Decimal

from ftw.shop.interfaces import IVariationConfig, IShopItem

from persistent.mapping import PersistentMapping
from zope.component import getUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer


class VariationConfig(object):
    """An Adapter for storing variation configurations on ShopItems
    """

    implements(IVariationConfig)
    adapts(IShopItem)

    def __init__(self, context):
        self.context = context
        self.annotations = IAnnotations(self.context)

    def hasVariations(self):
        """Determines if the item has variations or not
        """
        field = self.context.Schema().getField('variation1_attribute')
        return field.get(self.context) not in (None, '')

    def getVariationDict(self):
        """Returns a nested dict with the variation config for the item
        """
        return self.annotations.get('variations', PersistentMapping())

    def updateVariationConfig(self, data):
        """Updates the stored variation config with changes
        """
        if not 'variations' in self.annotations.keys():
            self.annotations['variations'] = PersistentMapping()
        self.annotations['variations'].update(data)

    def getVariation1Values(self):
        """Returns the values for the top level variation,
        e.g. ['Red', 'Green', 'Blue']
        """
        value_string = getattr(self.context, 'variation1_values', None)
        if value_string:
            return [v.strip() for v in value_string.split(',')]
        else:
            return []

    def getVariation2Values(self):
        """Returns the values for the second level variation,
        e.g. ['S', 'M', 'L', 'XL']
        """
        value_string = getattr(self.context, 'variation2_values', None)
        if value_string:
            return [v.strip() for v in value_string.split(',')]
        else:
            return []

    def getVariationAttributes(self):
        """Returns a list of the two variation attributes,
        e.g. ['Color', 'Size']
        """
        variation_attributes = []
        for name in ['variation1_attribute', 'variation2_attribute']:
            field = self.context.Schema().getField(name)
            if field.get(self.context) not in (None, ''):
                variation_attributes.append(field.get(self.context))
        return variation_attributes

    def getVariationData(self, var1_attr, var2_attr, field):
        """Returns the data for one specific variation instance's field
        """
        variation_dict = self.getVariationDict()
        normalizer = getUtility(IIDNormalizer)

        if var2_attr is None:
            # We only have one variation
            variation_key = normalizer.normalize(var1_attr)
        else:
            # We have two levels of variation
            variation_key = normalizer.normalize("%s-%s" % (var1_attr, var2_attr))
        var_data = variation_dict.get(variation_key, None)
        if var_data is not None and field in var_data.keys():
            if not var_data[field] == "":
                return var_data[field]
        # Return a default value appropriate for the field type
        if field == 'active':
            return True
        elif field == 'price':
            return Decimal("%s.%02d" % self.context.price)
        elif field == 'stock':
            return 0
        elif field == 'skuCode':
            return ""
        else:
            return None

    def getPrettyName(self, variation_key):
        """Returns the human facing name for a variation,
        e.g. 'Green-XXL'
        """
        normalizer = getUtility(IIDNormalizer)
        if len(self.getVariationAttributes()) == 1:
            for var1_value in self.getVariation1Values():
                vkey = normalizer.normalize(var1_value)
                if vkey == variation_key:
                    return var1_value
        else:
            for var1_value in self.getVariation1Values():
                for var2_value in self.getVariation2Values():
                    vkey = normalizer.normalize("%s-%s" % (var1_value, var2_value))
                    if vkey == variation_key:
                        return "%s-%s" % (var1_value, var2_value)
        return None
        