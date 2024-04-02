"""
    File : prepare.py
    Author : Stian Broen
    Date : 13.04.2022
    Description :

Contains functions which are related to geography

"""

# from standard Python
import datetime

# from common_library
from libs.commonlib.defs import *
from libs.commonlib.graph_funcs import get_buyrequests_with_reservations_in_county , get_all_countys , \
    get_postcodes_in_county , get_sellers_in_postcode_capacity , insert_reservation , get_reservations_in_county , \
    remove_all_reservations , update_num_reserved_for_SellRequest , update_amount_reserved_for_SellRequest , \
    get_buyrequests_without_reservations_in_county , insert_stagesell , update_num_staged_for_SellRequest , \
    update_amount_staged_for_SellRequest , get_staged_sells_in_county , get_drivers_in_county , \
    get_sell_requests_in_county , insert_stagedrive , update_num_staged_pickups_for_DriveRequest , get_staged_drives_in_county, \
    remove_all_logistics , remove_all_staged_sells , get_staged_drives_in_county_both_locations , \
    get_staged_sells_for_sellreq , get_reservations_for_sellreq , insert_travel_from_to , remove_all_travels , \
    get_pickup_from_driver_home , remove_staged_driver , set_SellRequest_for_BuyRequest_reservation , set_driver_available, \
    set_driver_available_again_time, get_staged_drives_in_county_both_locations_multi
from libs.commonlib.location_funcs import distance_between_coordinates , sort_by_distance

CLEAN_RUNS = True

def clear_all_existing_logistics_relationships():
    """
    Make sure that drivers who have been in quarantine become available again, if the quarantine periode has
    expired
    """
    counties = get_all_countys()
    for county in counties:
        countyName = county[0]['name']
        non_available_drivers = get_drivers_in_county(countyName, False)
        for driver in non_available_drivers:
            driverObj = driver[0]
            time_until_drivable = driverObj.get('available_again_time', 0) - datetime.datetime.utcnow().timestamp()
            if time_until_drivable < 0:
                set_driver_available(driverObj['name'], True)
                set_driver_available_again_time(driverObj['name'], 0)
    """
    Then remove all routes
    """
    remove_all_logistics()


if CLEAN_RUNS:
    remove_all_reservations()
    remove_all_staged_sells()
    clear_all_existing_logistics_relationships()
    remove_all_travels()

"""
    get_sellers_in_county :

    Retrieve all the sellers available from the argument county
"""
def get_sellers_in_county(county : str) :
    sellers_in_county: dict = {}
    postcodes = get_postcodes_in_county(county)
    for postcode_at in postcodes:
        postcode = postcode_at[0]['name']
        sellers_here = get_sellers_in_postcode_capacity(postcode)
        sellers_in_county[str(postcode)] = sellers_here
    return sellers_in_county

