"""
    File : actions.py
    Author : Stian Broen
    Date : 20.07.2022
    Description :

When we have retrieved calculations from the "prepare.py" file, we can take those results and act on them
in this file

"""

# from standard Python
import datetime
import random
import string

# from common_library
from libs.commonlib.db_insist import get_db , set_graph_changed
from libs.commonlib.pymongo_paginated_cursor import PaginatedCursor as mpcur
from libs.commonlib.graph_funcs import mark_pickup_relationship , set_last_calced_BuyRequest , remove_reservation , \
    remove_staged_sell , remove_travel_to_pickup , remove_travel_to_deliver , remove_staged_driver , \
    set_reserved_weeks_BuyRequest , update_stock_sellRequest , mark_delivery_relationship , \
    increment_prepare_for_pickup_for_SellRequest , set_claimed_by_driver_on_buyRequest , \
    decrement_prepare_for_pickup_for_SellRequest , set_driver_available , update_available_driveRequest , \
    get_user_with_sellrequest_name , get_user_with_buyrequest_name , get_user_with_driverequest_name

# from matching_library
from .vipps_payment import request_payment , pay_seller_and_driver

# other stuff
from fpdf import FPDF
import pytz

VEDBJORN_COMPANY : dict = {
    "email_address" : "regninger@vedbjorn.no",
    "companyname" : "VEDBJØRN AS",
    "companynum" : "929350790",
    "companyaddress" : "Adalsveien 1B , 3185 , SKOPPUM"
}

"""
    Function : handle_routes

    Description :
        When a graph-iteration has finished, it will end up in this function with the resulting routes, updating any
        existing route, or inserting the route, if they didnt exist, also initializing notifications to the drivers
    
"""
def handle_routes(routes: dict , is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()) :
    print('###############################')
    print('#')
    print('#       Handle Routes - BEGINS')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')

    for driveRequest_name , route in routes.items() :
        ongoing_route = load_ongoing_route(driveRequest_name)
        if ongoing_route :
            """
            If this is the case, then the graph-algorithm has been mistaken. The target driver has already accepted
            another mission, which is currently being processed. The driver is not available for another mission yet
            """
            update_available_driveRequest(driveRequest_name , False)
            set_graph_changed()
            continue

        overwrite_planned_route(driveRequest_name, route, is_fake, calc_time)

    print('#')
    print('#')
    print('#       Handle Routes - FINISHED')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('###############################')

"""
    Function : handle_failed_reservations

    Description :
        

"""
def handle_failed_reservations(ok_reservations : list , failed_reservations : list,
                               calc_time : datetime.datetime = datetime.datetime.utcnow()) :

    print('###############################')
    print('#')
    print('#       Handling Failed Reservations - BEGINS')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('#')

    if len(failed_reservations) <= 0 :
        print('\tThere are no failed reservations to handle')

    # TODO - The failed reservations needs to be stored, and updated, because it will not be created again in
    #      - subsequent organize_reserved_sales iterations. It may, however, be rendered outdated by subsequent
    #      - iterations, if it turns out that a previously failed reservation is no longer failed, but instead was
    #      - covered by sellRequests like we want to.

    for failed_reservation in failed_reservations :
        # TODO
        # TODO
        # TODO
        pass

    print('#')
    print('#')
    print('#       Handling Failed Reservations - FINISHED')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('###############################')

"""
    Function : handle_failed_sales

    Description :


"""
def handle_failed_sales(ok_sales : list , failed_sales: list ,
                        calc_time : datetime.datetime = datetime.datetime.utcnow()):
    print('###############################')
    print('#')
    print('#       Handling Failed Ordinary Sales - BEGINS')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('#')

    if len(failed_sales) <= 0:
        print('\tThere are no failed sales to handle')

    # TODO - The failed sales needs to be stored, and updated, because it will not be created again in
    #      - subsequent organize_ordinary_sales iterations. It may, however, be rendered outdated by subsequent
    #      - iterations, if it turns out that a previously failed sale is no longer failed, but instead was
    #      - covered by sellRequests like we want to.

    for failed_reservation in failed_sales:
        buyReqyest   = failed_reservation[0]
        buy_user     = failed_reservation[1]
        buy_location = failed_reservation[2]
        print('\tFailed to prepare sale (',buyReqyest['current_requirement'],') for customer (' , buy_user['name'] , ') in (' , buy_location['display_name'],')')
        # TODO
        # TODO
        # TODO

    print('#')
    print('#')
    print('#       Handling Failed Ordinary Sales - FINISHED')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('###############################')

"""
    Function : handle_drives

    Description :


"""
def handle_drives(ok_drives : list , failed_drives : list ,
                  calc_time : datetime.datetime = datetime.datetime.utcnow()):
    print('###############################')
    print('#')
    print('#       Handling Drives - BEGINS')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('#')

    """
        NOTE : Failed drives here are to be expected. It means that SellRequests was found which were not associated
               with drivers. But this could mean that all available routes has been claimed by drivers, and its not
               really "failed" in that regard, just means that the sellers has no more clients to sell to at the moment
    """

    if len(failed_drives) <= 0:
        print('\tThere are no failed sales to handle')


    print('#')
    print('#')
    print('#       Handling Drives - FINISHED')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('###############################')

"""
    Function : execute_and_finalize_routes

    Description :
        This is for debugging purposes, since it will take the role of the driver, and execute all routes all in one go

"""
def execute_and_finalize_routes(routes: dict , is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()):
    print('###############################')
    print('#')
    print('#       Execute and Finalize Routes - BEGINS')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')

    for driveRequest_name , route in routes.items() :
        execute_and_finalize_route(driveRequest_name , route , is_fake , calc_time)

    print('#')
    print('#')
    print('#       Execute and Finalize Routes - FINISHED')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('###############################')

