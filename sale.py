# This file is part of sale_customer_product module for Tryton.  The COPYRIGHT
# file at the top level of this repository contains the full copyright
# notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['SaleLine']
__metaclass__ = PoolMeta


class SaleLine:
    __name__ = 'sale.line'

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls.product.context['sale_customer'] = Eval('_parent_sale',
            {}).get('party')

    @fields.depends('product', 'sale')
    def on_change_product(self):
        ProductCustomer = Pool().get('sale.product_customer')
        super(SaleLine, self).on_change_product()
        if self.product:
            party_context = {}
            if self.sale and self.sale.party:
                party = self.sale.party
                if party.lang:
                    party_context['language'] = party.lang.code
                with Transaction().set_context(party_context):
                    products = ProductCustomer.search([
                            ('product', '=', self.product.template.id),
                            ('party', '=', self.sale.party.id),
                            ])
                if products:
                    product = products[0]
                    code = product.code or self.product.code
                    name = product.name or self.product.template.name
                    description = name
                    if code:
                        description = '[%s] %s' % (code, description)
                    self.description = description
