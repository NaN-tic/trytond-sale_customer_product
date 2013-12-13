#This file is part of sale_customer_product module for Tryton.  The COPYRIGHT
#file at the top level of this repository contains the full copyright
#notices and license terms.

import datetime

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend

__all__ = ['Template', 'Product', 'ProductCustomer', 'SaleLine']
__metaclass__ = PoolMeta


class Template:
    __name__ = "product.template"

    product_customer = fields.One2Many('sale.product_customer',
        'product', 'Customers', states={
            'readonly': ~Eval('active', True),
            'invisible': (~Eval('salable', False)
                | ~Eval('context', {}).get('company')),
            }, depends=['active', 'salable'])


class Product:
    __name__ = 'product.product'

    def get_rec_name(self, name):
        sale_party = Transaction().context.get('sale_party')
        if not sale_party:
            return super(Product, self).get_rec_name(name)

        ProductCustomer = Pool().get('sale.product_customer')
        products = ProductCustomer.search([
                ('product', '=', self.template.id),
                ('party', '=', sale_party)])

        rec_name = super(Product, self).get_rec_name(name)

        if not products:
            return rec_name

        product, = products

        customer_rec_name = ''
        if product.code:
            customer_rec_name = '[' + product.code + '] '
        customer_rec_name += product.name

        return customer_rec_name + " / " + rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        sale_party = Transaction().context.get('sale_party')
        customer_products = Pool().get('sale.product_customer').search(
            [tuple(clause), ('party', '=', sale_party)])

        ids2 = [x.product.id for x in customer_products]
        ids = map(int, cls.search([('code', ) + tuple(clause[1:])], order=[]))
        ids += ids2

        if ids:
            ids += map(int,
                cls.search([('template.name',) + tuple(clause[1:])], order=[]))
            return [('id', 'in', ids)]
        return [('template.name', ) + tuple(clause[1:])]


class ProductCustomer(ModelSQL, ModelView):
    'Product Customer'

    __name__ = 'sale.product_customer'

    product = fields.Many2One('product.template', 'Product', required=True,
            ondelete='CASCADE', select=True)
    party = fields.Many2One('party.party', 'Customer', required=True,
            ondelete='CASCADE', select=True)
    name = fields.Char('Name', size=None, translate=True, select=True)
    code = fields.Char('Code', size=None, select=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE', select=True,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        if self.code:
            return '[' + self.code + '] ' + self.name
        else:
            return self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        ids = map(int, cls.search([('code',) + tuple(clause[1:])], order=[]))
        if ids:
            ids += map(int,
                cls.search([('name',) + tuple(clause[1:])], order=[]))
            return [('id', 'in', ids)]
        return super(ProductCustomer, cls).search_rec_name(name, clause)


class SaleLine:
    __name__ = 'sale.line'

    customer_product_name = fields.Function(
        fields.Char('Customer Product Name',
            on_change_with=['product', '_parent_sale.party']),
            'on_change_with_customer_product_name')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls.product.context['sale_party'] = Eval('_parent_sale',
            {}).get('party')

    def on_change_with_customer_product_name(self, name=None):
        ProductCustomer = Pool().get('sale.product_customer')
        if not self.product:
            return ''
        products = ProductCustomer.search([
                ('product', '=', self.product.template.id),
                ('party', '=', self.sale.party.id)])

        if not products:
            return ''
        return products[0].rec_name