"""
    Function : execute_and_finalize_route

    Description :
        This is for debugging purposes, since it will take the role of the driver, and execute the route all in one go

"""
def execute_and_finalize_route(driveRequest_name : str, route : list, is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()) :

    """
    1. If there are already an ongoing route, load it and continue on it
    """
    ongoing_route = load_ongoing_route(driveRequest_name)
    if ongoing_route :
        return do_all_ongoing_route(ongoing_route, is_fake, calc_time)


    """
    2. Save the route object to the database.

       This can/should go on repeatedly to update the planned route. The driver can pay attention to it until he
       decides that he wants to perform the route. At that time, the planned route will lock and become something
       static the driver needs to complete, before a new planned route can become available for him. From the moment the
       planned route is transferred into an ongoing route, the planned route is zeroed-out, and a new planned route
       can begin to form (it must exclude the sell-requests which are currently being processed by the ongoing route)

        production will do something like :
        
        while True :
            overwrite_planned_route(driveRequest_name, route, is_fake, calc_time)
            time.sleep(FOR_A_WHILE)

    """
    overwrite_planned_route(driveRequest_name, route, is_fake, calc_time)

    """
    3. The driver will manage, potentially reorganize and stage the route manually from the mobile-app
       Here, we simulate that situation by loading the recently saved planned_route, and then save the
       ready route to the "staged_routes". Then we load that staged_route, and act upon it
    """
    planned_routes = load_planned_route(driveRequest_name)

    """
    4. The planned route must be "claimed", which means that the buy-requests will be locked into the ongoing
       route which we will create now.
       
       This means that while the driver is taking care of this route, another planned_route can begin to form
       in parallell (the new planned_route will then not include the claimed buy-requests)
       
       In production, this function will be triggered by a driver user, which has been presented the planned_route
       and has decided to claim in.
       
    """

    ongoing_route = claim_planned_route(planned_routes, is_fake, calc_time)

    """
    5. We "cheat" a little bit here, and pretend that the driver executes the ongoing route all in one go
    """
    do_all_ongoing_route(ongoing_route, is_fake, calc_time)

"""
    Function : overwrite_planned_route

    Description :

       This can/should go on repeatedly to update the planned route. The driver can pay attention to it until he
       decides that he wants to perform the route. At that time, the planned route will lock and become something
       static the driver needs to complete, before a new planned route can become available for him. From the moment the
       planned route is transferred into an ongoing route, the planned route is zeroed-out, and a new planned route
       can begin to form (it must exclude the sell-requests which are currently being processed by the ongoing route)

"""
def overwrite_planned_route(driveRequest_name : str, route : list, is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()) :
    route_obj : dict = {
        'driveRequestName' : driveRequest_name ,
        'created_UTC' : datetime.datetime.utcnow().timestamp() ,
        'route' : route ,
        'calc_time' : calc_time.timestamp()
    }
    if is_fake :
        route_obj['fake'] = True

    """
    Sort all purchases into according sellers
    """
    deals : dict = {}
    for visit in route:
        sellRequest = visit.get('sellRequest', {})
        sellRequest_name = sellRequest['name']
        if not sellRequest_name in deals :
            deals[sellRequest_name] = {
                'sellRequest' : sellRequest ,
                'sells' : [] ,
                'number_of_bags_sold' : 0
            }
        if visit.get('type' , '') == 'delivery' :
            buyRequest = visit.get('buyRequest', {})
            deals[sellRequest_name]['sells'].append(buyRequest)
            deals[sellRequest_name]['number_of_bags_sold'] = deals[sellRequest_name]['number_of_bags_sold'] + buyRequest.get('current_requirement' , 0)
    route_obj['deals'] = deals

    db = get_db()
    already_route = db.insist_on_find_one_q('planned_routes' , {'driveRequestName' : driveRequest_name})
    if already_route:
        route_obj['updated'] = datetime.datetime.utcnow().timestamp()
        db.insist_on_replace_one('planned_routes' , already_route['_id'] , route_obj)
    else:
        planned_routes_id = db.insist_on_insert_one('planned_routes' , route_obj)
        for sellreq_name, deal in route_obj.get('deals' , {}).items() :
            seller_graph = get_user_with_sellrequest_name(sellreq_name)
            if seller_graph :
                db.insist_on_insert_one('notifications' , {
                    'email': seller_graph[0][0]['email'],
                    'timestamp': datetime.datetime.utcnow().timestamp(),
                    'planned_routes': planned_routes_id,
                    'contentType' : 'new assignment' ,
                    'status' : 'new' ,
                    'text' : 'Et nytt oppdrag trenger din godkjenning.'
                })

"""
    Function : load_planned_route

    Description :


"""
def load_planned_route(driveRequest_name : str) :
    db = get_db()
    already_route = db.insist_on_find_one_q('planned_routes', {'driveRequestName': driveRequest_name})
    return already_route

"""
    Function : load_ongoing_route

    Description :


"""
def load_ongoing_route(driveRequest_name : str) -> dict :
    db = get_db()
    already_route = db.insist_on_find_one_q('ongoing_routes', {
        'driveRequestName': driveRequest_name ,
        'status' : 'ongoing'
    })
    return already_route

def decline_planned_route(planned_routes: dict):
    db = get_db()
    set_driver_available(planned_routes['driveRequestName'], False)
    db.insist_on_delete_one('planned_routes', planned_routes['_id'])

"""
    Function : claim_planned_route

    Description :


"""
def claim_planned_route(planned_routes: dict, is_fake: bool = False, calc_time: datetime.datetime = datetime.datetime.utcnow()):
    db = get_db()
    set_driver_available(planned_routes['driveRequestName'], False)
    db.insist_on_delete_one('planned_routes', planned_routes['_id'])
    del planned_routes['_id']
    if is_fake:
        planned_routes['fake'] = True
        planned_routes['calc_time'] = calc_time.timestamp()
    planned_routes['due'] = calc_time.timestamp() + (86400 * 2)
    inserted_id = db.insist_on_insert_one('ongoing_routes',planned_routes)  # < the "planned_route" is now an "ongoing route"
    planned_routes['status'] = 'ongoing'
    planned_routes['_id'] = inserted_id

    for trip in planned_routes.get('route', []):
        if trip.get('type', '') == 'pickup':
            prepare_increment_by = trip.get('loaded_after', 0) - trip.get('loaded_before', 0)
            sellRequest_name = trip.get('sellRequest', {}).get('name', '')

            #
            # TODO : Notify the seller to prepare cargo for pickup
            #
            sellerNode = get_user_with_sellrequest_name(sellRequest_name)

            db.insist_on_insert_one('notifications', {
                'status': 'requested',
                'email': sellerNode[0][0]['email'],
                'contentType': 'pickup',
                'amount': prepare_increment_by ,
                'ongoing_routes' : inserted_id
            })

            increment_prepare_for_pickup_for_SellRequest(sellRequest_name, prepare_increment_by)
        elif trip.get('type', '') == 'delivery':

            buyRequest_name = trip.get('buyRequest', {}).get('name', '')
            #
            # TODO : Notify the buyer that cargo is on it's way
            #
            buyerNode = get_user_with_buyrequest_name(buyRequest_name)
            db.insist_on_insert_one('notifications', {
                'status': 'requested',
                'email': buyerNode[0][0]['email'],
                'contentType': 'delivery' ,
                'ongoing_routes': inserted_id
            })
            set_claimed_by_driver_on_buyRequest(buyRequest_name, True)

    return planned_routes