"""
    Function : organize_reserved_sales

    Description :
        Using only data from the graph, create a set of trades for the clients which
        has reserved firewood

"""
def organize_reserved_sales(calc_time : datetime.datetime = datetime.datetime.utcnow()) -> tuple:

    print('###############################')
    print('#')
    print('#       Organizing reservations - BEGINS')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('#')

    """
        find_already_reserved :

        If the buyRequest already has a reservation at a specific sell-request, then find that one
        
    """
    def find_already_reserved(sellers_in_county : dict, buy_location : dict , buyRequest : dict) -> tuple:
        reserve_target = buyRequest.get('reserve_target' , '')
        if reserve_target :
            for postcode, local_sellers in sellers_in_county.items():
                for local_seller in local_sellers:
                    if isinstance(local_seller, list) and len(local_seller) >= 3 and local_seller[0].get('name' , '_') == reserve_target :
                        print('FOUND EXISTING RESERVATION')
                        return True , {
                            'distance' : distance_between_coordinates(local_seller[2], buy_location) ,
                            'local_seller' : local_seller
                        }
        return False , None

    """
        find_nearest_reservable_in_postcode :

        Based on the argument postcode, locate the nearest reservable seller, which has a capacity to handle the
        reservation (the required total reservation-amount from the client must be less than the seller capacity)
    """
    def find_nearest_reservable_in_postcode(postcode : str, sellers_in_county : dict, buy_location : dict, buyRequest : dict) :
        if postcode in sellers_in_county:
            required_reserve_amount = buyRequest.get('reserved_weeks' , 0) * buyRequest.get('current_requirement' , 0)
            local_sellers_distances: list = []
            local_sellers = sellers_in_county[postcode]
            minimum_num_reserved: int = 9999
            for local_seller in local_sellers:
                sellRequest = local_seller[0]
                available_to_reserve = sellRequest.get('current_capacity', 0) - sellRequest.get('amount_reserved', 0)
                if available_to_reserve < required_reserve_amount :
                    continue
                num_reserved = sellRequest.get('num_reserved', 0)
                if num_reserved <= minimum_num_reserved:
                    minimum_num_reserved = num_reserved
                else:
                    continue
                seller_location = local_seller[2]
                distance_from_buyer = distance_between_coordinates(seller_location, buy_location)
                local_sellers_distances.append({
                    'distance': distance_from_buyer,
                    'local_seller': local_seller
                })
            if len(local_sellers_distances) > 0:
                local_sellers_distances.sort(key=sort_by_distance)
                for local_sellers_distance in local_sellers_distances :
                    this_num_reserved = local_sellers_distance['local_seller'][0].get('num_reserved' , 0)
                    if this_num_reserved <= minimum_num_reserved :
                        return local_sellers_distance
        return None

    """
        find_nearest_reservable :

        This is like the function above, only that it searches in the entire collection of sellers
        
    """
    def find_nearest_reservable(sellers_in_county : dict, buy_location : dict, buyRequest : dict) :
        local_sellers_distances: list = []
        required_reserve_amount = buyRequest.get('reserved_weeks', 0) * buyRequest.get('current_requirement', 0)
        minimum_num_reserved: int = 9999
        for postcode , local_sellers in sellers_in_county.items() :
            for local_seller in local_sellers:
                sellRequest = local_seller[0]
                available_to_reserve = sellRequest.get('current_capacity' , 0) - sellRequest.get('amount_reserved' , 0)
                if available_to_reserve < required_reserve_amount :
                    continue
                num_reserved = sellRequest.get('num_reserved', 0)
                if num_reserved <= minimum_num_reserved:
                    minimum_num_reserved = num_reserved
                else:
                    continue
                seller_location = local_seller[2]
                distance_from_buyer = distance_between_coordinates(seller_location, buy_location)
                local_sellers_distances.append({
                    'distance': distance_from_buyer,
                    'local_seller': local_seller
                })
        if len(local_sellers_distances) > 0:
            local_sellers_distances.sort(key=sort_by_distance)
            for local_sellers_distance in local_sellers_distances:
                this_num_reserved = local_sellers_distance['local_seller'][0].get('num_reserved', 0)
                if this_num_reserved <= minimum_num_reserved:
                    return local_sellers_distance
        return None

    """
        establish_all_reservation_relationship :

        Create all the reservation relationships between requests-for-reservations and
        sell-requests with capacity for reservation.

    """
    def establish_all_reservation_relationship() -> tuple:
        failed_reservations : list = []
        ok_reservations : list = []
        counties = get_all_countys()
        covered_already_reservations: dict = {}
        for county_at in counties :
            county = county_at[0]['name']
            sellers_in_county = get_sellers_in_county(county)

            existing_reservations = get_reservations_in_county(county)
            for existing_reservation in existing_reservations :
                buyRequestName = existing_reservation[0].get('name' , '_')
                covered_already_reservations[buyRequestName] = existing_reservation

            """
                Retrieve all the reservations which has not been claimed by a driver yet AND
                that has not yet been served within the minimum-age
            """
            reservation_requests = get_buyrequests_with_reservations_in_county(
                county            = county    ,
                minimum_age       = FIVE_DAYS ,
                calc_time         = calc_time ,
                claimed_by_driver = False
            )

            for reservation_request in reservation_requests :
                buyRequest   = reservation_request[0]
                buy_location = reservation_request[2]
                buyRequestName = buyRequest.get('name' , '_')
                if buyRequestName in covered_already_reservations:
                    already_reservation = covered_already_reservations[buyRequestName]
                    reservation = already_reservation[3]
                    sellRequest = already_reservation[4]
                    ok_reservations.append(reservation_request)

                    print('\tALREADY : reservation between BuyRequest(', buyRequest['name'], ') and SellRequest(',
                          sellRequest['name'], ') initiated : ', datetime.datetime.utcfromtimestamp(reservation['calc_time']))

                    continue

                """
                 1. If the buyer has already registered a reservation on a seller
                    before in an earlier iteration, then we need to load that one, regardless of distance, even
                    though there might now be a seller which is even closer.
                    
                    It also means that the amount reserved that the buyer needs, has already been registered at this
                    seller. So, when we register a new registration on a seller-buyer relationship for the first time ,
                    the identify for that seller must be registered at the buyer, so we can know !
                """
                has_already_reserved , reserve_from_this_seller = find_already_reserved(sellers_in_county , buy_location, buyRequest)

                """
                2. Make a list of reservable sellers within the same postcode as the reservation, sorted by distance
                """
                if not reserve_from_this_seller:
                    postcode_key : str = str(buy_location.get('postcode' , '_'))
                    reserve_from_this_seller = find_nearest_reservable_in_postcode(postcode_key, sellers_in_county, buy_location, buyRequest)

                """
                3. If we didnt find a reservation from the list of sellers within the same postcode as the buyer, then we
                   start looking into nearby postcodes
                """
                if not reserve_from_this_seller :
                    reserve_from_this_seller = find_nearest_reservable(sellers_in_county, buy_location, buyRequest)

                """
                4. If we found an reservable seller for this client, then establish a "Reserve" relationship between the Sell and Buy
                """
                if reserve_from_this_seller :
                    covered_already_reservations[buyRequestName] = reservation_request
                    ok_reservations.append(reservation_request)
                    sellRequest = reserve_from_this_seller['local_seller'][0]
                    reserved_capacity = buyRequest.get('reserved_weeks', 0) * buyRequest.get('current_requirement', 0)

                    """
                    Insert the graph-relationship between seller and buyer , so that we can include this buyrequest 
                    in the pickup.
                    """
                    insert_reservation(
                        buyReq  = { 'name' : buyRequest ['name'] } ,
                        sellReq = { 'name' : sellRequest['name'] } ,
                        relationship_meta = {
                            'calc_time' : calc_time.timestamp() ,
                            'reserved' : reserved_capacity,
                            'BuyRequest_name' : buyRequest['name'] ,
                            'SellRequest_name' : sellRequest['name']
                    })

                    if has_already_reserved :
                        print('\tEXISTING : reservation between BuyRequest(', buyRequest['name'], ') and SellRequest(', sellRequest['name'], ')')
                    else:
                        print('\tNEW : reservation between BuyRequest(', buyRequest['name'], ') and SellRequest(', sellRequest['name'], ')')
                        num_reserved = sellRequest.get('num_reserved' , 0) + 1
                        update_num_reserved_for_SellRequest(sellRequest['name'], num_reserved)
                        sellRequest['num_reserved'] = num_reserved
                        amount_reserved = sellRequest.get('amount_reserved', 0) + reserved_capacity
                        update_amount_reserved_for_SellRequest(sellRequest['name'], amount_reserved)
                        sellRequest['amount_reserved'] = amount_reserved
                        set_SellRequest_for_BuyRequest_reservation(buyRequest ['name'] , sellRequest['name'])
                else :
                    failed_reservations.append(reservation_request)

        return ok_reservations , failed_reservations

    """
        clear_all_existing_reservation_relationships :

        Delete all existing reservation-relationship (good for debugging/development)

    """

    ok_reservations , failed_reservations = establish_all_reservation_relationship()

    # TEST : Running the algorithm multiple time, should not change the graph in subsequent iterations
    # ok_reservations , _ = establish_all_reservation_relationship()
    # ok_reservations , _ = establish_all_reservation_relationship()
    # ok_reservations , _ = establish_all_reservation_relationship()

    print('#')
    print('#')
    print('#       Organizing reservations - FINISHED')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('###############################')
    return ok_reservations , failed_reservations

