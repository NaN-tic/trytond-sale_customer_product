# This file is part of sale_customer_product module for Tryton.  The COPYRIGHT
# file at the top level of this repository contains the full copyright notices
# and license terms.
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pyson import Eval, If
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction

__all__ = ['Template', 'Product', 'ProductCustomer']


class Template(metaclass=PoolMeta):
    __name__ = "product.template"
    product_customers = fields.One2Many('sale.product_customer',
        'product', 'Customers',
        states={
            'readonly': ~Eval('active', True),
            'invisible': (~Eval('salable', False)
                | ~Eval('context', {}).get('company')),
            },
        depends=['active', 'salable'])
    customer_code = fields.Function(fields.Char('Customer Code'),
        'get_customer_fields', searcher='search_customer_field')
    customer_name = fields.Function(fields.Char('Customer Name'),
        'get_customer_fields', searcher='search_customer_field')

    @classmethod
    def get_customer_fields(cls, templates, names):
        ProductCustomer = Pool().get('sale.product_customer')

        template_ids = [x.id for x in templates]
        customer_code = dict((x, None) for x in template_ids)
        customer_name = dict((x, None) for x in template_ids)
        sale_customer = Transaction().context.get('sale_customer')
        if sale_customer:
            pcs = ProductCustomer.search([
                    ('product', 'in', template_ids),
                    ('party', '=', sale_customer),
                    ])
            for pc in pcs:
                customer_code[pc.product.id] = pc.code
                customer_name[pc.product.id] = pc.name

        res = {}
        if 'customer_code' in names:
            res['customer_code'] = customer_code
        if 'customer_name' in names:
            res['customer_name'] = customer_name
        return res

    @classmethod
    def search_customer_field(cls, name, clause):
        ProductCustomer = Pool().get('sale.product_customer')
        field_name = name.replace('customer_', '')
        sale_customer = Transaction().context.get('sale_customer')
        if sale_customer:
            pcs = ProductCustomer.search([
                    (field_name,) + tuple(clause[1:]),
                    ('party', '=', sale_customer),
                    ])
            res = [
                ('product_customers', 'in', [x.id for x in pcs]),
                ]
        else:
            res = [
                ('product_customers.%s' % field_name,) + tuple(clause[1:]),
                ]
        return res


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
    customer_code = fields.Function(fields.Char('Customer Code'),
        'get_customer_fields', searcher='search_customer_field')
    customer_name = fields.Function(fields.Char('Customer Name'),
        'get_customer_fields', searcher='search_customer_field')

    @classmethod
    def get_customer_fields(cls, products, names):
        Template = Pool().get('product.template')

        product_ids = [x.id for x in products]
        customer_code = dict((x, None) for x in product_ids)
        customer_name = dict((x, None) for x in product_ids)
        if Transaction().context.get('sale_customer'):
            template_ids = [product.template.id for product in products]
            templates = Template.browse(template_ids)
            tcodes = dict([(x.id, x.customer_code) for x in templates])
            tnames = dict([(x.id, x.customer_name) for x in templates])
            for product in products:
                customer_code[product.id] = tcodes[product.template.id]
                customer_name[product.id] = tnames[product.template.id]

        res = {}
        if 'customer_code' in names:
            res['customer_code'] = customer_code
        if 'customer_name' in names:
            res['customer_name'] = customer_name
        return res

    @classmethod
    def search_customer_field(cls, name, clause):
        return [('template.%s' % name,) + tuple(clause[1:])]

    @classmethod
    def search_rec_name(cls, name, clause):
        res = super(Product, cls).search_rec_name(name, clause)
        if Transaction().context.get('sale_customer'):
            res += [
                ('customer_code',) + tuple(clause[1:]),
                ('customer_name',) + tuple(clause[1:]),
                ]
        return res


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

    @classmethod
    def __setup__(cls):
        super(ProductCustomer, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('product_party_company_uniq',
                Unique(t, t.product, t.party, t.company),
                'Product and party must be unique per company.'),
            ]

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
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('code',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
            ]