"""
    Function : do_all_ongoing_route

    Description :


"""
def do_all_ongoing_route(ongoing_route : dict, is_fake : bool = False, calc_time : datetime.datetime = datetime.datetime.utcnow()) :

    if ongoing_route.get('status' , '_') == 'completed' :
        #
        # This ongoing route is actually already fininshed
        #
        return {'visited_status' : 'already'}

    index : int = -1
    driveRequestName = ongoing_route['driveRequestName']
    print('\tdo_all_ongoing_route for driveRequestName(',driveRequestName,')')
    for visit in ongoing_route.get('route' , []) :
        index = index + 1
        if not visit or not isinstance(visit, dict) :
            print('\t\tWARNING : Invalid visit-definition at index ' , index)
            continue
        visited = None
        if visit.get('type', '') == 'pickup' :
            visited = handle_pickup(visit , driveRequestName, index , ongoing_route, is_fake, calc_time)
        elif visit.get('type', '') == 'delivery' :
            visited = handle_delivery(visit , driveRequestName, index , ongoing_route, is_fake, calc_time)
        if visited and visited.get('visited_status') == 'completed':
            pass
        elif visited and visited.get('visited_status') == 'invalid' and 'errmsg' in visited:
            print('\tFAILED visited ', visit.get('type', '_'), ' ',visit.get('buyRequest', visit.get('sellRequest', {})).get('name', '_'), ' at index ', index, 'status =', visit.get('visited_status', ''))
            print('\t\tError Message : ' , visited.get('errmsg'))
        elif visited and visited.get('visited_status') == 'already':
            print('\tALREADY visited ', visit.get('type', '_'), ' ', visit.get('buyRequest', visit.get('sellRequest', {})).get('name', '_'), ' at index ', index, 'status =', visit.get('visited_status', ''))
        else:
            print('\tFAILED visited ', visit.get('type', '_'), ' ', visit.get('buyRequest', visit.get('sellRequest', {})).get('name', '_'), ' at index ', index, 'status =', visit.get('visited_status', ''))
            print('\t\tError Message : VOID')


"""
    Function : handle_pickup

    Description :

        This function needs to be called by the driver-app, when the driver has arrived at a pickup-point for a seller,
        and has picked up the correct amount of cargo

"""
def handle_pickup(visit : dict , driveRequestName : str, index : int , ongoing_route : dict, is_fake : bool = False,
                  calc_time : datetime.datetime = datetime.datetime.utcnow() , meta : dict = {}) -> dict :

    def is_valid_pickup(visit : dict) -> tuple :
        if not visit :
            return 'Falsy visit' , False
        if visit.get('type' , '_') != 'pickup' :
            return 'visit.type != \"pickup\"' , False
        if not 'sellRequest' in visit :
            return 'no sellRequest in visit' , False
        if not 'name' in visit['sellRequest'] :
            return 'no name in visit.sellRequest' , False
        return '' , True

    if ongoing_route.get('status' , '_') == 'completed' :
        #
        # This ongoing route is actually already fininshed
        #
        return {'visited_status' : 'already'}

    errmsg , is_valid = is_valid_pickup(visit)
    if not is_valid :
        return {'visited_status' : 'invalid' , 'errmsg' : errmsg}

    sellRequestName = visit['sellRequest']['name']
    db = get_db()
    already_visited = db.insist_on_find_one_q('pickups' , {
        'driveRequestName' : driveRequestName ,
        'ongoing_route' : ongoing_route['_id'] ,
        'sellRequestName' : sellRequestName
    })
    if already_visited :
        already_visited['visited_status'] = 'already'
        return already_visited

    # TODO - The actual pickup-process handling comes here
    # TODO - The actual pickup-process handling comes here
    # TODO - The actual pickup-process handling comes here

    now_time_string = calc_time.strftime('%d.%m.%Y %H:%M:%S')
    pickup_document : dict = visit
    pickup_document['visited_status']   = 'completed'
    pickup_document['completed']        = calc_time.timestamp()
    pickup_document['completed_str']    = now_time_string
    pickup_document['driveRequestName'] = driveRequestName
    pickup_document['ongoing_route']    = ongoing_route['_id']
    pickup_document['sellRequestName']  = sellRequestName
    pickup_document['index']            = index
    if meta :
        pickup_document['meta'] = meta
    if is_fake :
        pickup_document['fake'] = True
    inserted_id = db.insist_on_insert_one('pickups' , pickup_document)
    pickup_document['_id'] = inserted_id
    mark_pickup_relationship(driveRequestName, sellRequestName, 'completed' , now_time_string)

    """
        Update the trip info in the ongoing_route document, so we can know whether or not the route is finished
    """
    db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited', inserted_id)
    db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited_status', 'completed')

    print('\tNEW visited pickup ', sellRequestName, ' at index ', index, ', status = completed')

    """
    Check ongoing_route is finished. It should not be, because a "pickup" needs to be followed by deliveries. But lets
    check in any case, maybe in the future we can have negative pickups (e.g. return an excessive loaded cargo)
    """
    is_done , msg = verify_that_route_is_completed(ongoing_route)
    if is_done :

        wrap_up_ongoing_route(str(ongoing_route['_id']), is_fake, calc_time)
        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'finished')
        plan = db.insist_on_find_one_q('planned_routes', {'driveRequestName': ongoing_route['driveRequestName']})
        if plan:
            db.insist_on_delete_one('planned_routes', plan['_id'])
        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'all_delivered')

    return pickup_document

