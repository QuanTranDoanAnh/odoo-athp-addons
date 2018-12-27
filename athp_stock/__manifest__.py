{
    'name': "An Toan Hoa Phat Stock Management App",
    'summary': "Stock Management App customized for An Toan Hoa Phat",
    'description': """
    Stock Management App customized for An Toan Hoa Phat
    """,
    'author': 'Business Link Development Technologies Co., Ltd.',
    'website': 'http://www.bld.com.vn',
    'license': 'Other proprietary',
    'depends': ['base', 'stock'],
    'category': 'Stock',
    'version': '1.0.0',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_request_views.xml',
        'views/product_views.xml',
        'views/actions.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True
}