from constructs import Construct
from aws_cdk import (
    Stage
)
from vr_api.routes.email_scraper_stack import EmailScraper

class RouteStage(Stage):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = EmailScraper(self, 'EmailScraper')