"""
    Function : organize_ordinary_sales

    Description :
        Using only data from the graph, create a set of trades for the clients which
        wants to buy firewood for the next-iteration, but which has not reserved

"""
def organize_ordinary_sales(calc_time : datetime.datetime = datetime.datetime.utcnow()) -> tuple:
    print('###############################')
    print('#')
    print('#       Organizing Ordinary Sales (non-reserved) - BEGINS')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('#')

    """
        find_nearest_seller_in_postcode :

        Based on the argument postcode, locate the nearest seller, which has a capacity to handle an
        ordinary sale (the required total amount from the client must be less than the seller capacity)
    """
    def find_nearest_seller_in_postcode(postcode : str, sellers_in_county : dict, buy_location : dict, buyRequest : dict) :
        if postcode in sellers_in_county:
            required_amount = buyRequest.get('current_requirement' , 0)
            local_sellers_distances: list = []
            local_sellers = sellers_in_county[postcode]
            minimum_num_staged : int = 9999
            for local_seller in local_sellers:
                sellRequest = local_seller[0]
                available_to_sell = sellRequest.get('current_capacity', 0) - sellRequest.get('amount_reserved', 0) - \
                                    sellRequest.get('amount_staged' , 0)
                if available_to_sell < required_amount :
                    continue
                num_staged = sellRequest.get('num_staged', 0)
                if num_staged <= minimum_num_staged:
                    minimum_num_staged = num_staged
                else:
                    continue
                seller_location = local_seller[2]
                distance_from_buyer = distance_between_coordinates(seller_location, buy_location)
                local_sellers_distances.append({
                    'distance': distance_from_buyer,
                    'local_seller': local_seller
                })
            if len(local_sellers_distances) > 0:
                local_sellers_distances.sort(key=sort_by_distance)
                for local_sellers_distance in local_sellers_distances :
                    this_num_reserved = local_sellers_distance['local_seller'][0].get('num_staged' , 0)
                    if this_num_reserved <= minimum_num_staged :
                        return local_sellers_distance
        return None

    """
        find_nearest_seller :

        Locate the nearest seller, which has a capacity to handle an
        ordinary sale (the required total amount from the client must be less than the seller capacity)
    """
    def find_nearest_seller(sellers_in_county : dict, buy_location : dict, buyRequest : dict) :
        local_sellers_distances: list = []
        required_amount = buyRequest.get('current_requirement', 0)
        minimum_num_staged: int = 9999
        for postcode, local_sellers in sellers_in_county.items():
            for local_seller in local_sellers:
                sellRequest = local_seller[0]
                available_to_sell = sellRequest.get('current_capacity', 0) - sellRequest.get('amount_reserved', 0) - \
                                    sellRequest.get('amount_staged', 0)
                if available_to_sell < required_amount:
                    continue
                num_staged = sellRequest.get('num_staged', 0)
                if num_staged <= minimum_num_staged:
                    minimum_num_staged = num_staged
                else:
                    continue
                seller_location = local_seller[2]
                distance_from_buyer = distance_between_coordinates(seller_location, buy_location)
                local_sellers_distances.append({
                    'distance': distance_from_buyer,
                    'local_seller': local_seller
                })
        if len(local_sellers_distances) > 0:
            local_sellers_distances.sort(key=sort_by_distance)
            for local_sellers_distance in local_sellers_distances :
                this_num_reserved = local_sellers_distance['local_seller'][0].get('num_staged' , 0)
                if this_num_reserved <= minimum_num_staged :
                    return local_sellers_distance
        return None

    """
        establish_all_ordinary_sales_relationship :

        Create all the reservation relationships between requests-for-reservations and
        sell-requests with capacity for reservation.

    """
    def establish_all_ordinary_sales_relationship() -> tuple:
        failed_sales : list = []
        ok_sales : list = []
        counties = get_all_countys()
        covered_already_sales: dict = {}
        for county_at in counties :
            county = county_at[0]['name']
            sellers_in_county = get_sellers_in_county(county)

            existing_staged_sells = get_staged_sells_in_county(county)
            for existing_staged_sell in existing_staged_sells :
                buyRequestName = existing_staged_sell[0].get('name' , '_')
                covered_already_sales[buyRequestName] = existing_staged_sell

            """
            Retrieve all the sales which has not been claimed by a driver yet AND
            that has not yet been served within the minimum-age  
            """
            sell_requests = get_buyrequests_without_reservations_in_county(
                county            = county    ,
                minimum_age       = FIVE_DAYS ,
                calc_time         = calc_time ,
                claimed_by_driver = False
            )

            for sell_request in sell_requests:
                buyRequest     = sell_request[0]
                buy_location   = sell_request[2]
                buyRequestName = buyRequest.get('name', '_')
                if buyRequestName in covered_already_sales:
                    already_staged_sell = covered_already_sales[buyRequestName]
                    staged_sell = already_staged_sell[3]
                    sellRequest = already_staged_sell[4]
                    ok_sales.append(sell_request)

                    print('\tALREADY : sell between BuyRequest(', buyRequest['name'], ') and SellRequest(',
                          sellRequest['name'], ') initiated : ', datetime.datetime.utcfromtimestamp(staged_sell['calc_time']))
                    continue

                """
                1. Make a list of sellers within the same postcode as the reservation, sorted by distance
                """
                postcode_key : str = str(buy_location.get('postcode' , '_'))
                buy_from_this_seller = find_nearest_seller_in_postcode(postcode_key, sellers_in_county, buy_location, buyRequest)

                """
                2. If we didnt find a seller from the list of sellers within the same postcode as the buyer, then we
                   start looking into nearby postcodes
                """
                if not buy_from_this_seller :
                    buy_from_this_seller = find_nearest_seller(sellers_in_county, buy_location, buyRequest)

                """
                3. If we found an seller for this client, then establish a "StageSale" relationship between the Sell and Buy
                """
                if buy_from_this_seller :
                    ok_sales.append(sell_request)
                    covered_already_sales[buyRequestName] = sell_request
                    sellRequest = buy_from_this_seller['local_seller'][0]
                    current_requirement = buyRequest.get('current_requirement', 0)
                    print('\tNEW : sell between BuyRequest(', buyRequest['name'], ') and SellRequest(', sellRequest['name'], ')')
                    insert_stagesell(
                        buyReq={'name': buyRequest['name']},
                        sellReq={'name': sellRequest['name']},
                        relationship_meta={
                            'calc_time': calc_time.timestamp(),
                            'staged': current_requirement,
                            'BuyRequest_name': buyRequest['name'],
                            'SellRequest_name': sellRequest['name']
                        })
                    num_staged = sellRequest.get('num_staged', 0) + 1
                    update_num_staged_for_SellRequest(sellRequest['name'], num_staged)
                    sellRequest['num_staged'] = num_staged
                    amount_staged = sellRequest.get('amount_staged', 0) + current_requirement
                    update_amount_staged_for_SellRequest(sellRequest['name'], amount_staged)
                    sellRequest['amount_staged'] = amount_staged
                else:
                    failed_sales.append(sell_request)

        return ok_sales , failed_sales

    """
        clear_all_existing_staged_sell_relationships :

        Delete all existing staged-sell-relationship (good for debugging/development)

    """
    ok_sales , failed_sales = establish_all_ordinary_sales_relationship()

    # TEST : Running the algorithm multiple time, should not change the graph in subsequent iterations
    # ok_sales , _ = establish_all_ordinary_sales_relationship()
    # ok_sales , _ = establish_all_ordinary_sales_relationship()
    # ok_sales , _ = establish_all_ordinary_sales_relationship()

    print('#')
    print('#')
    print('#       Organizing Ordinary Sales (non-reserved) - FINISHED')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('###############################')
    return ok_sales , failed_sales