"""
    Function : handle_delivery

    Description :


"""
def handle_delivery(visit: dict , driveRequestName : str, index : int, ongoing_route : dict, is_fake : bool = False,
                    calc_time : datetime.datetime = datetime.datetime.utcnow(), meta : dict = {}) -> dict:

    def is_valid_delivery(visit: dict) -> tuple:
        if not visit:
            return 'Falsy visit', False
        if visit.get('type', '_') != 'delivery':
            return 'visit.type != \"delivery\"', False
        if not 'buyRequest' in visit:
            return 'no buyRequest in visit', False
        if not 'sellRequest' in visit:
            return 'no sellRequest in visit', False
        if not 'name' in visit['buyRequest']:
            return 'no name in visit.buyRequest', False
        return '', True

    if ongoing_route.get('status' , '_') == 'completed' :
        #
        # This ongoing route is actually already fininshed
        #
        return {'visited_status' : 'already'}

    errmsg, is_valid = is_valid_delivery(visit)
    if not is_valid:
        return {'visited_status': 'invalid', 'errmsg': errmsg}

    sellRequest = visit['sellRequest']
    buyRequest = visit['buyRequest']
    buyRequestName = buyRequest['name']
    graphret = get_user_with_buyrequest_name(buyRequestName)
    if not graphret :
        return {'visited_status': 'invalid', 'errmsg': 'Buyer user not found'}
    buyer = graphret[0][0]
    db = get_db()

    already_visited = db.insist_on_find_one_q('deliveries', {
        'driveRequestName': driveRequestName,
        'ongoing_route': ongoing_route['_id'],
        'buyRequestName': buyRequestName
    })
    if already_visited:
        if not 'visited' in ongoing_route['route'][index] :
            db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited', already_visited['_id'])
            db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited_status', 'completed')
            return already_visited
        already_visited['visited_status'] = 'already'
        return already_visited

    # TODO - The actual delivery-process handling comes here
    # TODO - The actual delivery-process handling comes here
    # TODO - The actual delivery-process handling comes here

    letters = string.ascii_uppercase
    the_code = ''.join(random.choice(letters) for i in range(4))

    now_time_string = calc_time.strftime('%d.%m.%Y %H:%M:%S')
    delivery_document: dict = visit
    delivery_document['visited_status'] = 'completed'
    delivery_document['completed'] = calc_time.timestamp()
    delivery_document['completed_str'] = now_time_string
    delivery_document['driveRequestName'] = driveRequestName
    delivery_document['ongoing_route'] = ongoing_route['_id']
    delivery_document['buyRequestName'] = buyRequestName
    delivery_document['index'] = index
    delivery_document['the_code'] = the_code
    if is_fake :
        delivery_document['fake'] = True
    if meta :
        delivery_document['meta'] = meta
    inserted_id = db.insist_on_insert_one('deliveries', delivery_document)
    delivery_document['_id'] = inserted_id

    mark_delivery_relationship(driveRequestName, buyRequestName, 'completed', now_time_string)

    """
        Find the correct price
    """
    price_at_county = db.insist_on_find_one_q('prices' , {'county' : visit.get('to', {}).get('county' , '_')})
    if price_at_county :
        price_per_bag = price_at_county.get('price', 150)
    else:
        price_per_bag = sellRequest.get('price' , 150)
    price_for_delivery = price_per_bag * buyRequest.get('current_requirement' , 0)


    """
        Create the Vipps-message
    """
    message : str = 'Leveranse av ved fra Vedbjørn :)\n' + \
                    'Antall vedsekker : ' + str(buyRequest.get('current_requirement' , 0)) + '\n' + \
                    'Pris per vedsekk : ' + str(price_per_bag) + ' kr. (inkludert MVA)' + '\n' + \
                    'Levert av sjåføren : ' + driveRequestName + '\n' + \
                    'Kode : ' + the_code

    """
        Create the reference-object
    """
    ref : dict = {
        'collection' : 'deliveries' ,
        'the_code' : the_code ,
        'visit_id' : inserted_id ,
        'route' : ongoing_route['_id'] ,
        'describe' : 'See ObjectId(\"' + str(inserted_id) + '\") at collection \"deliveries\"'
    }

    """
        Send the Vipps request
    """
    payment_ref = request_payment(price_for_delivery , buyer , message , ref , is_fake, calc_time)
    db.insist_on_update_one(delivery_document , 'deliveries' , 'payment_ref' , payment_ref)

    notification_id = db.insist_on_insert_one('notifications' , {
        'email' : buyer['email'] ,
        'timestamp' : datetime.datetime.utcnow().timestamp() ,
        'contentType' : 'delivery' ,
        'ref_collection' : 'deliveries' ,
        'ref_id' : str(inserted_id) ,
        'text' : 'Du har fått en leveranse som trenger din godkjennelse. Ta en titt på bildet du har fått tilsendt. \n'
                 'Stemmer antallet vedsekker oppgitt i teksten på bildet med det antall sekker du ser på bildet? \n'
                 'Hvis alt stemmer så kan du gå videre til betalingen. Det er veldig enkelt og kan gjøres fra din vedbjørn-profil på hjemmesiden. '
                 'Din leveranse id er \"' + the_code + '\". \n'
                 'Takk for samarbeidet!' ,
        'web_text': 'Du har fått en leveranse som trenger din godkjennelse. Ta en titt på bildet nedenfor. \n'
                'Stemmer antallet vedsekker oppgitt i teksten på bildet med det antall sekker du ser på bildet? \n'
                'Hvis alt stemmer så kan du gå videre til betalingen ved å trykke på knappen nedenfor. '
                'Din leveranse id er \"' + the_code + '\". \n'
                'Takk for samarbeidet!',
        'status' : 'new'
    })
    db.insist_on_update_one(delivery_document, 'deliveries', 'notification', notification_id)

    """
        Update the trip info in the ongoing_route document, so we can know whether or not the route is finished
    """
    db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited', inserted_id)
    db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited_status', 'completed')

    print('\tNEW visited delivery ', buyRequestName, ' at index ', index, ', status = completed')

    is_done , msg = verify_that_route_is_completed(ongoing_route)
    if is_done :

        wrap_up_ongoing_route(str(ongoing_route['_id']), is_fake, calc_time)
        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'finished')
        plan = db.insist_on_find_one_q('planned_routes', {'driveRequestName': ongoing_route['driveRequestName']})
        if plan:
            db.insist_on_delete_one('planned_routes', plan['_id'])
        db.insist_on_update_one(ongoing_route , 'ongoing_routes' , 'status' , 'all_delivered')

    return delivery_document

