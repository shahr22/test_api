import aws_cdk as core
import aws_cdk.assertions as assertions

from vr_api.vr_api_stack import VrApiStack

# example tests. To run these tests, uncomment this file along with the example
# resource in vr_api/vr_api_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = VrApiStack(app, "vr-api")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