"""
    Function : organize_drivers

    Description :
        Using only data from the graph, make relationships between drivers and sellers

"""
def organize_drivers(calc_time : datetime.datetime = datetime.datetime.utcnow()) -> tuple:
    print('###############################')
    print('#')
    print('#       Organizing Drivers - BEGINS')
    print('#')
    print('#\tTime : ', datetime.datetime.utcnow())
    print('#')
    print('#')

    """
        find_nearest_driver_in_postcode

    """
    def find_nearest_driver_in_postcode(postcode: str, drivers_in_county: dict, sell_location: dict):
        if postcode in drivers_in_county:
            local_drivers = drivers_in_county[postcode]
            driver_distances: list = []
            minimum_num_staged_pickups: int = 9999
            for local_driver in local_drivers:
                driveRequest = local_driver[0]
                num_staged_pickups = driveRequest.get('num_staged_pickups', 0)
                if num_staged_pickups <= minimum_num_staged_pickups:
                    minimum_num_staged_pickups = num_staged_pickups
                else:
                    continue
                drive_location = local_driver[2]
                distance_from_driver = distance_between_coordinates(drive_location, sell_location)
                driver_distances.append({
                    'distance': distance_from_driver,
                    'local_driver': local_driver
                })
            if len(driver_distances) > 0:
                driver_distances.sort(key=sort_by_distance)
                for driver_distance in driver_distances:
                    num_staged_pickups = driver_distance['local_driver'][0].get('num_staged_pickups', 0)
                    if num_staged_pickups <= minimum_num_staged_pickups:
                        return driver_distance
        return None

    """
        find_nearest_driver

    """
    def find_nearest_driver(drivers_in_county: dict, sell_location: dict):
        driver_distances: list = []
        minimum_num_staged_pickups: int = 9999
        for postcode, local_drivers in drivers_in_county.items():
            for local_driver in local_drivers:
                driveRequest = local_driver[0]
                num_staged_pickups = driveRequest.get('num_staged_pickups', 0)
                if num_staged_pickups <= minimum_num_staged_pickups:
                    minimum_num_staged_pickups = num_staged_pickups
                else:
                    continue
                drive_location = local_driver[2]
                distance_from_driver = distance_between_coordinates(drive_location, sell_location)
                driver_distances.append({
                    'distance': distance_from_driver,
                    'local_driver': local_driver
                })
        if len(driver_distances) > 0:
            driver_distances.sort(key=sort_by_distance)
            for driver_distance in driver_distances:
                num_staged_pickups = driver_distance['local_driver'][0].get('num_staged_pickups', 0)
                if num_staged_pickups <= minimum_num_staged_pickups:
                    return driver_distance
        return None

    """
        assign_sellRequests_to_driveRequests

    """
    def assign_sellRequests_to_driveRequests() -> tuple:
        counties = get_all_countys()
        covered_already: dict = {}
        ok_drives: list = []
        failed_drives: list = []
        for county_at in counties:
            county = county_at[0]['name']

            existing_staged_drives = get_staged_drives_in_county(county)
            for existing_staged_drive in existing_staged_drives:
                driveRequestName = existing_staged_drive[0].get('name', '_')

                """
                Every time we run the assign_sellRequests_to_driveRequests algorithm, we need to remove the
                STAGED_DRIVER relationships which are already existing. This is because we need to allow
                potential changes in the sell-request to influent the sales-to-driver distributions
                """
                remove_staged_driver(driveRequestName)

            sellRequests = get_sell_requests_in_county(county)
            drivers_in_county = get_drivers_in_county(county)

            drivers_in_county_dict: dict = {}
            for slrc in drivers_in_county:
                if len(slrc) < 3:
                    continue
                postcode: str = str(slrc[2].get('postcode', '_'))
                if not postcode in drivers_in_county_dict:
                    drivers_in_county_dict[postcode] = []
                drivers_in_county_dict[postcode].append(slrc)

            """
            1. First try to find a driver for the sellrequest within the same postcode
            """
            found_no_local_drivers: list = []
            for sellreq in sellRequests:
                sellRequest = sellreq[0]
                sell_location = sellreq[2]
                sellRequestName = sellRequest.get('name', '_')
                if sellRequestName in covered_already:
                    driveRequest = covered_already[sellRequestName][0]
                    print('\tALREADY : drive between driveRequest(', driveRequest['name'], ') and SellRequest(',
                          sellRequest['name'], ')')
                    continue

                postcode_key: str = str(sell_location.get('postcode', '_'))
                drive_to_this_seller = find_nearest_driver_in_postcode(postcode_key, drivers_in_county_dict,
                                                                       sell_location)
                if drive_to_this_seller:
                    covered_already[sellRequestName] = drive_to_this_seller['local_driver']
                    driveRequest = drive_to_this_seller['local_driver'][0]
                    print('\tNEW : drive between driveRequest(', driveRequest['name'], ') and SellRequest(',
                          sellRequest['name'], ')')
                    insert_stagedrive(
                        driveReq={'name': driveRequest['name']},
                        sellReq={'name': sellRequest['name']},
                        relationship_meta={
                            'calc_time': calc_time.timestamp(),
                            'DriveRequest_name': driveRequest['name'],
                            'SellRequest_name': sellRequest['name']
                        }
                    )
                    ok_drives.append({
                        'driveRequest': driveRequest,
                        'sellRequest': sellRequest
                    })
                    num_staged_pickups = driveRequest.get('num_staged_pickups', 0) + 1
                    update_num_staged_pickups_for_DriveRequest(driveRequest['name'], num_staged_pickups)
                    driveRequest['num_staged_pickups'] = num_staged_pickups
                else:
                    found_no_local_drivers.append(sellreq)

            """
            2. For the sell-requests which had no driver nearby (same postcode), find drivers within same COUNTY
            """
            for sellreq in found_no_local_drivers:
                sellRequest = sellreq[0]
                sell_location = sellreq[2]
                sellRequestName = sellRequest.get('name', '_')
                if sellRequestName in covered_already:
                    driveRequest = covered_already[sellRequestName][0]
                    print('\tALREADY : drive between driveRequest(', driveRequest['name'], ') and SellRequest(',
                          sellRequest['name'], ')')
                    continue

                drive_to_this_seller = find_nearest_driver(drivers_in_county_dict, sell_location)
                if drive_to_this_seller:
                    covered_already[sellRequestName] = drive_to_this_seller['local_driver']
                    driveRequest = drive_to_this_seller['local_driver'][0]
                    print('\tNEW : drive between driveRequest(', driveRequest['name'], ') and SellRequest(',
                          sellRequest['name'], ')')
                    insert_stagedrive(
                        driveReq={'name': driveRequest['name']},
                        sellReq={'name': sellRequest['name']},
                        relationship_meta={
                            'calc_time': calc_time.timestamp(),
                            'DriveRequest_name': driveRequest['name'],
                            'SellRequest_name': sellRequest['name']
                        }
                    )
                    ok_drives.append({
                        'driveRequest': driveRequest,
                        'sellRequest': sellRequest
                    })
                    num_staged_pickups = driveRequest.get('num_staged_pickups', 0) + 1
                    update_num_staged_pickups_for_DriveRequest(driveRequest['name'], num_staged_pickups)
                    driveRequest['num_staged_pickups'] = num_staged_pickups
                else:
                    failed_drives.append({
                        'driveRequest': 0,
                        'sellRequest': sellRequest
                    })

        return ok_drives, failed_drives

    ok_drives1, failed_drives1 = assign_sellRequests_to_driveRequests()
    # ok_drives2, failed_drives2 = assign_sellRequests_to_driveRequests()
    # ok_drives3, failed_drives3 = assign_sellRequests_to_driveRequests()
    # TEST : ok_drives1 == ok_drives2 == ok_drives3

    print('#')
    print('#')
    print('#       Organizing Drivers : FINISHED')
    print('#')
    print('# \tTime : ', datetime.datetime.utcnow())
    print('#')
    print('###############################')
    return ok_drives1 , failed_drives1


