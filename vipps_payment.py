"""
    File : vipps_payment.py
    Author : Stian Broen
    Date : 21.07.2022
    Description :

Using the Vipps API, perform payment-related operations

"""

# from standard Python
import datetime

# from common_library
from libs.commonlib.db_insist import get_db

VEDBJORN_INTERMEDIATE_ACCOUNT : str = 'VEDBJORN_INTERMEDIATE_ACCOUNT'
VEDBJORN_SELF_ACCOUNT         : str = 'VEDBJORN_SELF_ACCOUNT'
PTC_CUT_DRIVER   : float = 0.2
PTC_CUT_VEDBJORN : float = 0.05

"""
    Function : request_payment

    Description :

        Request a VIPPS payment from a target paying user. The money will be transferred to the Vedbjørn account
         
"""
def request_payment(amount_NOK : float , paying_user : dict , message : str , ref : dict, is_fake : bool = False,
                    calc_time : datetime.datetime = datetime.datetime.utcnow()) :

    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$')
    print('$   VIPPS - Request Payment : BEGINS')
    print('$')
    print('$   Time : ' , datetime.datetime.utcnow())
    print('$   Amount : ' , amount_NOK , ' NOK ,-')
    print('$   Target User : ' , paying_user.get('name' , 'N/A'))
    print('$   Message : ' , message )
    print('$   Reference : ', ref.get('describe' , 'N/A'))
    print('$')
    print('$')

    # TODO
    # TODO
    # TODO
    payment_doc : dict = {
        'amount_NOK' : amount_NOK ,
        'paying_user' : paying_user ,
        'receiving_user' : VEDBJORN_INTERMEDIATE_ACCOUNT ,
        'message' : message ,
        'ref' : ref ,
        'status' : 'unpaid' ,
        'calc_time' : calc_time.timestamp()
    }
    if is_fake :
        payment_doc['fake'] = True

    db = get_db()
    payment_ref = db.insist_on_insert_one('vipps_payments_in' , payment_doc)

    print('$')
    print('$')
    print('$   VIPPS - Request Payment : FINISHED')
    print('$')
    print('$   Time : ', datetime.datetime.utcnow())
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    return payment_ref


"""
    Function : pay_seller_and_driver

    Description :

        All planned sales for a specific seller has completed.
        This means money has been transferred from all purchasing clients, to Vedbjørns account
        Now, we must transfer the income back from Vedbjørns account to the seller and the driver

"""
def pay_seller_and_driver(amount_NOK : float , seller : dict , driver : dict , message : str , ref : dict ,
                          is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()):

    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$')
    print('$   VIPPS - Pay Seller and Driver : BEGINS')
    print('$')
    print('$   Time : ' , datetime.datetime.utcnow())
    print('$   Amount : ' , amount_NOK , ' NOK ,-')
    print('$   Seller : ' , seller.get('name' , 'N/A'))
    print('$   Driver : ', driver.get('name', 'N/A'))
    print('$   Message : ' , message )
    print('$   Reference : ', ref.get('describe' , 'N/A'))
    print('$')
    print('$')

    # TODO
    # TODO
    # TODO

    amount_reserved_for_driver   : float = amount_NOK * PTC_CUT_DRIVER
    amount_reserved_for_vedbjorn : float = amount_NOK * PTC_CUT_VEDBJORN
    amount_reserved_for_seller   : float = amount_NOK - amount_reserved_for_driver - amount_reserved_for_vedbjorn

    db = get_db()
    seller_payment_doc : dict = {
        'amount_NOK' : amount_reserved_for_seller ,
        'paying_user' : VEDBJORN_INTERMEDIATE_ACCOUNT ,
        'receiving_user' : seller ,
        'message' : message ,
        'ref' : ref ,
        'status' : 'unpaid' ,
        'calc_time' : calc_time.timestamp() ,
        'target' : 'seller'
    }
    if is_fake :
        seller_payment_doc['fake'] = True

    seller_payment_ref = db.insist_on_insert_one('vipps_payments_out' , seller_payment_doc)

    driver_payment_doc: dict = {
        'amount_NOK': amount_reserved_for_driver,
        'paying_user': VEDBJORN_INTERMEDIATE_ACCOUNT,
        'receiving_user': driver,
        'message': message,
        'ref': ref,
        'status': 'unpaid',
        'calc_time': calc_time.timestamp() ,
        'target' : 'driver'
    }
    if is_fake :
        driver_payment_doc['fake'] = True

    driver_payment_ref = db.insist_on_insert_one('vipps_payments_out', driver_payment_doc)

    print('$')
    print('$')
    print('$   VIPPS - Pay Seller and Driver : FINISHED')
    print('$')
    print('$   Time : ', datetime.datetime.utcnow())
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    return seller_payment_ref , driver_payment_ref


"""
    Function : pay_vedbjorn

    Description :

        

"""
def pay_vedbjorn(wrapup_obj : dict , is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()) :
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$')
    print('$   VIPPS - Pay Vedbjørn : BEGINS')
    print('$')
    print('$   Time : ' , datetime.datetime.utcnow())
    print('$')
    print('$')

    db = get_db()
    amount_reserved_for_vedbjorn: float = wrapup_obj['total_income_from_sales_paid'] * PTC_CUT_VEDBJORN
    driver_payment_doc: dict = {
        'amount_NOK': amount_reserved_for_vedbjorn,
        'paying_user': VEDBJORN_INTERMEDIATE_ACCOUNT,
        'receiving_user': VEDBJORN_SELF_ACCOUNT,
        'ref': wrapup_obj,
        'status': 'unpaid',
        'calc_time': calc_time.timestamp()
    }
    if is_fake :
        driver_payment_doc['fake'] = True

    payment_ref = db.insist_on_insert_one('vipps_internal_transfers', driver_payment_doc)

    print('$')
    print('$')
    print('$   VIPPS - Pay Vedbjørn : FINISHED')
    print('$')
    print('$   Time : ', datetime.datetime.utcnow())
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    return payment_ref
