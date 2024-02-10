from django.shortcuts import render
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from ADS_app.models import Account, Campaign, Location, AdGroup
import datetime
import ast
from django.http import JsonResponse
from django.shortcuts import render
import json
import argparse
import requests
# import mysql.connector

from django.http import HttpResponse

manager_customer_id: str = '2718785142'
# app = flask.Flask(__name__)
client = GoogleAdsClient.load_from_storage('google-ads.yaml')
# conn = mysql.connector.connect(host="127.0.0.1", port="3306", database="ads_api", user="root", password="root")
# cur = conn.cursor()
import csv


def load_geo_targets(file_path):
    """Загружает геотаргетинговые идентификаторы и названия из CSV файла."""
    geo_targets = {}
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            geo_targets[row['Criteria ID']] = row['Name']
    return geo_targets


def get_location_names(ids, geo_targets):
    """Возвращает названия местоположений для списка идентификаторов."""
    names = []
    for id in ids:
        id_number = str(id).split('/')[1]  # Убедитесь, что отступы соответствуют уровню блока
        name = geo_targets.get(id_number)
        if name:
            names.append(name)
    return names

# функция получения списка аккаунтов под управлением менеджера manager_customer_id, возвращает список customer_id
def get_client_accounts():
    google_ads_service = client.get_service('GoogleAdsService')
    query = f'''SELECT customer_client.id,customer_client.descriptive_name,customer_client.status,customer_client.manager,customer_client.level FROM customer_client WHERE customer_client.manager = FALSE'''
    try:
        response = google_ads_service.search_stream(customer_id=manager_customer_id, query=query)
        result = []
        for batch in response:
            for row in batch.results:
                customer_id = str(row.customer_client.id)
                name = str(row.customer_client.descriptive_name)
                status = str(row.customer_client.status)
                level = str(row.customer_client.level)
                # print(f'{name}  Customer ID:{customer_id} ')
                result.append({'customer_id': customer_id, 'name': name, 'status': status, 'level': level})
        return result
    except GoogleAdsException as ex:
        # Обработка ошибки Google Ads API
        print(f'Query has triggered an exception.\n')
        print(f'Error with Google Ads API.')
        for error in ex.failure.errors:
            print(f'Error with ID: {error.error_code}, message: {error.message}')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f'\tOn field: {field_path_element.field_name}')  #


def get_account_budgets(client_customer_id):
    service = client.get_service('GoogleAdsService')
    query2 = f'''SELECT campaign_budget.amount_micros FROM campaign_budget WHERE campaign_budget.status = 'ENABLED' '''
        # f'''SELECT billing_setup.id FROM account_budget '''

    try:
        response2 = service.search(customer_id=client_customer_id, query=query2)
        for row in response2:
            limit_type = row.billing_setup.id
            # limit_type = budget.total_amount_micros / 1000000
            # remaining_budget = budget.total_adjustments_micros / 1000000
            return limit_type
    except GoogleAdsException as ex:
        print(f'Error with Google Ads API: {ex}')


def _micros_to_currency(micros):
    return micros / 1000000.0 if micros is not None else None