def handle_return(visit: dict , driveRequestName : str, index : int, ongoing_route : dict, is_fake : bool = False,
                    calc_time : datetime.datetime = datetime.datetime.utcnow(), meta : dict = {}) -> dict :

    def is_valid_return(visit: dict) -> tuple:
        if not visit:
            return 'Falsy visit', False
        if visit.get('type', '_') != 'return':
            return 'visit.type != \"return\"', False
        if not 'sellRequest' in visit:
            return 'no sellRequest in visit', False
        if not 'name' in visit['sellRequest']:
            return 'no name in visit.sellRequest', False
        return '', True

    if ongoing_route.get('status' , '_') == 'completed' :
        #
        # This ongoing route is actually already fininshed
        #
        return {'visited_status' : 'already'}

    errmsg, is_valid = is_valid_return(visit)
    if not is_valid:
        return {'visited_status': 'invalid', 'errmsg': errmsg}

    sellRequest = visit['sellRequest']
    sellRequestName = visit['sellRequest']['name']
    db = get_db()
    already_visited = db.insist_on_find_one_q('returns' , {
        'driveRequestName' : driveRequestName ,
        'ongoing_route' : ongoing_route['_id'] ,
        'sellRequestName' : sellRequestName
    })
    if already_visited :
        already_visited['visited_status'] = 'already'
        return already_visited

    # TODO - The actual return-process handling comes here
    # TODO - The actual return-process handling comes here
    # TODO - The actual return-process handling comes here

    now_time_string = calc_time.strftime('%d.%m.%Y %H:%M:%S')
    return_document : dict = visit
    return_document['visited_status']   = 'completed'
    return_document['completed']        = calc_time.timestamp()
    return_document['completed_str']    = now_time_string
    return_document['driveRequestName'] = driveRequestName
    return_document['ongoing_route']    = ongoing_route['_id']
    return_document['sellRequestName']  = sellRequestName
    return_document['index']            = index
    if meta :
        return_document['meta'] = meta
    if is_fake :
        return_document['fake'] = True
    inserted_id = db.insist_on_insert_one('returns' , return_document)
    return_document['_id'] = inserted_id

    """
        Update the trip info in the ongoing_route document, so we can know whether or not the route is finished
    """
    db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited', inserted_id)
    db.insist_on_set_attribute_in_array_at_index(ongoing_route['_id'], 'ongoing_routes', index, 'route', 'visited_status', 'completed')

    print('\tNEW visited return ', sellRequestName, ' at index ', index, ', status = completed')

    is_done, msg = verify_that_route_is_completed(ongoing_route)
    if is_done:
        wrap_up_ongoing_route(str(ongoing_route['_id']) , is_fake, calc_time)
        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'finished')
        plan = db.insist_on_find_one_q('planned_routes', {'driveRequestName': ongoing_route['driveRequestName']})
        if plan:
            db.insist_on_delete_one('planned_routes', plan['_id'])
        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'all_delivered')

    return return_document

"""
    Function : wrap_up_ongoing_route

    Description :


"""
def wrap_up_ongoing_route(ongoing_route_id : str, is_fake : bool = False,
                          calc_time : datetime.datetime = datetime.datetime.utcnow()) :

    print('###############################')
    print('#')
    print('#       Wrap up ongoing route - BEGINS')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')

    def ongoing_route_is_valid(ongoing_route : dict) :
        if not ongoing_route :
            return 'ongoing_route is Falsy' , False
        if not 'route' in ongoing_route or not isinstance(ongoing_route['route'] , list):
            return 'ongoing_route has no route list' , False
        if len(ongoing_route['route']) <= 0 :
            return 'ongoing_route.route is empty' , False
        index : int = -1
        unfinished_visits : list = []
        for visit in ongoing_route['route'] :
            index = index + 1
            is_completed = visit and isinstance(visit, dict) and \
                (str(visit.get('visited_status' , '_')) == 'completed' or str(visit.get('status' , '_')) == 'withdrawn')
            if not is_completed :
                unfinished_visits.append(index)
        if len(unfinished_visits) > 0:
            return 'unfinished visits : ' + str(unfinished_visits) , False
        return '' , True

    db = get_db()
    ongoing_route = db.insist_on_find_one('ongoing_routes' , ongoing_route_id)
    errmsg , is_valid = ongoing_route_is_valid(ongoing_route)
    if is_valid :
        dues : list = []
        dues_indexes : list = []
        total_income_from_sales : float = 0
        total_income_from_sales_due : float = 0
        total_income_from_sales_paid : float = 0
        number_of_deliveries : int = 0
        number_of_pickups : int = 0
        total_distance : float = 0
        duration : float = 0
        began : datetime = None
        ended : datetime = None

        index : int = -1
        new_completed_deals : dict = {}
        already_completed_deals : dict = ongoing_route.get('completed_sellRequests' , {})
        for visit in ongoing_route['route']:

            index = index + 1
            sellRequest = visit.get('sellRequest', {})
            sellRequest_name = sellRequest.get('name', '_')

            if visit.get('visited_status') == 'completed' and visit.get('type') == 'delivery':
                visitObj = db.insist_on_find_one('deliveries', visit['visited'])
                paymentObj = db.insist_on_find_one('vipps_payments_in', visitObj['payment_ref'])

                #if paymentObj.get('status' , '_') == 'paid' :
                total_income_from_sales_paid = total_income_from_sales_paid + paymentObj.get('amount_NOK' , 0)

                if not sellRequest_name in new_completed_deals :
                    new_completed_deals[sellRequest_name] = {
                        'sellRequest' : sellRequest ,
                        'sells' : []
                    }
                new_completed_deals[sellRequest_name]['sells'].append({
                    'visitObj' : visitObj ,
                    'paymentObj' : paymentObj
                })
                # else:
                #     dues_indexes.append(index)
                #     dues.append({
                #         'visitObj' : visitObj ,
                #         'paymentObj' : paymentObj
                #     })
                #     total_income_from_sales_due = total_income_from_sales_due + paymentObj.get('amount_NOK', 0)
                total_income_from_sales = total_income_from_sales + paymentObj.get('amount_NOK', 0)
                number_of_deliveries = number_of_deliveries + 1

            elif visit.get('visited_status') == 'completed' and visit.get('type') == 'pickup':
                visitObj = db.insist_on_find_one('pickups', visit['visited'])
                number_of_pickups = number_of_pickups + 1

            else :
                continue
            total_distance = total_distance + visit.get('distance', 0)
            ended = datetime.datetime.utcfromtimestamp(visitObj['completed'])
            if not began :
                began = datetime.datetime.utcfromtimestamp(visitObj['completed'])

        if began and ended :
            duration = ended.timestamp() - began.timestamp()

        """
        Close all the deals between Vedbjørn and the sellers. This is where the sellers get their share
        """
        for sellRequest_name , completed_deals in new_completed_deals.items() :
            if sellRequest_name in already_completed_deals :
                print('ALREADY completed deal for ' , sellRequest_name)
                continue
            planned_deals = ongoing_route['deals'][sellRequest_name]
            close_planned_deals(planned_deals , completed_deals, ongoing_route, is_fake, calc_time)

        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'finished_time', datetime.datetime.utcnow().timestamp())
        db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'finished_time_str', datetime.datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S'))

        """
        Close the routes themselves. This is where the drivers get paid
        """
        if len(dues) > 0:
            handle_dues(dues)
            db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'dues', dues_indexes)
            db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'missing_payments')
        else:
            db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'dues', [])
            db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'status', 'finished')

            remove_travel_to_pickup(ongoing_route['driveRequestName'])
            remove_travel_to_deliver(ongoing_route['driveRequestName'])
            remove_staged_driver(ongoing_route['driveRequestName'])
            set_driver_available(ongoing_route['driveRequestName'], True)

            wrap_up_obj : dict = {
                'total_income_from_sales_paid' : total_income_from_sales_paid ,
                'number_of_deliveries' : number_of_deliveries ,
                'number_of_pickups' : number_of_pickups ,
                'total_distance' : total_distance ,
                'duration' : duration ,
                'began' : began ,
                'ended' : ended ,
                'ongoing_route' : ongoing_route['_id'] ,
                'calc_time' : calc_time
            }
            if is_fake :
                wrap_up_obj['fake'] = True

            wrap_up_id = db.insist_on_insert_one('wrapup_routes' , wrap_up_obj)
            wrap_up_obj['_id'] = wrap_up_id
            db.insist_on_update_one(ongoing_route, 'ongoing_routes', 'wrapup', wrap_up_id)
            wrap_up_obj['ongoing_route'] = ongoing_route
            # wrapup_payment_id = pay_vedbjorn(wrap_up_obj, is_fake, calc_time)
            # db.insist_on_update_one(wrap_up_obj, 'wrapup_routes', 'payment_ref', wrapup_payment_id)

            generate_and_send_outgoing_invoices(ongoing_route['_id'])

    print('#')
    print('#')
    print('#       Wrap up ongoing route - FINISHED')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('###############################')

