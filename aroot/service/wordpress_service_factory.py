from service.wordpress_service import WordpressService
from service.wordpress_service_stripe import WordpressServiceStripe
from domain.customers import Customer


class WordpressServiceFactory:
    @staticmethod
    def create_service(customer: Customer):
        """顧客のpayment_typeに応じて適切なWordpressServiceを生成"""
        if customer.payment_type == "stripe":
            return WordpressServiceStripe(
                customer.wordpress_url, 
                customer.delete_hash, 
                customer.name,
                customer.get_secret_phrase()
            )
        else:  # none or other types
            return WordpressService(
                customer.wordpress_url, 
                customer.delete_hash, 
                customer.name
            )