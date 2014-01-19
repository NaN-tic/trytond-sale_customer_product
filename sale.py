#This file is part of sale_customer_product module for Tryton.  The COPYRIGHT
#file at the top level of this repository contains the full copyright
#notices and license terms.
import datetime
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend

__all__ = ['SaleLine']
__metaclass__ = PoolMeta


class SaleLine:
    __name__ = 'sale.line'

    def on_change_product(self):
        ProductCustomer = Pool().get('sale.product_customer')
        res = super(SaleLine, self).on_change_product()
        if not self.product:
            return res
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
            res['description'] = description
        return res