def generate_outgoing_invoice(from_company : dict, to_company : dict, amount : float , message : str, bill_date_UTC : datetime.datetime) :
    db = get_db()
    pdf = FPDF()
    pdf.add_page()
    pdf.image('./bear_less_padded.png', 5, 5, 20, 20)
    pdf.set_font('helvetica', 'B', 20)
    pdf.cell(80)
    pdf.cell(30, 10, 'Faktura', align='C', new_y='NEXT', new_x='LMARGIN')

    pdf.ln(15)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(None, None, 'Avsender : ', align='L', new_y='NEXT', new_x='LMARGIN', ln = 2)
    pdf.set_font('helvetica', '', 12)
    from_company_text = from_company.get('companyname', '') + ' (' + from_company.get('billname', '') + ')'
    pdf.cell(None, None,from_company_text , align='L', new_y='NEXT', new_x='LMARGIN')
    address_text = from_company.get('companyaddress' , '')
    if address_text :
        pdf.cell(None, None, 'Adresse : ' + address_text, align='L', new_y='NEXT', new_x='LMARGIN')
    company_num_text = from_company.get('companynum', '')
    if company_num_text :
        pdf.cell(None, None,  'Org.num. : ' + company_num_text, align='L', new_y='NEXT', new_x='LMARGIN')
    phone_text = from_company.get('phone_number' , '')
    if phone_text :
        pdf.cell(None, None, 'Telefon : +' + phone_text, align='L', new_y='NEXT', new_x='LMARGIN')
    email_text = from_company.get('email_address' , '')
    if email_text :
        pdf.cell(None, None, 'E-post : ' + email_text, align='L', new_y='NEXT', new_x='LMARGIN')

    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(None, None, 'Mottaker : ', align='L', new_y='NEXT', new_x='LMARGIN', ln = 2)
    pdf.set_font('helvetica', '', 12)
    company_text = to_company.get('companyname', '')
    pdf.cell(None, None,company_text , align='L', new_y='NEXT', new_x='LMARGIN')
    address_text = to_company.get('companyaddress' , '')
    if address_text :
        pdf.cell(None, None, 'Adresse : ' + address_text, align='L', new_y='NEXT', new_x='LMARGIN')
    company_num_text = to_company.get('companynum', '')
    if company_num_text :
        pdf.cell(None, None,  'Org.num. : ' + company_num_text, align='L', new_y='NEXT', new_x='LMARGIN')
    phone_text = to_company.get('phone_number' , '')
    if phone_text :
        pdf.cell(None, None, 'Telefon : +' + phone_text, align='L', new_y='NEXT', new_x='LMARGIN')
    email_text = to_company.get('email_address' , '')
    if email_text :
        pdf.cell(None, None, 'E-post : ' + email_text, align='L', new_y='NEXT', new_x='LMARGIN')

    NOR_TIME = pytz.timezone('Europe/Oslo')
    pdf.ln(50)
    pdf.set_font('helvetica', '', 12)
    pdf.cell(w=None, h=None, txt='Fakturadato : ' + bill_date_UTC.astimezone(NOR_TIME).strftime('%d-%m-%Y') , align='L', new_y='NEXT', new_x='LMARGIN')

    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_line_width(0.5)
    pdf.set_draw_color(r=255, g=128, b=0)
    pdf.line(x1=0, y1=y, x2=150, y2=y)
    pdf.ln(3)

    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(w=None, h=None, txt='Betalingsinformasjon' , align='L', new_y='NEXT', new_x='LMARGIN')
    pdf.set_font('helvetica', '', 12)
    due = bill_date_UTC + datetime.timedelta(days=30)
    pdf.cell(w=None, h=None, txt='Forfallsdato : ' + due.astimezone(NOR_TIME).strftime('%d-%m-%Y'), align='L', new_y='NEXT', new_x='LMARGIN')
    pdf.cell(w=None, h=None, txt='Kontonummer : ' + from_company['accountnum'], align='L', new_y='NEXT', new_x='LMARGIN')
    pdf.cell(w=None, h=None, txt='Melding : ' + message, align='L', new_y='NEXT', new_x='LMARGIN')

    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_line_width(0.5)
    pdf.set_draw_color(r=255, g=128, b=0)
    pdf.line(x1=0, y1=y, x2=150, y2=y)
    pdf.ln(10)

    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(w=None, h=None, txt='Beskrivelse', align='L', new_y='NEXT', new_x='LMARGIN')
    pdf.set_font('helvetica', '', 12)

    inc_mva = amount
    womva = round(inc_mva / 1.25, 2)
    mva = inc_mva - womva

    pdf.cell(w=None, h=None, txt='Beløp Kr. (ekskl. MVA) : ' + str(womva), align='L', new_y='NEXT', new_x='LMARGIN')
    pdf.cell(w=None, h=None, txt='MVA Kr : ' + str(mva), align='L', new_y='NEXT', new_x='LMARGIN')
    pdf.cell(w=None, h=None, txt='Beløp Kr. (inkl. MVA) : ' + str(inc_mva) , align='L', new_y='NEXT', new_x='LMARGIN')

    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_line_width(0.5)
    pdf.set_draw_color(r=255, g=128, b=0)
    pdf.line(x1=0, y1=y, x2=150, y2=y)
    pdf.ln(3)

    pdf.set_font('helvetica', 'B', 14)
    summary = 'Betales til bankkonto ' + from_company['accountnum'] + ' : NOK ' + str(inc_mva)
    pdf.cell(w=None, h=None, txt=summary, align='L', new_y='NEXT', new_x='LMARGIN')

    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_line_width(1)
    pdf.set_draw_color(r=255, g=128, b=0)
    pdf.line(x1=0, y1=y, x2=150, y2=y)
    pdf.ln(10)

    #pdf.output('./TEST_INVOICE.pdf')
    pdf_bytes = bytes(pdf.output())
    filename = 'Regning_' + bill_date_UTC.astimezone(NOR_TIME).strftime('%d%m%Y') + '_' +from_company_text + '.pdf'
    meta: dict = {
        'Content-Type': 'application/pdf',
        'filename': filename,
        'description': 'invoice to Vedbjørn',
        'from_company' : from_company ,
        'to_company' : to_company
    }
    file_id = db.insist_on_insert_file(pdf_bytes, filename, 'pdf', meta)
    return file_id