"""
    Function : organize_routes

    Description :
        Using only data from the graph, organize the routes between Locations

"""
def organize_routes(calc_time : datetime.datetime = datetime.datetime.utcnow()) :
    print('###############################')
    print('#')
    print('#       Organizing Routes - BEGINS')
    print('#')
    print('#\tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('#')

    """
        route_to_graph

    """
    def route_to_graph(route : list) :
        for trip in route :
            travel_name = 'TRAVEL_TO_DELIVER'
            travel_meta: dict = {
                'distance'       : trip['distance'],
                'loaded_before'  : trip['loaded_before'],
                'loaded_after'   : trip['loaded_after'],
                'driveRequest'   : trip['driveRequest']['name'],
                'drive_user_name': trip['drive_user']['name']
            }
            if trip['type'] == 'pickup' :
                travel_name = 'TRAVEL_TO_PICKUP'
                travel_meta['sellRequest_name'] = trip['sellRequest']['name']
            else:
                travel_meta['buyRequest_name'] = trip['buyRequest']['name']

            insert_travel_from_to(
                travel_from       = {'name' : trip['from']['name']} ,
                travel_to         = {'name' : trip['to']['name']} ,
                travel_name       = travel_name ,
                relationship_meta = travel_meta
            )



    """
        make_routes

    """
    def make_routes() -> dict:
        routes : dict = {}
        counties = get_all_countys()
        for county_at in counties:
            county = county_at[0]['name']

            """
            1. For each driver, find the assigned sell-requests (pickup-points) in a list sorted by distance
            """
            sell_to_driver_assigns = get_staged_drives_in_county_both_locations(county)
            multiservice_drivers = get_staged_drives_in_county_both_locations_multi(county)
            sell_to_driver_assigns.extend(multiservice_drivers)
            pickups_per_driver : dict = {}
            for sell_to_driver_assign in sell_to_driver_assigns :

                if len(sell_to_driver_assign) >= 6 :
                    sell_location  = sell_to_driver_assign[0]
                    sell_user      = sell_to_driver_assign[1]
                    sellRequest    = sell_to_driver_assign[2]
                    driveRequest   = sell_to_driver_assign[3]
                    drive_user     = sell_to_driver_assign[4]
                    drive_location = sell_to_driver_assign[5]
                elif len(sell_to_driver_assign) == 4:
                    sell_location  = sell_to_driver_assign[0]
                    sell_user      = sell_to_driver_assign[1]
                    sellRequest    = sell_to_driver_assign[2]
                    driveRequest   = sell_to_driver_assign[3]
                    drive_user     = sell_to_driver_assign[1]
                    drive_location = sell_to_driver_assign[0]
                else:
                    continue

                staged_sells: list = get_staged_sells_for_sellreq(sellRequest['name'])
                reservations: list = get_reservations_for_sellreq(sellRequest['name'])
                all_deliveries: list = staged_sells
                all_deliveries.extend(reservations)
                if len(all_deliveries) == 0:
                    print('No deliveries for ' , sellRequest['name'], ' found at this moment.')
                    continue

                already_pickup = get_pickup_from_driver_home(drive_location['name'])

                if already_pickup and len(already_pickup) > 0:
                    print('ALREADY : route for driveRequest(' , driveRequest['name'],') to sellRequest(' ,
                          sellRequest['name'], ')')
                    continue

                driveRequest_name = driveRequest['name']
                if not driveRequest_name in pickups_per_driver :
                    pickups_per_driver[driveRequest_name] = []
                distance_between_driver_and_sellrequest = distance_between_coordinates(drive_location, sell_location)
                pickups_per_driver[driveRequest_name].append({
                    'distance' : distance_between_driver_and_sellrequest ,
                    'sellRequest' : sellRequest ,
                    'sell_user' : sell_user ,
                    'sell_location' : sell_location ,
                    'driveRequest' : driveRequest ,
                    'drive_user' : drive_user ,
                    'drive_location' : drive_location ,
                    'all_deliveries' : all_deliveries
                })

            for driveRequest_name , sell_to_driver_assigns in pickups_per_driver.items() :
                if len(sell_to_driver_assigns) == 1:
                    """
                    If this driver has just one pickup-point, we can just make a route based on that pickup-point's
                    staged sales and reservations
                    """
                    distance       = sell_to_driver_assigns[0]['distance']
                    sell_location  = sell_to_driver_assigns[0]['sell_location']
                    sellRequest    = sell_to_driver_assigns[0]['sellRequest']
                    driveRequest   = sell_to_driver_assigns[0]['driveRequest']
                    drive_user     = sell_to_driver_assigns[0]['drive_user']
                    drive_location = sell_to_driver_assigns[0]['drive_location']
                    all_deliveries = sell_to_driver_assigns[0]['all_deliveries']

                    # staged_sells : list = get_staged_sells_for_sellreq(sellRequest['name'])
                    # reservations : list = get_reservations_for_sellreq(sellRequest['name'])
                    # all_deliveries : list = staged_sells
                    # all_deliveries.extend(reservations)

                    loaded_here : int = 0
                    for delivery in all_deliveries :
                        loaded_here = loaded_here + delivery[0]['current_requirement']

                    route : list = []
                    current_pos : dict = {
                        'from' : drive_location ,
                        'to' : sell_location ,
                        'distance' : distance ,
                        'type' : 'pickup' ,
                        'loaded_before' : 0 ,
                        'loaded_after' : loaded_here ,
                        'sellRequest' : sellRequest ,
                        'driveRequest' : driveRequest ,
                        'drive_user' : drive_user
                    }
                    route.append(current_pos)

                    while len(all_deliveries) > 0 :
                        delivery_distances : list = []
                        for delivery in all_deliveries :
                            distance = distance_between_coordinates(delivery[2] , current_pos['to'])
                            delivery_distances.append({
                                'distance' : distance ,
                                'delivery' : delivery
                            })
                        delivery_distances.sort(key=sort_by_distance)
                        next_delivery = delivery_distances[0]
                        next_buyreq       = next_delivery['delivery'][0]
                        next_delivery_loc = next_delivery['delivery'][2]
                        next_pos : dict = {
                            'from' : current_pos['to'] ,
                            'to' : next_delivery_loc ,
                            'distance' : next_delivery['distance'] ,
                            'type' : 'delivery' ,
                            'loaded_before' : current_pos['loaded_after'] ,
                            'loaded_after' : current_pos['loaded_after'] - next_buyreq['current_requirement'] ,
                            'sellRequest' : sellRequest ,
                            'buyRequest' : next_buyreq ,
                            'driveRequest': driveRequest,
                            'drive_user': drive_user
                        }
                        route.append(next_pos)
                        current_pos = next_pos
                        all_deliveries = list(filter(lambda i: i[0]['name'] != next_buyreq['name'] , all_deliveries))

                    routes[driveRequest_name] = route
                    route_to_graph(route)
                    print('NEW : route for driveRequest(', driveRequest_name, ') to sellRequest(', sellRequest['name'], ')')

                elif len(sell_to_driver_assigns) > 1:
                    """
                    If there are more than 1 pickup point, we need to optimize the route by finding which of the
                    delivery-positions for each sale is closest to the next pickup points. Of course, to do that we 
                    also need to have a list of pickup-points which is sorted by distance.
                    """
                    route: list = []
                    current_pos = None
                    sell_to_driver_assigns.sort(key=sort_by_distance)
                    for next_pickup in sell_to_driver_assigns:
                        next_distance       = next_pickup['distance']
                        next_sell_location  = next_pickup['sell_location']
                        next_sellRequest    = next_pickup['sellRequest']
                        next_driveRequest   = next_pickup['driveRequest']
                        next_drive_user     = next_pickup['drive_user']
                        next_drive_location = next_pickup['drive_location']
                        next_all_deliveries = next_pickup['all_deliveries']

                        # next_staged_sells: list = get_staged_sells_for_sellreq(next_sellRequest['name'])
                        # next_reservations: list = get_reservations_for_sellreq(next_sellRequest['name'])
                        # next_all_deliveries: list = next_staged_sells
                        # next_all_deliveries.extend(next_reservations)

                        next_loaded_here: int = 0
                        for delivery in next_all_deliveries:
                            next_loaded_here = next_loaded_here + delivery[0]['current_requirement']

                        from_pos = next_drive_location
                        loaded_before = 0
                        if current_pos :
                            # Note that "current_pos" here, is actually the previous position
                            from_pos = current_pos['to']
                            loaded_before = current_pos['loaded_after']

                        current_pos: dict = {
                            'from': from_pos,
                            'to': next_sell_location,
                            'distance': next_distance,
                            'type': 'pickup',
                            'loaded_before': loaded_before,
                            'loaded_after': next_loaded_here,
                            'sellRequest': next_sellRequest,
                            'driveRequest': next_driveRequest,
                            'drive_user': next_drive_user
                        }
                        route.append(current_pos)

                        while len(next_all_deliveries) > 0:
                            delivery_distances: list = []
                            for delivery in next_all_deliveries:
                                distance = distance_between_coordinates(delivery[2], current_pos['to'])
                                delivery_distances.append({
                                    'distance': distance,
                                    'delivery': delivery
                                })
                            delivery_distances.sort(key=sort_by_distance)
                            next_delivery = delivery_distances[0]
                            next_buyreq = next_delivery['delivery'][0]
                            next_delivery_loc = next_delivery['delivery'][2]
                            next_pos: dict = {
                                'from': current_pos['to'],
                                'to': next_delivery_loc,
                                'distance': next_delivery['distance'],
                                'type': 'delivery',
                                'loaded_before': current_pos['loaded_after'],
                                'loaded_after': current_pos['loaded_after'] - next_buyreq['current_requirement'],
                                'sellRequest': next_sellRequest,
                                'buyRequest': next_buyreq,
                                'driveRequest': next_driveRequest,
                                'drive_user': next_drive_user
                            }
                            route.append(next_pos)
                            current_pos = next_pos
                            next_all_deliveries = list(filter(lambda i: i[0]['name'] != next_buyreq['name'], next_all_deliveries))

                        print('NEW : route for driveRequest(', driveRequest_name, ') to sellRequest(', next_sellRequest['name'], ')')

                    routes[driveRequest_name] = route
                    route_to_graph(route)

        return routes


    routes = make_routes()
    # routes2 = make_routes()
    # routes3 = make_routes()

    # TEST : routes == routes2 == routes3

    print('#')
    print('#')
    print('#       Organizing Logistics : FINISHED')
    print('#')
    print('# \tTime : ' , datetime.datetime.utcnow())
    print('#')
    print('###############################')
    return routes