def get_invoice(client, customer_id, billing_setup_id):
    last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    response = client.get_service("InvoiceService").list_invoices(
        customer_id=customer_id,
        billing_setup=client.get_service("GoogleAdsService").billing_setup_path(
            customer_id, billing_setup_id
        ),
        issue_year=str(last_month.year),
        issue_month=last_month.strftime("%B").upper(),
    )
    for invoice in response.invoices:
        print(
            f"""
- Found the invoice {invoice.resource_name}
    ID (also known as Invoice Number): '{invoice.id}'
    Type: {invoice.type_}
    Billing setup ID: '{invoice.billing_setup}'
    Payments account ID (also known as Billing Account Number): '{invoice.payments_account_id}'
    Payments profile ID (also known as Billing ID): '{invoice.payments_profile_id}'
    Issue date (also known as Invoice Date): {invoice.issue_date}
    Due date: {invoice.due_date}
    Currency code: {invoice.currency_code}
    Service date range (inclusive): from {invoice.service_date_range.start_date} to {invoice.service_date_range.end_date}
    Adjustments:
        subtotal {_micros_to_currency(invoice.adjustments_subtotal_amount_micros)}
        tax {_micros_to_currency(invoice.adjustments_tax_amount_micros)}
        total {_micros_to_currency(invoice.adjustments_total_amount_micros)}
    Regulatory costs:
        subtotal {_micros_to_currency(invoice.regulatory_costs_subtotal_amount_micros)}
        tax {_micros_to_currency(invoice.regulatory_costs_tax_amount_micros)}
        total {_micros_to_currency(invoice.regulatory_costs_total_amount_micros)}
    Replaced invoices: {invoice.replaced_invoices.join(", ") if invoice.replaced_invoices else "none"}
    Amounts:
        subtotal {_micros_to_currency(invoice.subtotal_amount_micros)}
        tax {_micros_to_currency(invoice.tax_amount_micros)}
        total {_micros_to_currency(invoice.total_amount_micros)}
    Corrected invoice: {invoice.corrected_invoice or "none"}
    PDF URL: {invoice.pdf_url}
    Account budgets:
    """
        )
        for account_budget_summary in invoice.account_budget_summaries:
            print(
                f"""
                  - Account budget '{account_budget_summary.account_budget}':
                      Name (also known as Account Budget): '{account_budget_summary.account_budget_name}'
                      Customer (also known as Account ID): '{account_budget_summary.customer}'
                      Customer descriptive name (also known as Account): '{account_budget_summary.customer_descriptive_name}'
                      Purchase order number (also known as Purchase Order): '{account_budget_summary.purchase_order_number}'
                      Billing activity date range (inclusive):
                        from #{account_budget_summary.billable_activity_date_range.start_date}
                        to #{account_budget_summary.billable_activity_date_range.end_date}
                      Amounts:
                        subtotal '{_micros_to_currency(account_budget_summary.subtotal_amount_micros)}'
                        tax '{_micros_to_currency(account_budget_summary.tax_amount_micros)}'
                        total '{_micros_to_currency(account_budget_summary.total_amount_micros)}'
                """
            )
            # [END get_invoices_1]


def get_account_campaigns(client_customer_id):
    service = client.get_service('GoogleAdsService')
    query = f'''SELECT campaign.id, campaign.name, campaign.dynamic_search_ads_setting.domain_name, campaign.status FROM campaign WHERE campaign.status != 'REMOVED' AND campaign.advertising_channel_type = 'SEARCH' '''
    try:
        response = service.search(customer_id=client_customer_id, query=query)
        campaigns = []
        for row in response:

            #row.campaign.dynamic_search_ads_setting.domain_name
            # print(row.campaign.name, row.campaign.id, row.campaign.dynamic_search_ads_setting.domain_name)
            campaigns.append({'id': row.campaign.id, 'name': row.campaign.name, 'status': row.campaign.status})
        return campaigns
    except GoogleAdsException as ex:
        print(f'Request with ID "{ex.request_id}" failed with status '
              f'"{ex.error.code().name}" and includes the following errors:')
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f'\t\tOn field: {field_path_element.field_name}')


def get_campaign_conversions(client_customer_id, campaign_id, date):
    service = client.get_service('GoogleAdsService')
    query = f'''SELECT campaign.id, metrics.conversions FROM campaign WHERE campaign.id = {campaign_id} AND segments.date = '{date}' '''
    try:
        response = service.search(customer_id=client_customer_id, query=query)
        return response.results[0].metrics.conversions
    except GoogleAdsException as ex:
        print(f'Request with ID "{ex.request_id}" failed with status '
              f'"{ex.error.code().name}" and includes the following errors:')
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f'\t\tOn field: {field_path_element.field_name}')


def get_campaign_locations(client_customer_id, campaign_id):
    service = client.get_service('GoogleAdsService')
    query = f''' SELECT campaign_criterion.location.geo_target_constant FROM campaign_criterion WHERE campaign_criterion.campaign = 'customers/{client_customer_id}/campaigns/{campaign_id}' AND campaign_criterion.type = 'LOCATION' '''
    try:
        response = service.search(customer_id=client_customer_id, query=query)
        return response
    except GoogleAdsException as ex:
        print(f'Request with ID "{ex.request_id}" failed with status '
              f'"{ex.error.code().name}" and includes the following errors:')
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f'\t\tOn field: {field_path_element.field_name}')