# generate_outgoing_invoice(
#     from_company = {
#         '_id': '63b42285be32179114634b8c',
#         'email_address': 'stian@vedbjorn.no',
#         'phone_number': '4798454811',
#         'billname': 'Mitt veddepo',
#         'accountnum': '123.123.123.123',
#         'companyname': 'BROENTECH SOLUTIONS AS',
#         'companynum': '914079845',
#         'companyaddress': 'Langmyra 11 , 3185 , SKOPPUM'
#     } ,
#     to_company = VEDBJORN_COMPANY ,
#     amount = 337.5 ,
#     message = 'Dine planlagte leveranser har blitt fullført for SELL_Test User . '
#               'Herav 3 sekker med ved. Vennlig hilsen Vedbjørn' ,
#     bill_date_UTC = datetime.datetime.utcnow()
# )

def generate_and_send_outgoing_invoices(ongoing_routes_id):
    """
    Send invoices from the sellers and the drivers, to vedbjørn's invoice reception email

    Regninger@vedbjorn.no

    :param ongoing_routes_id:
    :return:
    """
    db = get_db()
    ongoing_routes = db.insist_on_find_one('ongoing_routes', ongoing_routes_id)
    if not ongoing_routes :
        raise Exception('Ongoing route not found')

    """
    1 : Send invoices from sellers to vedbjørn
    """
    pay_def_it = db.insist_on_find('vipps_payments_out' , {
        'ref.ongoing_route' : ongoing_routes['_id'] ,
        'target' : 'seller' ,
        'status' : 'unpaid'
    })

    _now = datetime.datetime.utcnow()

    for pay_def in mpcur(pay_def_it) :
        sellName = pay_def.get('receiving_user', {}).get('name' , '')
        if not sellName :
            raise Exception('Failed to identify sellName from pay_def')
        userGraph = get_user_with_sellrequest_name(sellName)
        if not userGraph :
            raise Exception('Failed to retrieve seller-node from graph')
        userObj = userGraph[0][0]

        #company = db.insist_on_find_one_q('companies' , {'email_address' : userObj['email']})
        company = db.insist_on_find_one_q('companies', {
            '$or': [
                {'email_address': userObj.get('email', '')},
                {'phone_number': userObj.get('phone', '')}
            ]
        })

        if not company :
            raise Exception('failed to find company')

        invoice_id = generate_outgoing_invoice(
            from_company  = company ,
            to_company    = VEDBJORN_COMPANY ,
            amount        = pay_def['amount_NOK'] ,
            message       = pay_def['message'] ,
            bill_date_UTC = _now
        )
        db.insist_on_update_one(pay_def, 'vipps_payments_out', 'invoice_id', invoice_id)
        db.insist_on_insert_one('notifications' , {
            'email' : VEDBJORN_COMPANY['email_address'] ,
            'email_copy' : userObj['email'] ,
            'timestamp' : _now.timestamp(),
            'contentType' : 'IncomingInvoice' ,
            'invoice_id' : invoice_id,
            'status' : 'new'
        })

    """
    2 : Send invoice from the driver to vedbjørn
    """
    pay_def_it = db.insist_on_find('vipps_payments_out', {
        'ref.ongoing_route': ongoing_routes['_id'],
        'target': 'driver' ,
        'status': 'unpaid'
    })
    driver_amount : float = 0
    driver_company = None
    for pay_def in mpcur(pay_def_it):
        driver_amount = driver_amount + pay_def['amount_NOK']
        if not driver_company :
            the_driver = pay_def.get('receiving_user', {})
            driverEmail = the_driver.get('email', '')
            driverPhone = the_driver.get('phone', '')
            if not driverEmail:
                raise Exception('Failed to identify driverEmail from pay_def')
            driver_company = db.insist_on_find_one_q('companies', {
                '$or' : [
                    {'email_address' : driverEmail} ,
                    {'phone_number': driverPhone}
                ]
            })

            if not driver_company:
                raise Exception('failed to find company')

    invoice_id = generate_outgoing_invoice(
        from_company  = driver_company,
        to_company    = VEDBJORN_COMPANY,
        amount        = driver_amount,
        message       = 'Fullført kjøreoppdrag' ,
        bill_date_UTC = _now
    )
    pay_def_it = db.insist_on_find('vipps_payments_out', {
        'ref.ongoing_route': ongoing_routes['_id'],
        'target': 'driver',
        'status': 'unpaid'
    })
    for pay_def in mpcur(pay_def_it):
        db.insist_on_update_one(pay_def, 'vipps_payments_out', 'invoice_id', invoice_id)
    db.insist_on_insert_one('notifications', {
        'email': VEDBJORN_COMPANY['email_address'],
        'email_copy': driver_company['email_address'],
        'timestamp': _now.timestamp(),
        'contentType': 'IncomingInvoice',
        'invoice_id': invoice_id,
        'status' : 'new'
    })


"""
    Function : handle_dues

    Description :


"""
def handle_dues(dues : list) :
    for due in dues :
        print('TODO')

