from constructs import Construct
from aws_cdk import (
    Stage
)
from .vr_api_stack import VrApiStack

class PipelineStage(Stage):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = VrApiStack(self, 'TestApi')