def get_campaign_devices(client_customer_id, campaign_id):
    service = client.get_service('GoogleAdsService')
    query = f'''SELECT campaign_criterion.campaign, campaign_criterion.device.type, campaign_criterion.bid_modifier FROM campaign_criterion WHERE campaign_criterion.campaign = 'customers/{client_customer_id}/campaigns/{campaign_id}' AND campaign_criterion.type = 'DEVICE' '''
    try:
        response = service.search(customer_id=client_customer_id, query=query)
        return response
    except GoogleAdsException as ex:
        print(f'Request with ID "{ex.request_id}" failed with status '
              f'"{ex.error.code().name}" and includes the following errors:')
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f'\t\tOn field: {field_path_element.field_name}')


def get_groups(client_customer_id, campaign_id):
    service = client.get_service('GoogleAdsService')
    query = f'''SELECT ad_group.id, ad_group.name, ad_group.status FROM ad_group WHERE ad_group.campaign = 'customers/{client_customer_id}/campaigns/{campaign_id}' AND ad_group.status != 'REMOVED' '''
    list = []
    try:
        response = service.search(customer_id=client_customer_id, query=query)
        for row in response:
            list.append({'id': row.ad_group.id, 'name': row.ad_group.name, 'status': row.ad_group.status})
        return list
    except GoogleAdsException as ex:
        print(f'Request with ID "{ex.request_id}" failed with status '
              f'"{ex.error.code().name}" and includes the following errors:')
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f'\t\tOn field: {field_path_element.field_name}')

def get_all_data():
    manager_customer_id = '2718785142'
    results = []
    unique_geo_constants = []
    unique_geo_names = []

    geo_targets = load_geo_targets('geo_targets.csv')
    n = 0
    for row in get_client_accounts():

        for camp in get_account_campaigns(row['customer_id']):
            g = []
            c = get_campaign_conversions(row['customer_id'], camp['id'], 20230729)
            g = get_groups(row['customer_id'], camp['id'])
            for row2 in get_campaign_locations(row['customer_id'], camp['id']):
                unique_geo_constants.append(row2.campaign_criterion.location.geo_target_constant)
                # print(row2.campaign_criterion.location.geo_target_constant)
                # print(unique_geo_constants)
            location_names = get_location_names(unique_geo_constants, geo_targets)
            unique_geo_names.append(location_names)
            unique_geo_constants = []
            # locations_list.append(l.campaign_criterion.location.geo_target_constant)
            results.append({'account_name': row['name'], 'account_id': row['customer_id'], 'campaign_name': camp['name'], 'campaign_id': camp['id'], 'status': row['status'], 'conversions': c, 'groups': g , 'locations': list(unique_geo_names[n])})
            n += 1

    # print(results)
    return results
def insert_data():
    data = get_all_data()
    for entry in data:
        account, created = Account.objects.get_or_create(
            account_id=entry['account_id'],
            defaults={'account_name': entry['account_name']}
        )
        campaign, created = Campaign.objects.get_or_create(
            campaign_id=entry['campaign_id'],
            defaults={
                'account': account,
                'campaign_name': entry['campaign_name'],
                'status': entry['status'],
                'conversions': entry['conversions']
            }
        )
        for location_name in entry['locations']:
            Location.objects.get_or_create(
                loc_data=ast.literal_eval(location_name),

                campaign=campaign,
                location_name=location_name.strip("'[]'"),
            )
        for group in entry['groups']:

            AdGroup.objects.get_or_create(
                campaign=campaign,
                name=group['name'],
                ad_group_id=group['id'],
                status=group['status'] )
        #

def index(request):
    data = get_all_data()
    print(data)
    # insert_data()
    return render(request, 'ADS_app/index.html', {'data': data})
def db_write(request):
    try:
        insert_data()
    except Exception as e:
        print(e)
    print('done')
    return render(request, 'ADS_app/success.html')