"""
    Function : CHEATING__set_all_delivery_payments_to_completed

    Description :


"""
def CHEATING__set_all_delivery_payments_to_completed(ongoing_route : dict) :
    db = get_db()
    for visit in ongoing_route['route'] :
        if visit.get('visited_status') == 'completed' and visit.get('type') == 'delivery':
            visitObj = db.insist_on_find_one('deliveries', visit.get('_id' , visit.get('visited' , None)))
            paymentObj = db.insist_on_find_one('vipps_payments_in' , visitObj['payment_ref'])
            db.insist_on_update_one(paymentObj, 'vipps_payments_in', 'status' , 'paid')

"""
    Function : close_planned_deals

    Description :


"""
def close_planned_deals(planned_deals , completed_deals, ongoing_route, is_fake : bool = False,
                        calc_time : datetime.datetime = datetime.datetime.utcnow()) :

    if planned_deals.get('sellRequest' , {}).get('name' , 'a') != completed_deals.get('sellRequest' , {}).get('name' , 'b') :
        print('FAILED at close_planned_deals : planned_deals.sellRequest.name != completed_deals.sellRequest.name')
        return
    planned_sells : list = planned_deals.get('sells' , [])
    completed_sells : list = completed_deals.get('sells' , [])
    if len(planned_sells) <= 0 :
        print('FAILED at close_planned_deals : len(planned_deals.sells) = 0')
        return
    if len(completed_sells) > len(planned_sells) :
        raise Exception('close_planned_deals : len(completed_sells) > len(planned_sells)')
    if len(completed_sells) < len(planned_sells) :
        print('close_planned_deals : There are still some clients which has not paid')
        return

    seller_name = planned_deals.get('sellRequest', {}).get('name', 'a')
    completed_sellRequests = ongoing_route.get('completed_sellRequests', {})
    if seller_name in completed_sellRequests:
        print('ALREADY completed : close_planned_deals')
        return

    driver_user = ongoing_route['route'][0]['drive_user']

    """
    All the clients have paid, we can transfer the income to the seller
    """
    number_of_bags_sold : int = planned_deals.get('number_of_bags_sold' , 0)
    total_amount_NOK : float = 0
    index : int = -1
    for sell in completed_deals.get('sells' , []) :
        index = index + 1
        visitObj = sell['visitObj']
        paymentObj = sell['paymentObj']
        # if paymentObj.get('status' , '') != 'paid' :
        #     raise Exception('close_planned_deals : planned_deals.sells[' + str(index) + '].paymentObj.status != paid')
        total_amount_NOK = total_amount_NOK + paymentObj['amount_NOK']

    seller_paid_id , driver_paid_id = pay_seller_and_driver(
        amount_NOK = total_amount_NOK ,
        seller = planned_deals.get('sellRequest' , {}) ,
        driver = driver_user ,
        message = 'Betaling for ' + str(number_of_bags_sold) + ' vedsekker, kjøpt av Vedbjørn AS',
        ref = {
            'ongoing_route' : ongoing_route['_id'] ,
            'describe' : 'See ObjectId(\"' + str(ongoing_route['_id']) + '\") at collection \"ongoing_route\"'
        } ,
        is_fake = is_fake ,
        calc_time = calc_time
    )

    seller_name = planned_deals.get('sellRequest' , {}).get('name' , 'a')
    completed_sellRequests = ongoing_route.get('completed_sellRequests' , {})
    if seller_name in completed_sellRequests :
        raise Exception('close_planned_deals : seller_name in completed_sellRequests')
    completed_sellRequests[seller_name] = {
        'seller_paid_id' : seller_paid_id ,
        'driver_paid_id' : driver_paid_id
    }
    get_db().insist_on_update_one(ongoing_route, 'ongoing_routes', 'completed_sellRequests', completed_sellRequests)
    ongoing_route['completed_sellRequests'] = completed_sellRequests

    #
    # Finally : Update the graph
    #
    sellRequest : dict = None
    updated_num_reserved : int = 0
    updated_amount_reserved : int = 0
    for completed in completed_sells :
        visitObj = completed['visitObj']
        if not sellRequest :
            sellRequest = visitObj.get('sellRequest' , None)
        buyRequest = visitObj['buyRequest']
        buyRequest_name = buyRequest['name']
        set_last_calced_BuyRequest(buyRequest_name , calc_time.timestamp())
        set_claimed_by_driver_on_buyRequest(buyRequest_name, False)
        remove_reservation(buyRequest_name)
        remove_staged_sell(buyRequest_name)
        reserved_weeks = buyRequest.get('reserved_weeks' , 0)
        if reserved_weeks > 0:
            updated_reserved_weeks = reserved_weeks - 1
            set_reserved_weeks_BuyRequest(buyRequest_name , updated_reserved_weeks)
            if updated_reserved_weeks > 0:
                updated_num_reserved = updated_num_reserved + 1
                updated_amount_reserved = updated_amount_reserved + \
                        (updated_reserved_weeks * buyRequest.get('current_requirement'))

    previous_capacity = sellRequest.get('current_capacity' , 0)
    capacity_reduction_due_to_reservations = sellRequest.get('amount_reserved' , 0) - updated_amount_reserved
    updated_capacity = previous_capacity - sellRequest.get('amount_staged' , 0) - capacity_reduction_due_to_reservations

    """
    Decrease the number of bags that the seller need to have prepared for picking up, equal to the number
    of bags that was sold during this mission (routes)
    """
    decrement_prepare_for_pickup_for_SellRequest(sellRequest['name'], number_of_bags_sold)

    update_stock_sellRequest(
        sellRequest_name    = sellRequest['name']     ,
        new_capacity        = updated_capacity        , # the stock-capacity (amount of bags) of this seller has been reduced because of the sells
        new_amount_reserved = updated_amount_reserved , # this is the new amount of bags to be held-off by reservations
        new_amount_staged   = 0                       , # the staged-sells are zero (non-reserved staged sells) because they have been done
        new_num_reserved    = updated_num_reserved    , # amount of clients with one or more weeks of reservations has potentially been reduced
        new_num_staged      = 0                       ) # there are no more clients with staged sells for this seller now

    print('NEW completed deal for ' , seller_name)


"""
    Function : verify_that_route_is_completed

    Description :


"""
def verify_that_route_is_completed(ongoing_route : dict) -> tuple :
    not_completed : list = []
    index : int = -1
    for visit in ongoing_route.get('route' , []) :
        index = index + 1
        if visit.get('status' , '_') == 'withdrawn' :
            continue
        if visit.get('visited_status' , '') != 'completed' :
            not_completed.append(index)

    retmsg = ''
    if len(not_completed) > 0 :
        retmsg = 'The following indexes not completed ' + str(not_completed)
    return len(not_completed) == 0 , retmsg